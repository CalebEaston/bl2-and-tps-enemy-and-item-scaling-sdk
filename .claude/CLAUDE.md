# Enemy and Item Scaling (BL2 PythonSDK mod)

A Borderlands 2 mod for the **new** PythonSDK stack (willow2-mod-manager v3.8 / pyunrealsdk /
`mods_base` 1.12, embedded Python 3.14). The legacy PythonSDK (`Mods.ModMenu`, `BL2MOD`) is archived
and is NOT what this targets.

## What the mod does

Four spinner options, each `Vanilla` | `Player Level` | `Within 1 Level` ... `Within 10 Levels`:

| Option | Vanilla | Within N |
|---|---|---|
| Minimum Enemy Level | no floor | enemy level raised to at least `player - N` |
| Maximum Enemy Level | no cap | enemy level lowered to at most `player + N` |
| Minimum Item Level | no floor | item level raised to at least `player - N` |
| Maximum Item Level | no cap | item level lowered to at most `player + N` |

`player` = `PlayerReplicationInfo.ExpLevel`, plus `OverpowerChoiceValue` in UVHM only. Item bounds
are independent of enemy bounds. Two `BoolOption`s (v2): `On-Level Mission Rewards` (the mission
is levelled to the player turning it in before its rewards, XP and cash are rolled) and
`On-Level Vendors` (vending machines are set to the player's level when they spawn and before
they restock; vendors are excluded from the item band). `Log Adjustments` prints every change.

Current priority: **get a working version in-game first, then patch**. Don't over-engineer for
compatibility yet; see "Later" at the bottom for the compatibility work that is deferred. Keep it
simple: an option that only takes effect after a save-quit-continue is acceptable, so prefer the
plain approach over live re-application.

## Layout

```
src/enemy_item_scaling/   the mod: __init__.py, pyproject.toml (mod metadata), Readme.md (changelog)
src/                      is the "mods folder" the game is pointed at; keep it to mod packages only
.willow2-mod-manager/     git submodule, pinned to the v3.8 release commit (9097107) for type-checking
docs/sdk-notes.md         reference: SDK facts, hook targets, prior art, open questions
docs/testing.md           in-game test plan: console probes and scenarios with expected log output
docs/development.md       human-facing dev notes: layout, checks, running from checkout, releases
.github/workflows/        release.yml: a v* tag builds the .sdkmod and publishes a GitHub Release
pyproject.toml            pyright + ruff config only (copied from the bl-sdk repos)
```

The README is the player-facing page (download link first, install guide, no internals); keep
developer material out of it and in `docs/`.

The folder name `enemy_item_scaling` is the Python module name, the settings file name
(`<game>/sdk_mods/settings/enemy_item_scaling.json`) and the required root folder of the `.sdkmod`.
Never put a `.` in it. Every non-dot subfolder of `src/` gets imported as a mod, so tests/docs/tools
go at the repo root, not under `src/`.

## Hard rules for the code

- `build_mod()` must be called at module level of `__init__.py` (it inspects the caller's frame to
  find the module and the sibling `pyproject.toml`). Name/author/version/description come from
  `pyproject.toml`; don't define `__version__`/`__author__` in code.
- Hook strings are `Package.Class:Function` (colon). Callback is
  `(obj: UObject, args: WrappedStruct, ret: Any, func: BoundFunction)`.
- `args` is a COPY. To change an argument: `with prevent_hooking_direct_calls(): func(new)` then
  `return Block`. Forgetting the context manager recurses into the hook; forgetting `Block` runs
  the original call as well.
- Exceptions inside a hook are logged and the function runs anyway, so a broken hook looks like a
  no-op. Turn on `Log Adjustments` and read the console/log when testing.
- Hooks are inert until the mod is enabled. Never pass `immediately_enable=True`.
- Options: pass `options=[...]` explicitly (module-scan order is unstable). `on_change_*`
  callbacks receive the NEW value while `opt.value` is still the OLD one. `SliderOption.value` is
  typed `float` (wrap in `int()` for pyright) and may be int or float at runtime. Don't call
  `option.reset()` (added in mods_base 1.13; the game ships 1.12).
- Skip the player's own pawn in pawn hooks (`WillowPlayerPawn` goes through `SetGameStage` too).
- The first 1024 bytes of `__init__.py` must not contain `from Mods.`, `from ..ModMenu import` or
  `BL2MOD):`, even in a comment, or the loader treats the mod as legacy.
- `project.version` must be dotted integers (`"0.1"`); anything else raises at import.
- Python file content stays ASCII (ruff RUF001/RUF003 flag en dashes and curly quotes). No `TODO`
  comments in code (ruff TD/FIX rules); put open items in `docs/sdk-notes.md`.
