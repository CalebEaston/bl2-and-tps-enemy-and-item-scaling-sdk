# Enemy and Item Scaling (BL2 / TPS PythonSDK mod)

A Borderlands 2 and Borderlands: The Pre-Sequel mod for the **new** PythonSDK stack
(willow2-mod-manager v3.8 / pyunrealsdk / `mods_base` 1.12, embedded Python 3.14; one SDK zip and
one `.sdkmod` serve both games). The legacy PythonSDK (`Mods.ModMenu`, `BL2MOD`) is archived and
is NOT what this targets. TPS support is declared since v0.6 (2026-10-09) and is unplayed so far.

## What the mod does

Four spinner options, each `Vanilla` | `Player Level` | `Within 1 Level` ... `Within 10 Levels`:

| Option | Vanilla | Within N |
|---|---|---|
| Minimum Enemy Level | no floor | enemy level raised to at least `player - N` |
| Maximum Enemy Level | no cap | enemy level lowered to at most `player + N` |
| Minimum Item Level | no floor | item level raised to at least `player - N` |
| Maximum Item Level | no cap | item level lowered to at most `player + N` |

`player` = `PlayerReplicationInfo.ExpLevel`, plus `OverpowerChoiceValue` in BL2 UVHM only (TPS has
no OP levels and no such field; `has_overpower_levels()` looks the field up on the class once and
guards the read). Item bounds
work without enemy bounds (vanilla enemies, on-level loot); a clamped enemy drops loot at its
clamped level with the item band applied on top. Two `BoolOption`s (v2): `On-Level Mission
Rewards` (the mission's stage is set to the player turning it in before its rewards, XP and cash
are rolled: the definition's transient stage from every trigger, the player's saved copy only in
the grant hook since that copy goes into the save file; a reward item is re-levelled as it is
taken if it still isn't on level) and
`On-Level Vendors` (vending machines are set to the player's level when they spawn and before
they restock; vendors are excluded from the item band; in TPS the Concordia SHiFT machine,
`WillowVendingMachineShift`, a plain `WillowInteractiveObject`, counts as a vendor too).
`Log Adjustments` prints every change.

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
- Both games: `[tool.sdkmod] supported_games` must list `"BL2"` and `"TPS"`, or `mods_base` shows
  the mod as `Incompatible` and locks the enable toggle in the missing game. Every hook target
  and field used here exists in both games with the same parameter names (checked against the
  game-generated stubs, see `docs/sdk-notes.md` v0.6). Anything game-specific is detected by
  looking for the class or field itself, not via `Game.get_current()` (which assumes BL2 for an
  unknown executable name): `has_overpower_levels()` uses `UClass._find_prop` (ValueError when
  missing), `_vendor_classes()` uses `unrealsdk.find_class` (ValueError when missing; with a
  short name it only sees classes present when the SDK first filled its class cache, so use it
  for native WillowGame classes only). A hook on a function the running game doesn't have is
  harmless and simply never fires (`unrealsdk` matches hooks by the called function's name).

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
   `<game>/Binaries/Win32/Plugins/`). `<game>` is `.../steamapps/common/Borderlands 2` (Steam app
   49520) or `.../steamapps/common/BorderlandsPreSequel` (261640); the steps below are the same
   for both, and each game keeps its own `sdk_mods/settings/enemy_item_scaling.json`.
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
| `WillowGame.PopulationFactoryBalancedAIPawn:CreatePopulationActor` and `:RestorePopulatedAIPawn` (PRE) | `GameStage`; re-call `func(args)`, return `(Block, spawned)` (no fallback: `prevent_hooking_direct_calls` doesn't cover the factory's nested setter calls, so a retry at the original stage would be re-clamped by the safety nets anyway) | primary enemy path: the factory passes this one argument to `SetGameStage`, `SetExpLevel` (nameplate; the input of the health/damage formulas) and `SetGameStageForSpawnedInventory`, so clamping it moves all three |
| `WillowGame.WillowPawn:SetGameStage` and `WillowGame.WillowAIPawn:SetExpLevel` | `NewGameStage` / `NewExpLevel` | safety nets for pawns that skip the factory; no-ops after the factory hook. A `SetGameStage`-only hook (v0.1-v0.4) left enemies at their vanilla nameplate/health with on-level drops |
| `WillowGame.WillowPawn:SetGameStageForSpawnedInventory` and `WillowAIPawn:` same | `NewInventoryGameStage` | level of an enemy's drops (a clamped enemy's drops follow its clamped level; the item band applies on top) |
| `WillowGame.WillowInteractiveObject:SetGameStage` | `NewGameStage` | chests, slot machines, dice/golden chests (item band; never lowered when the object path starts with `Xmas_P.` or `MoonShotIntro_P.`, where Bouncy Loot God found a chest that spawns nothing when down-levelled); vending machines (vendor toggle) |
| `WillowGame.WillowVendingMachine:ResetInventory` and `WillowGame.WillowVendingMachineShift:ResetInventory` (TPS only; never fires in BL2) | none; calls `SetGameStage` + `SetExpLevel` on `obj` first | vendor restocks and paid resets |
| `WillowGame.QuestAcceptGFxMovie:UpdateMissionList` / `:DetermineQuestEntries` / `:extPopulateQuestEntries` (POST) | iterate `obj.MissionList[]` (`MissionDef`, `MissionStatus`), player `obj.WPCOwner` | primary: levels every accepted mission (status 1/2/3) when an NPC's list is built, before any turn-in, order-independent |
| `WillowGame.QuestAcceptGFxMovie:SetRewardCard` (PRE) | `MissionDef`, `WPC`; same write if status in {1,2,3} | second trigger when a reward card shows |
| `WillowGame.QuestAcceptGFxMovie:extCompleteConfirmed` (PRE) | none; mission from `obj.MissionList[obj.GetSelectedIndex()].MissionDef`, player `obj.WPCOwner` | backstop at the turn-in confirm; only beats the reroller's hook if ours registered first |
| `WillowGame.WillowPlayerController:ServerGrantMissionRewards` (PRE) | `Mission`, `bGrantAltReward`; same write | scripted completions with no UI; expected once per player on the host, untested in co-op |
| `WillowGame.WillowPlayerController:ReceiveWeaponReward` / `:ReceiveItemReward` (PRE) | `Mission`, out `DefinitionData`; rewrite `ManufacturerGradeIndex` + `GameStage`, `func(args)`, `Block` | accept-time safety net: the item is handed over at the player's level. Usually a difference is the mission's own XP levelling the player between roll and accept (ordinary adjustment); if the item is at the mission's ORIGINAL stage (from `_saved_mission_stages`) the roll ignored the write and a "please report this" warning is always logged |
| `WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie` (POST) | none | clears `_saved_mission_stages` on every map load so no stage crosses characters/playthroughs |
| `WillowGame.WillowPlayerController:MissionRewardsReceived` (POST_UNCONDITIONAL) and `:UpdateMissionStatus` (POST_UNCONDITIONAL, when `NewMissionStatus == 4` Complete) | `Mission`; restores the saved stage | after the reward is taken / the mission completes; in the vanilla flow Complete comes before the roll and the grant hook re-levels |

