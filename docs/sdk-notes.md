# SDK and game notes

Reference gathered on 2026-10-08 from the willow2-mod-manager v3.8 release, the `mods_base`,
`pyunrealsdk` and `willow2-mod-manager` repos, apple1417's `willow2-sdk-mods`, and third-party mods.
"Verified" = read in source. "Claim" = another author's statement about decompiled game code.

## Stack

- Release: https://github.com/bl-sdk/willow2-mod-manager/releases (v3.8 "Slammer", 2026-06-26).
  Ships `Binaries/Win32/ddraw.dll` (plugin loader), `Binaries/Win32/Plugins/{unrealsdk.dll,
  pyunrealsdk.dll, python314.*, unrealsdk.toml}` and `sdk_mods/` with `__main__.py`, `.stubs/`,
  `settings/` and the base packages as `.sdkmod` zips (`mods_base` 1.12, `willow2_mod_menu` 3.6).
- Legacy PythonSDK is archived (2025-01-01). Legacy mods still load through `legacy_compat`.
- Install guide / mod DB: https://bl-sdk.github.io/willow2-mod-db/  (FAQ has the Proton notes)
- Developer Discord: https://discord.gg/VJXtHvh

## Loader (`sdk_mods/__main__.py`, verified)

- Mod folders = `sdk_mods/` + each `mod_manager.extra_folders` entry from `unrealsdk.user.toml`
  (merged over `unrealsdk.toml`, both next to `unrealsdk.dll`). Each is scanned: every non-dot
  subfolder is `importlib.import_module(name)`'d; names containing `.` are rejected;
  `X/X/__init__.py` double nesting only logs an error. `.sdkmod` = zip with one root folder named
  like the file. A folder beats a `.sdkmod` of the same name; `sdk_mods/` beats extra folders.
- Legacy detection regex on the first 1024 bytes of `__init__.py`:
  `from (\.\.ModMenu|Mods(\.\S+)?) import|BL2MOD\):`