- Use `unrealsdk.logging.info/warning/error`, never `print`. `dev_warning` is hidden in-game.

## Dev loop

Local checks (no game needed):

```sh
git submodule update --init .willow2-mod-manager
git -C .willow2-mod-manager submodule update --init src/mods_base src/keybinds src/console_mod_menu
python3 -m venv .venv && .venv/bin/pip install ruff     # once
.venv/bin/ruff check src && .venv/bin/ruff format --check src
npx --yes pyright src
```

In-game (the game is NOT installed on this dev machine; it runs elsewhere via Steam/Proton):

1. Install the SDK release zip into the game folder (gives `<game>/sdk_mods` and
   `<game>/Binaries/Win32/Plugins/`).
2. Create `<game>/Binaries/Win32/Plugins/unrealsdk.user.toml` pointing at this repo's `src/`, so no
   copying is needed (Windows path as seen by Wine; `Z:` is the default mapping of `/`):
   ```toml
   [mod_manager]
   extra_folders = ['Z:\home\caleb\Development\caleb\bl2-enemy-and-item-scaling-sdk\src']
   ```
   Alternatively copy `src/enemy_item_scaling/` into `<game>/sdk_mods/`.
3. Steam launch options for Proton: `WINEDLLOVERRIDES="ddraw=n,b" %command% -pf_tricks=vcrun2022`
4. Enable the mod once from the main menu `MODS` entry (fresh installs start disabled).
5. Console = tilde twice. `rlm enemy_item_scaling` hot-reloads the module after edits.
   `mods` opens the console mod menu. The log file is
   `<game>/Binaries/Win32/Plugins/unrealsdk.log` (truncated every launch).
6. Package: `cd src && zip -r ../enemy_item_scaling.sdkmod enemy_item_scaling -x '*__pycache__*'`
   (a `.sdkmod` is a zip whose single root folder is named exactly like the file).

## Hook targets in use

| Hook | Arg | What it covers |
|---|---|---|
| `WillowGame.WillowPawn:SetGameStage` | `NewGameStage` | enemy level at spawn |
| `WillowGame.WillowPawn:SetGameStageForSpawnedInventory` and `WillowAIPawn:` same | `NewInventoryGameStage` | level of an enemy's drops |
| `WillowGame.WillowInteractiveObject:SetGameStage` | `NewGameStage` | chests, slot machines, dice/golden chests (item band); vending machines (vendor toggle) |
| `WillowGame.WillowVendingMachine:ResetInventory` | none; calls `SetGameStage` + `SetExpLevel` on `obj` first | vendor restocks and paid resets |
| `WillowGame.WillowPlayerController:ServerGrantMissionRewards` (PRE + POST_UNCONDITIONAL) | `Mission`, `bGrantAltReward`; writes `Mission.GameStage` + `bGameStageLocked`, restores after | mission reward roll (plus XP and cash); expected once per player on the host, untested in co-op |

The first three are the exact targets shipped by apple1417's `enemy_level_randomizer` and EdricY's
Bouncy-Loot-God `always_on_level`; the mission one is hooked by RedxYeti's PayToLoot and its
`GameStage` write is what BouncyLootGod and Roguelands do before calling it. Raid-boss dedicated
drops, Moxxi tips and slot-machine payouts (`Behavior_SpawnItems`) take their level from the pawn
or container they come from, so the hooks above cover them. See `docs/sdk-notes.md`.

## Later (deferred on purpose)

- Compatibility with the TPS character ports (Nisha, Athena, Doppelganger; all PythonSDK mods on
  Nexus). Plan: get their folders, grep their hook targets against ours, and if they overlap
  consider `Type.POST_UNCONDITIONAL` hooks that read back `obj.GetGameStage()` and only re-set
  out-of-band values, so other mods' pre-hooks run first.
- Known v2 trade-offs, left simple on purpose: mission XP and cash scale with the reward level
  (restore vanilla XP via a `(Block, value)` return override on
  `WillowGame.MissionDefinition:GetExperienceReward` if ever unwanted); base-game vendor stock keeps
  its vanilla `-2..0` level variance (`GD_Economy.VendingMachine.Init_VendingMachine_LootGamestageVariance`,
  a global object other mods edit too); the item of the day is exactly the machine's stage.
- Nexus Mods listing: Nexus can't be automated, so `docs/nexus.md` holds the summary, BBCode
  description, requirements, install steps and category for the user to paste.
- Out of scope by decision (2026-10-08): re-levelling enemies that are already alive when the
  player levels up. They keep their spawn level until they respawn.
- Local unit tests for `clamp_level` (needs a conftest that stubs `mods_base`/`unrealsdk`).