All of this is single-player / host-side; in co-op the shared mission object can end up at
another player's level (documented, untested).

Reward Reroller (legacy mod the user plays with) blocks `ServerGrantMissionRewards` and
`MissionTracker:CompleteMission` and grants rewards itself from a PRE hook on
`QuestAcceptGFxMovie:extCompleteConfirmed`, reading `mission.GetGameStage()` from Python.
**Legacy mods' calls never trigger hooks**: `legacy_compat` wraps every legacy callback in
`prevent_hooking_direct_calls()` (`.willow2-mod-manager/src/legacy_compat/__init__.py:123`), so a
return override on `GetGameStage` (the v0.3 attempt) can't reach them. Only the field write
does, and it has to happen before their hook runs: hence the reward-card hook. PRE hooks on one
function run in registration order, so our `extCompleteConfirmed` hook runs before the
reroller's only when our mod was enabled first (normal launch order), which is why the reward
card is the primary hook.

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
- Assault on Dragon Keep standalone (`Game.AoDK`, `tinytina.exe`): believed to be the BL2 build,
  so `"AoDK"` in `supported_games` is probably the whole change (the Overpower read is decided by
  field presence, so it needs no change), but the stub zip has no AoDK tree and nothing was
  checked; not declared because nobody has asked.
- TPS enemy vehicles, the SHiFT machine's gamble stock (whether the shipped game exposes it and
  whether it follows the stage are unknown), Wilhelm's `OzSupportDrone` / `OzPlayerJumpPad` (plain
  interactive objects the item band would log as `container` if the game ever sets their stage),
  and TPS's `MissionDefinition.LevelAdjustment` / `GetMissionLevel(pc, bIncludeLevelAdjustment)`
  (BL2 has neither; the mod writes `GameStage` only): same "wait for a report" status as BL2
  vehicles, with the checks listed in `docs/testing.md` section 9.
