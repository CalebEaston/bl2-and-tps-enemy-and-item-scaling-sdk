# Enemy and Item Scaling (BL2 / TPS PythonSDK mod)

A Borderlands 2 and Borderlands: The Pre-Sequel mod for the **new** PythonSDK stack
(willow2-mod-manager v3.8 / pyunrealsdk / `mods_base` 1.12, embedded Python 3.14; one SDK zip and
one `.sdkmod` serve both games). The legacy PythonSDK (`Mods.ModMenu`, `BL2MOD`) is archived and
is NOT what this targets. TPS support is declared since v0.6 (2026-10-09) and is unplayed so far.

## What the mod does

Five spinner options, each `Vanilla` | `Player Level` | `Within 1 Level` ... `Within 10 Levels`:

| Option | Vanilla | Within N |
|---|---|---|
| Minimum Enemy Level | no floor | enemy level raised to at least `player - N` |
| Maximum Enemy Level | no cap | enemy level lowered to at most `player + N` |
| Minimum Item Level | no floor | item level raised to at least `player - N` |
| Maximum Item Level | no cap | item level lowered to at most `player + N` |
| Minimum Mission Level | no floor | an accepted mission's level raised to at least `player - N`, never lowered, written into the save (v0.8; was the `On-Level Mission Rewards` bool in v0.2-v0.7) |

`player` = `PlayerReplicationInfo.ExpLevel`, plus `OverpowerChoiceValue` in BL2 UVHM only (TPS has
no OP levels and no such field; `has_overpower_levels()` looks the field up on the class once and
guards the read). Item bounds
work without enemy bounds (vanilla enemies, on-level loot); a clamped enemy drops loot at its
clamped level with the item band applied on top. The mission bound (v0.7 semantics, v0.8 name):
every accepted mission below the floor is raised to it, never lowered, for good: the definition's
`GameStage` + `bGameStageLocked` and the player's `MissionStatusPlayerData.GameStage` record,
which the save file stores; written on accept, on each level-up, on map load and again at the
NPC list / reward card / turn-in / grant backstops; nothing is restored; the reward item is only
checked as it is taken, and a roll below the stage the mission had at the roll logs a "please
report this" line. One `BoolOption`:
`On-Level Vendors` (vending machines are set to the player's level when they spawn and before
they restock; vendors are excluded from the item band; in TPS the Concordia SHiFT machine,
`WillowVendingMachineShift`, a plain `WillowInteractiveObject`, counts as a vendor too).
`Log Adjustments` prints every change.

Current priority: **get a working version in-game first, then patch**. Don't over-engineer for
compatibility yet; see "Later" at the bottom for the compatibility work that is deferred. Keep it
simple: an option that only takes effect after a save-quit-continue is acceptable, so prefer the
plain approach over live re-application (the one exception so far: accepted missions are
re-levelled on every level-up, v0.7, because the mission log is meant to track the player).

## Layout

```
src/enemy_item_scaling/   the mod: __init__.py, pyproject.toml (mod metadata), Readme.md (changelog)
src/                      is the "mods folder" the game is pointed at; keep it to mod packages only
.willow2-mod-manager/     git submodule, pinned to the v3.8 release commit (9097107) for type-checking
docs/sdk-notes.md         reference: SDK facts, hook targets, prior art, open questions
docs/testing.md           playtest checklist for Caleb: plain in-game steps and log lines, nothing typed into
                          the console (he can't paste into it)
docs/testing-probes.md    developer version: console probes and detailed scenarios with expected log output
docs/development.md       human-facing dev notes: layout, checks, running from checkout, releases
.github/workflows/        release.yml: a v* tag builds the .sdkmod and publishes a GitHub Release
pyproject.toml            pyright + ruff config only (copied from the bl-sdk repos)
```