- Import failures show only the last traceback frame unless `FULL_TRACEBACKS = True` in
  `__main__.py` (only editable when `init_script` points at a checkout of the manager's `src/`).
- `mod_manager.extra_sys_path` adds plain import paths that are not scanned for mods (3.8+).
- Settings: `<MODS_DIR>/settings/<module>.json` with `{"enabled", "options", "keybinds"}`; written
  on enable/disable and when leaving a mod's options screen. Missing file = mod starts disabled.

## mods_base API (verified, identical in shipped 1.12 and repo 1.13 except `reset()`)

- `build_mod(*, options=, hooks=, keybinds=, commands=, on_enable=, on_disable=, name=, ...)`:
  keyword-only; reads `[tool.sdkmod] name/version/auto_enable/mod_type/supported_games/coop_support`
  then `[project] name/version/description/authors`; `supported_games` and `coop_support` are
  case-sensitive enum member names (`"BL2"`, `"HostOnly"`; unknown silently dropped). Injects
  `__version__`/`__version_info__` into the module. Auto-collects module-level `BaseOption`,
  `HookType`, `KeybindType`, `AbstractCommand` instances and `on_enable`/`on_disable` functions.
  `GroupedOption`/`NestedOption` must be passed explicitly.
- `@hook(hook_func, hook_type=Type.PRE, *, immediately_enable=False, hook_identifier=None)`;
  decorators stack. PRE returns `Block | type[Block] | None` or `(signal, return_override)`;
  POST/POST_UNCONDITIONAL return None. `HookType.pause()` context manager exists.
- `unrealsdk.hooks`: `Type.PRE/POST/POST_UNCONDITIONAL`, `Block`, `Unset`,
  `prevent_hooking_direct_calls()` (only suppresses hooks on direct `BoundFunction` calls).
- `unrealsdk`: `find_object(cls, name)`, `find_class(name)`, `find_all(cls, exact=True)`,
  `construct_object(...)`, `make_struct(name, **fields)`, `config` (merged toml). Missing lookups
  raise `ValueError`; missing fields on an object raise `AttributeError`.
- `UObject`: `Class`, `Name`, `Outer`, `_path_name()`, `Class._inherits(other_class)`,
  `Class.ClassDefaultObject`. `BoundFunction.__call__` returns the plain return value, or a tuple
  `(ret, *out_params)` if there are out params; `Ellipsis` for void.
- `get_pc()` -> local `WillowPlayerController` (`WillowGameEngine_0.GamePlayers[0].Actor`);
  may be `None` during loading screens.
- Options: `SpinnerOption(identifier, value, choices, wrap_enabled=False, *, description=...)`,
  `BoolOption(identifier, value, true_text=None, false_text=None, ...)`,
  `SliderOption(identifier, value, min_value, max_value, step=1, is_integer=True, ...)`,
  `DropdownOption`, `GroupedOption`, `NestedOption`, `HiddenOption`, `ButtonOption`,
  `KeybindOption`. `on_change_anytime=` / `on_change_while_enabled=` kwargs or
  `.set_on_change()` (returns the option, so it must be the outermost decorator).
- `rlm <module glob>` console command reloads modules; `build_mod` deregisters the previous
  instance via the shared settings file so the menu doesn't get duplicates.

## Game-side level mechanics

Enemy level ("game stage"):

- Verified in shipped code: `WillowGame.WillowPawn:SetGameStage(NewGameStage)` fires for every
  pawn spawn, including `WillowPlayerPawn` (skip it). apple1417's `enemy_level_randomizer` PRE-hooks
  it, re-calls `func(new)` under `prevent_hooking_direct_calls()` and returns `Block`.
  https://github.com/apple1417/willow2-sdk-mods/tree/master/enemy_level_randomizer
- Prior art, EdricY Bouncy-Loot-God `always_on_level.py` (new SDK): stacks PRE hooks on
  `WillowPawn:SetGameStage`, `WillowInteractiveObject:SetGameStage`,
  `WillowPawn:SetGameStageForSpawnedInventory`, `WillowAIPawn:SetGameStageForSpawnedInventory`;
  reads `args.NewGameStage` / `args.NewInventoryGameStage`; target
  `get_pc().PlayerReplicationInfo.ExpLevel`; modes always/only-up/only-down. It skips interactive
  objects whose path starts with `Xmas_P.TheWorld` and `MoonShotIntro_P.TheWorld` when DOWN-levelling
  ("ruins christmas" / an intro chest spawns empty). Its `pawn.py` uses
  `pc.PlayerReplicationInfo.ExpLevel + pc.OverpowerChoiceValue` as the effective level.
  https://github.com/EdricY/Bouncy-Loot-God
- Prior art, galqawala EnemyBalancer (new SDK, BL1/BL2/TPS, `coop_support = "HostOnly"`):
  PRE-hooks `WillowGame.PopulationFactoryBalancedAIPawn:CreatePopulationActor` (BL2 args
  `Master, Opportunity, SpawnLocationContextObject, SpawnLocation, SpawnRotation, GameStage,
  AwesomeLevel, SpawnOwner`) and `:RestorePopulatedAIPawn`, re-invokes with a new `GameStage` and
  returns `(Block, spawned)`; keeps `WillowPawn:SetGameStage` / `WillowAIPawn:SetExpLevel`
  (`NewExpLevel`) as safety nets; rescales already-alive enemies via `find_all("WillowMind")` ->
  `mind.Pawn.SetGameStage(n)` / `.SetExpLevel(n)`; clamps to `pc.GetMaxExpLevel()`.
  CLAIM from its docstring: the factory picks the balance grade (health etc.) from `GameStage`
  BEFORE the pawn exists, so changing `SetGameStage` afterwards may only change the displayed level.
  apple1417's shipped mod relies on the `SetGameStage` hook regardless, so test in-game which it is.
  CLAIM: asking for a stage with no matching grade makes `CreatePopulationActor` return None (no
  spawn). https://github.com/galqawala/EnemyBalancer
- Region stage (what BLCMM "area scaling" mods edit): `GD_GameStages.Balance.*.BalanceByRegion[]
  .Min/MaxDefaultGameStage`; `pc.GetGameStageFromRegion(region)`; cached per region+playthrough on
  the controller (`pc.RegionGameStages`). Not used by this mod.
- Vehicles: `WillowVehicle:SetGameStage` / `:SetExpLevel` exist (EnemyBalancer hooks them);
  unknown whether our `WillowPawn:SetGameStage` hook also sees them.

Item level:

- Verified in shipped code: an item's level is `DefinitionData.ManufacturerGradeIndex` with
  `DefinitionData.GameStage` kept in sync (`vendor_edit`). Items are spawned from pools via
  `ItemPool.SpawnBalancedInventoryFromPool(Definition, GameStage, AwesomeLevel, ContextSource,
  SpawnedInventory /*out*/, [variance])`; hooking that with block+recall would lose the out param,
  so prefer the setters above. Balances cap at
  `Manufacturers[].Grades[].GameStageRequirement.MaxGameStage` (see legacy `ItemLevelUncapper`).
- CLAIM (BL2_ReBased notes): a dropped item's level is the game stage it spawned at; enemy drops use
  the dropper's stage with no variance; interactive objects apply `LootGameStageVarianceFormula`;
  the pool clamps into `Min/MaxGameStageRequirement`.
- Open: whether enemy drops use the pawn's `SetGameStage` value or the separate
  `SetGameStageForSpawnedInventory` value (decides whether the item bounds act on enemy loot at
  all when the enemy bounds are vanilla). Test in-game with `Log Adjustments` on.
- Not covered yet: vending machines (`FeaturedItemGameStage`, `GD_Economy.VendingMachine.*`),
  mission rewards (`MissionDefinition.GetGameStage()`), already-spawned enemies on level-up
  (`WillowPlayerController:ExpLevelUp` POST hook is the obvious trigger).

## Proton / Linux

- Steam launch options: `WINEDLLOVERRIDES="ddraw=n,b" %command% -pf_tricks=vcrun2022`; the FAQ
  recommends recent Proton GE builds and notes some builds hit a pybind "returned NULL without
  setting an exception" bug that the loader reports at startup (`check_proton_bugs`).
- The embedded interpreter is Windows CPython under Wine: `pathlib.Path` is `WindowsPath`,
  `sys.executable` is `borderlands2.exe`, so toml paths are Windows paths (`Z:\...`). Use TOML
  literal strings (`'...'`) to avoid escaping backslashes. Forward slashes probably work but are
  untested.
- Console key defaults to Tilde (`WillowInput.ini` `ConsoleKey=`); press twice.
- `[unrealsdk] console_log_level = "DEV_WARNING"` in the user toml shows dev warnings (for example
  "Extra mod folder does not exist") in the in-game console.

## TPS character port mods the user plays with

All three are PythonSDK mods on Nexus (not BLCMM text mods), so they can register hooks:
- Nisha (LJBreeze): https://www.nexusmods.com/borderlands2/mods/654
- Athena (GoldenBoy444 / "Leon"): https://www.nexusmods.com/borderlands2/mods/661  (serializes its
  own items; no co-op; compatible with the Nisha mod)
- Doppelganger (Jack): https://www.nexusmods.com/borderlands2/mods/666  (rebuilds Jack's files from
  a TPS install on first launch; Jack has no melee animation if Athena is also installed)
Nexus blocks automated fetches; to audit their hook targets, grep their mod folders for `@hook(` and
`add_hook(`.