The README is the player-facing page (download link first, install guide, no internals); keep
developer material out of it and in `docs/`. Its first line is the AI disclosure, worded exactly
"This mod was made with AI (Claude Code). The code and docs were written with it, under my
direction." (Caleb's wording; not "with the help of AI"). Its Credits section lists the mods
whose findings this one builds on; add to it (and to `docs/nexus.md`) when a new source shapes
the code.

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
- Option names: the existing `Minimum/Maximum <Thing> Level` style, plain words that read
  naturally (Caleb's ask), and short: the mod menu truncates long labels (EnemyBalancer measured
  26 characters already dropping the last word), so stay at or under 25. Renaming an option
  orphans its saved value in `settings/enemy_item_scaling.json`; say so in the changelog.
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
   extra_folders = ['Z:\home\caleb\Development\caleb\bl2-and-tps-enemy-and-item-scaling-sdk\src']
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
| `WillowGame.WillowPlayerController:AcceptMission` (POST, status in {1,2,3} via `GetPlayersMissionStatus`), `:UpdateMissionStatus` (POST_UNCONDITIONAL, `NewMissionStatus` in {1,2,3}) and `:ClientReceiveMissionStatus` (POST, `MissionStatusData.Mission` / `.Status` in {1,2,3}) | `Mission`; same write | the moment a mission is accepted, by NPC or by script (ECHO, cutscene): the native `MissionTracker.ActivateMission` locks the stage, then calls `UpdateMissionStatus` and `ClientReceiveMissionStatus` per player, so a POST write wins; three idempotent hooks because which of them first sees the player's record is open (`docs/sdk-notes.md` v0.7) |
| `WillowGame.WillowPlayerController:OnExpLevelChange` (POST, only when `bFeedback` or `bNaturalLevelup`) and `:WillowClientDisableLoadingMovie` (POST) | flags / none; iterate `obj.MissionPlaythroughs[obj.GetCurrentPlaythrough()].MissionList` (`Status`, `MissionDef`, `GameStage`) | every accepted mission after a level-up (`ExpLevelUp` increments `ExpLevel` then calls this; the flags skip the call the game makes at character load, when the PRI may still be stale) and after a map load (missions accepted before the bound was set, levels gained elsewhere; also clears `_rolled_stages`) |
| `WillowGame.QuestAcceptGFxMovie:UpdateMissionList` / `:DetermineQuestEntries` / `:extPopulateQuestEntries` (POST) | iterate `obj.MissionList[]` (`MissionDef`, `MissionStatus`), player `obj.WPCOwner` | backstop (the v0.4 primary): every accepted mission when an NPC's list is built; normally a no-op since v0.7, kept because it runs before any turn-in whichever order other mods' hooks run in |
| `WillowGame.QuestAcceptGFxMovie:SetRewardCard` (PRE) | `MissionDef`, `WPC`; same write if status in {1,2,3} | backstop when a reward card shows (still before Reward Reroller's turn-in hook) |
| `WillowGame.QuestAcceptGFxMovie:extCompleteConfirmed` (PRE) | none; `obj.MissionList[obj.GetSelectedIndex()]` after a bounds and status check, player `obj.WPCOwner` | backstop at the turn-in confirm; only beats the reroller's hook if ours registered first |
| `WillowGame.WillowPlayerController:ServerGrantMissionRewards` (PRE) | `Mission`, `bGrantAltReward`; same write, then the stage goes into `_rolled_stages` | right before the native roll, scripted completions included; expected once per player on the host, untested in co-op |
| `WillowGame.WillowPlayerController:ReceiveWeaponReward` / `:ReceiveItemReward` (PRE) | `Mission`, out `DefinitionData`; read only | check only: `ManufacturerGradeIndex` below the stage remembered at the roll means the roll read something else, logged as a "please report this" warning; no remembered roll (reroller path, a reward claimed in a later session) means no check |

All of this is single-player / host-side; in co-op the shared mission object can end up at
another player's level (documented, untested).

Reward Reroller (legacy mod the user plays with) blocks `ServerGrantMissionRewards` and
`MissionTracker:CompleteMission` and grants rewards itself from a PRE hook on
`QuestAcceptGFxMovie:extCompleteConfirmed`, reading `mission.GetGameStage()` from Python.
**Legacy mods' calls never trigger hooks**: `legacy_compat` wraps every legacy callback in
`prevent_hooking_direct_calls()` (`.willow2-mod-manager/src/legacy_compat/__init__.py:123`), so a
return override on `GetGameStage` (the v0.3 attempt) can't reach them. Only the field write
does, and it has to happen before their hook runs. Since v0.7 it happens at accept, on every
level-up and on every map load, so the mission has been at the player's level for a while by
the time the reroller reads it; the NPC-list and reward-card hooks stay as backstops that also
run before the reroller's turn-in hook. PRE hooks on one function run in registration order, so
our `extCompleteConfirmed` hook runs before the reroller's only when our mod was enabled first
(normal launch order). The reroller grants the mission's XP before it rolls, while the mission
is still ReadyToTurnIn, so a turn-in that levels the player rerolls at the new level; the
vanilla path marks the mission Complete before the XP, so there the item is one level below.

Where the targets come from: the factory hooks follow galqawala's EnemyBalancer (itself modelled on
RedxYeti's BL1 Enemy Randomizer); `WillowPawn:SetGameStage` is the one target apple1417's
`enemy_level_randomizer` ships; the loot and container targets and the intro-chest exclusion come
from EdricY's Bouncy-Loot-God `always_on_level` (the `MoonShotIntro_P` part from Adaptor-Face); the
mission grant hook is also hooked by RedxYeti's PayToLoot and its `GameStage` write is what
BouncyLootGod and Roguelands do before calling it. No code from any of them is in this mod; the
full credits list, with licences, is in `docs/sdk-notes.md` (Credits and prior art) and the
README's Credits section. Raid-boss dedicated
drops, Moxxi tips and slot-machine payouts (`Behavior_SpawnItems`) take their level from the pawn
or container they come from, so the hooks above cover them. See `docs/sdk-notes.md`.

## Later (deferred on purpose)

- Compatibility with the TPS character ports (Nisha, Athena, Doppelganger; all PythonSDK mods on
  Nexus). Plan: get their folders, grep their hook targets against ours, and if they overlap
  consider `Type.POST_UNCONDITIONAL` hooks that read back `obj.GetGameStage()` and only re-set
  out-of-band values, so other mods' pre-hooks run first.
- Known trade-offs, left simple on purpose: mission XP and cash follow the mission's raised level
  (the point of v0.7; if ever unwanted, a `(Block, value)` return override on
  `WillowGame.MissionDefinition:GetExperienceReward` is the lever, with the caveat that it is
  native and may not reach the game's own callers); base-game vendor stock keeps
  its vanilla `-2..0` level variance (`GD_Economy.VendingMachine.Init_VendingMachine_LootGamestageVariance`,
  a global object other mods edit too); the item of the day is exactly the machine's stage.
- Nexus Mods listing: Nexus can't be automated, so `docs/nexus.md` holds the summary, BBCode
  description, requirements, install steps and category for the user to paste.
- Willow2 mod database: listed via https://github.com/bl-sdk/bl-sdk.github.io/pull/261 (entry
  `_willow2_mods/EnemyItemScaling.md`, fork `CalebEaston/bl-sdk.github.io`). The page is built
  from `pyproject.toml`, so `tool.sdkmod.download` must stay the direct
  `releases/latest/download/enemy_item_scaling.sdkmod` link and `tool.sdkmod` may only hold the
  keys the database schema allows (see `docs/sdk-notes.md`, mod database section).
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
  vehicles, with the checks listed in `docs/testing-probes.md` section 9 (plain version: `docs/testing.md`
  section 8).
