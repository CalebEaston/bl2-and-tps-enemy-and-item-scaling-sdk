# SDK and game notes

Reference gathered on 2026-10-08 from the willow2-mod-manager v3.8 release, the `mods_base`,
`pyunrealsdk` and `willow2-mod-manager` repos, apple1417's `willow2-sdk-mods`, and third-party mods.
"Verified" = read in source. "Claim" = another author's statement about decompiled game code.

## Stack

- Release: https://github.com/bl-sdk/willow2-mod-manager/releases (v3.8 "Slammer", 2026-06-26).
  Ships `Binaries/Win32/ddraw.dll` (plugin loader), `Binaries/Win32/Plugins/{unrealsdk.dll,
  pyunrealsdk.dll, python314.*, unrealsdk.toml}` and `sdk_mods/` with `__main__.py`, `.stubs/`,
  `settings/` and the base packages as `.sdkmod` zips (`mods_base` 1.12, `willow2_mod_menu` 3.6).
- Legacy PythonSDK (https://github.com/bl-sdk/PythonSDK) was archived on 2025-01-01 per its GitHub
  page. Legacy mods still load through `legacy_compat`.
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
  `__main__.py`. The release ships `<game>/sdk_mods/__main__.py` as a plain file, so edit it in
  place, or point `init_script` at a checkout of the manager's `src/`.
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
- The embedded interpreter is Windows CPython under Wine: `pathlib.Path` is `WindowsPath`, and
  `mods_base.Game.get_current()` expects `sys.executable` to be `borderlands2.exe` (mod.py), so
  toml paths are Windows paths (`Z:\...`). Use TOML
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

## v2 research (2026-10-08): mission rewards, vendors, other item sources

Full briefs were produced by four readers over the prior-art mods, a generated UE3 SDK dump of
BL2's classes (`RobChiocchio/BL2-SDK`), game-generated stubs (`Justin99x/bl-py-stubs`) and
`apocalyptech/ft-explorer` object dumps. The facts the code relies on:

Mission rewards:
- `WillowGame.WillowPlayerController:ServerGrantMissionRewards(Mission, bGrantAltReward)` is a
  script function (hookable), run on the host once per player. Inside it the game rolls
  `Reward.RewardItems`/`RewardItemPools` into `PendingMissionRewardData.WeaponRewards[2]` /
  `ItemRewards[2]` at the mission's game stage, and computes XP and cash from the same stage.
  Hooked by PayToLoot (new SDK); BouncyLootGod and Roguelands write `MissionDefinition.GameStage`
  before calling it, which is what v2 does in a PRE hook.
- `MissionDefinition.GameStage` and `bGameStageLocked` are transient fields; an accepted mission
  is locked, an unaccepted one recomputes from `GameStageRegion` on every `GetGameStage()`.
  `GetGameStage()`, `GetItemRewardsForPlayer()`, `GetExperienceReward()` are native, so a return
  override would not reach the native reward roll; the field write does.
- Open in v2 (moot since v0.5/v0.7, which write both): whether the roll reads the per-player saved copy
  (`pc.MissionPlaythroughs[pt].MissionList[pc.NativeGetMissionIndex(m)].GameStage`) instead.
  Verified fallback: PRE hooks on `WillowPlayerController:ReceiveWeaponReward/ReceiveItemReward`
  (`Mission`, `DefinitionData`) rewriting `ManufacturerGradeIndex` (index 3) and `GameStage`
  (index 15) and re-calling (RogueLands RewardScaler pattern). Display-time alternative:
  `MissionRewardGFxObject:SetUpRewardsPage` rewriting `obj.RewardData` (ProjectileRandomizer).
- Reward pools gate on `Min/MaxGameStageRequirement` (`GD_Itempools.Scheduling.GameStage_NN`);
  raising the stage never falls below a minimum.

Vendors:
- `WillowVendingMachine` -> `WillowVendingMachineBase` -> `WillowInteractiveObject`; none of the
  vendor classes redeclare `SetGameStage`, so v1's `WillowInteractiveObject:SetGameStage` hook
  fires for them (if the factory calls it; juso40's factory reconstruction does
  `SetGameStage` -> ... -> `ResetInventory`). `WillowInteractiveObject` has plain `GameStage` and
  `ExpLevel` int properties.
- Stock level = machine stage + `-2..0` from `GD_Economy.VendingMachine.Init_VendingMachine_LootGamestageVariance`
  (base game; Torgue/Seraph vendors have no variance). Item of the day = `FeaturedItemGameStage`
  -> `GD_Population_Shopping.Balance.Init_FeaturedItem_GameStage` = `1 * GameStage + 0`, i.e.
  exactly the machine's stage. Sanctuary in-game observation: items 7-9 at stage 9.
- `WillowVendingMachine:ResetInventory()` regenerates stock and featured item at the stored stage;
  called at spawn, on the 20-minute global timer (`WillowGameInfo.SecondsUntilShopsReset`) and on
  paid resets (`WillowPlayerController:ServerPlayerResetShop`). apple1417's cheats call it via
  `find_all("WillowVendingMachine")`. v2 PRE-hooks it and calls `obj.SetGameStage(level)` first.
- Crazy Earl's black market sells SDUs built per player; not a level source.

Everything else:
- Candidate single choke point for "every freshly generated item" (not built; GUESS that the
  game's pool spawner calls it): `WillowGame.WillowWeapon:InitializeInventory` and
  `WillowGame.WillowItem:InitializeInventory`, events with params
  `(InBalanceDef, InManufacturer, InGradeIndex, InAdditionalQueryInterfaceSource)`, no out params,
  every inventory class resolves to one of the two, and `InGradeIndex` is the item level. A PRE
  hook could re-call with a clamped grade before parts are rolled; must skip player-owned items
  (`InAdditionalQueryInterfaceSource` a player class). Probe first: hook it log-only and see
  whether it fires for a pool drop. Rejected alternatives: `ItemPool:SpawnBalancedInventoryFromPool`
  (out param: block+re-call leaves the caller with nothing) and
  `Engine.WillowInventory:ClientInitializeInventoryFromDefinition` (universal but late, parts
  already rolled, runs on clients).
- (v2 design, superseded in v0.7, which restores nothing.) The mission hook restores
  `GameStage`/`bGameStageLocked` in a POST_UNCONDITIONAL hook on the
  same function (the rolled items keep their level; this only stops a repeatable mission, or
  another mod calling `ServerGrantMissionRewards` on an unaccepted mission, from inheriting a
  stale locked stage later in the session).
- Not built in v2 (the per-player copy has been written since v0.5; vendor re-rolls still not):
  also writing the per-player copy
  `obj.MissionPlaythroughs[pt].MissionList[idx].GameStage`, and re-rolling vendors on
  `WillowPlayerController:ExpLevelUp` (POST) via `find_all("WillowVendingMachine")` ->
  `ResetInventory()`. Each is a few lines if testing shows it is needed.
- `WillowGame.Behavior_SpawnItems:ApplyBehaviorToContext` (raid-boss dedicated drops, Warrior,
  BNK-3R, Moxxi tips, slot machine payouts, loot spewers) takes no level argument; the level comes
  from the context object's stage (pawn or interactive object), which the existing hooks set.
  Open: whether a pawn context uses `GetGameStage()` (enemy band) or
  `GetGameStageForSpawnedInventory()` (item band).
- Loot midgets, chubbies, Vermivorous, Terramorphous pool drops are ordinary pawn drops; loot
  midget containers spawn a pawn through the population system. Slot machines
  (`gd_slotmachine.SlotMachine`, Tina/Torgue variants), the dice chest, the golden chest and the
  treasure room chests are interactive objects.
- Alternative architecture (not taken): set every `GD_*_GameStages.Balance.*.BalanceByRegion[]
  .Min/MaxDefaultGameStage` to the player level on map load (Rossays' Game Scaler, juso40's
  ScaledTVHM). Moves everything at once, but is "set to player level" only, is cached per region
  on the controller, and does nothing in UVHM.
- Save-loaded, bank and memento items go through `InitializeFromDefinitionData` /
  `WillowPickup:CreatePickupFromMemento`; any future universal hook must skip them.

## Reward Reroller compatibility (v0.4; v0.3 attempt refuted)

(Superseded in v0.7, which raises the mission permanently and restores nothing; kept as history.)

ZetaDaemon's Reward Reroller (legacy mod, deps Enums + Structs, runs under `legacy_compat`) hooks
`QuestAcceptGFxMovie.extCompleteConfirmed` and grants the rewards itself (`grant_rewards`), then
blocks `ServerGrantMissionRewards` and `MissionTracker.CompleteMission` (returns False from both
hooks). Its first roll and every reroll call `mission.GetGameStage()` from Python
(`get_reward_data`, `validate_pool`) and build items with `InitializeInventory(balance,
manufacturer, gamestage, None)`. Rerolls cost 2 Eridium.

Verified fact that killed v0.3: `legacy_compat` appends `prevent_hooking_direct_calls` to its
compat handlers (`.willow2-mod-manager/src/legacy_compat/__init__.py:123`) and every legacy hook
callback runs inside `legacy_compat()` (`legacy_compat/unrealsdk/__init__.py:199-218`), so every
Python-to-Unreal call a legacy mod makes skips all hooks (`pyunrealsdk bound_function.cpp:218-220`
-> `inject_next_call`). A PRE return override on `MissionDefinition:GetGameStage` therefore never
fires for the reroller. Native callers never go through hooks either. What the native getter
returns for a locked mission is the `GameStage` field (prior-art claim, helios in-game notes), so
the field write is the only lever, and it must land before the reroller's hook runs.

v0.4 design: `_level_mission(mission, pc)` writes `GameStage` + `bGameStageLocked` (saving the
original with `setdefault`). Primary trigger: POST hooks on `QuestAcceptGFxMovie:UpdateMissionList`
(script, optional `OnlyIfThisMissionIsAlreadyInTheList`), `:DetermineQuestEntries` and
`:extPopulateQuestEntries`, iterating `obj.MissionList[]` (`StatusMenuMissionEligibilityData`:
`MissionDef`, `MissionStatus`, `bIsBlocked`, `bIsFiltered`) and levelling entries with status
1/2/3 for `obj.WPCOwner`; this runs when the NPC's list is built, before any turn-in, and does
not depend on hook order (verifier suggestion; which of the three fills the list is unverified,
hence all three). Second trigger: PRE `QuestAcceptGFxMovie:SetRewardCard(MissionDef, WPC)`
(script, flags 0x00040003) when `pc.GetPlayersMissionStatus(mission)` is Active (1),
RequiredObjectivesComplete (2) or ReadyToTurnIn (3); from PRE `QuestAcceptGFxMovie:
extCompleteConfirmed` as a backstop (mission = `obj.MissionList[obj.GetSelectedIndex()].MissionDef`,
player = `obj.WPCOwner`, the same fields the reroller reads); and from PRE
`ServerGrantMissionRewards` for scripted completions. Restored (POST_UNCONDITIONAL) in
`WillowPlayerController:MissionRewardsReceived(Mission)` (script, 0x00020103, i.e. after the
reward is accepted, so rerolls in between still read the player's level) and in the
`WillowPlayerController:UpdateMissionStatus(Mission, NewMissionStatus)` event when the status
becomes Complete (4): vanilla marks Complete before the roll (the grant hook re-levels right
after), the reroller marks Complete at accept input after its rolls. Verifier (2026-10-08)
could not refute the design; it rated the field-read-when-locked link medium-high (Ghidra +
helios XP sweep) and flagged co-op as unverified (host's shared mission object may carry a
client's level; restore is Simulated so the host never restores a client's turn-in). Open: whether
`SetRewardCard` is called for the turn-in screen (it is the movie that handles both accept and
complete) and whether `MissionRewardsReceived` fires on the reroller's accept path (if not, the
stage simply stays at the player's level; harmless). `EMissionStatus`: NotStarted 0, Active 1,
RequiredObjectivesComplete 2, ReadyToTurnIn 3, Complete 4, Failed 5.

## v0.5 (2026-10-08): first playtest findings

Enemies (reported: marauders at nameplate level 1 with player 4 and the enemy floor on, drops
at 4):

- The factory sequence for an AI pawn (juso40's reconstruction of
  `PopulationFactoryBalancedAIPawn.uc` lines 105-120, `MapLoader/placeablehelper/ai_pawn.py`):
  `SetGameStage(gs)`, `SetExpLevel(gs)`, `SetGameStageForSpawnedInventory(gs)`,
  `SetAwesomeLevel(0)`, `Controller.InitializeCharacterClass()`,
  `Controller.RecalculateAttributeInitializedState()`, `InitializeBalanceDefinitionState(bal, -1)`,
  `SetupPawnItemPoolList`, `AddDefaultInventory`. `gs` is the factory's own `GameStage` argument
  each time, so a hook that changes only the `SetGameStage` call leaves `ExpLevel` vanilla.
- `ExpLevel` is the nameplate (replicated `WillowAIPawn.ExpLevel`) and the `Level` term of the
  enemy health, shield and damage formulas (`D_Attributes.AI.AICharacterExperienceLevel`, see
  `Init_BaseEnemyHealth` etc. in the BLCM files quoted in the v2 research), initialised once at
  spawn. So the v0.1-v0.4 enemy hook produced vanilla enemies with on-level drops: exactly the
  report. apple1417's `enemy_level_randomizer` has the same limitation.
- v0.5: PRE hooks on `WillowGame.PopulationFactoryBalancedAIPawn:CreatePopulationActor` (event;
  BL2 params `Master, Opportunity, SpawnLocationContextObject, SpawnLocation, SpawnRotation,
  GameStage, AwesomeLevel` per the game-generated stubs) and `:RestorePopulatedAIPawn` (event;
  `Master, SpawnLocationContextObject, SpawnLocation, SpawnRotation, GameStage, AwesomeLevel,
  AIPawnMemento`): clamp `args.GameStage`, re-call `func(args)` (pyunrealsdk accepts the
  function's own args struct as the single argument) under `prevent_hooking_direct_calls()`,
  return `(Block, spawned)`. No fallback when the re-call returns None: EnemyBalancer saw None
  on BL1 for stages with no grade, but BL2's factory has no `GetPawnArchetypeForGrade`
  (`SelectGradeIndex` exists on `Engine.BaseBalanceDefinition`, the pawn grade is always -1),
  and a retry at the original stage would be pointless anyway because
  `prevent_hooking_direct_calls` only covers the direct call, not the factory's nested
  `SetGameStage`/`SetExpLevel` calls, which the safety nets would clamp again (review finding).
  `WillowPawn:SetGameStage` and `WillowAIPawn:SetExpLevel` (`NewExpLevel`; `WillowAIPawn`
  redeclares `SetExpLevel` but not `SetGameStage`) stay as safety nets for pawns that come
  through neither event; they are no-ops when the factory hook already clamped the argument.
- Consequence: a clamped enemy passes its clamped stage into `SetGameStageForSpawnedInventory`, so
  its drops follow the enemy level and the item band applies on top. Documented in the README.
- Not covered: enemy vehicles (`PopulationFactoryWillowVehicle:CreatePopulationActor`,
  `WillowVehicle:SetGameStage/SetExpLevel`), `WillowAIPawn:AILevelUp` transformations.

Mission rewards (reported: "This Town Ain't Big Enough" reward at 3 with player 6; whether the
toggle was on is unconfirmed). Superseded in v0.7, which raises the mission permanently and
restores nothing; kept as history:

- helios' in-game sweep proved XP follows the definition's `GameStage` of a locked mission, but
  nothing proves the native item roll (`GetItemRewardsForPlayer(WillowPC, out)`) reads the same
  field rather than the player's saved copy `MissionStatusPlayerData.GameStage`
  (`pc.MissionPlaythroughs[pc.GetCurrentPlaythrough()].MissionList[pc.NativeGetMissionIndex(m)]`,
  the value mopioid's Loot Randomizer uses as the reward level). v0.5 writes both (and restores
  both), reading the entry back and warning if the nested write did not take. The saved copy is
  written only from the `ServerGrantMissionRewards` PRE hook (right before the native roll, the
  only reader that could use it): it is what the save file stores
  (`PlayerSaveGame.MissionPlaythroughs[].MissionData`, Gibbed `MissionData.GameStage`), so writing
  it from the mission-list hook would persist a raised stage for any mission looked at and left
  for later. The definition's transient stage is still written from every trigger (the reroller
  reads that). `_saved_mission_stages` is cleared on `WillowClientDisableLoadingMovie` (POST) so a
  stage remembered for one character/playthrough is never restored into another's record.
- Accept-time safety net: PRE hooks on `WillowPlayerController:ReceiveWeaponReward` /
  `:ReceiveItemReward` (`Mission`, out `DefinitionData`, script Simulated|Final; this is what
  `MissionRewardGFxObject.AcceptReward` calls) rewrite `ManufacturerGradeIndex` and `GameStage`
  to the player's level and re-call `func(args)`, Block. The mission's own XP is granted inside
  `ServerGrantMissionRewards` before the reward UI opens, so a turn-in that levels the player up
  routinely makes the rolled item one level short at accept time: that is logged (with
  `Log Adjustments`) as an ordinary `reward item` adjustment. Only when the item is at the
  mission's ORIGINAL stage (`_saved_mission_stages[path][0]` or `[2]`) did the roll ignore the
  write; that case is always logged as a warning with "please report this". Parts were rolled at
  the old stage; mopioid ships the same grade/stage rewrite, so the item is valid. Reward
  Reroller grants its items without `ReceiveWeaponReward`, and other legacy mods' direct calls
  bypass hooks, so this net only sees the vanilla accept path.

## v0.6 (2026-10-09): The Pre-Sequel

Request: make the mod work in Borderlands: The Pre-Sequel. The SDK stack is shared
(willow2-mod-manager serves BL2, TPS and AoDK from one zip; `mods_base.Game.get_current()` maps
`borderlandspresequel.exe` to `Game.TPS`). What actually blocked TPS, and what was checked, all
against the game-generated stubs (`Justin99x/bl-py-stubs` `gamestubs.zip`, which has `bl2/`,
`tps/` and `common/` trees and no AoDK tree) plus galqawala's EnemyBalancer, which runs the same
factory hooks in TPS and logged live confirmations there (2026-08-23). An adversarial review
(five verifiers, SDK source included) checked every claim below; nothing has been played in TPS.

- `[tool.sdkmod] supported_games = ["BL2"]` was the real blocker: `mods_base.Mod.__post_init__`
  sets `enabling_locked = Game.get_current() not in supported_games`, the mod menu shows the mod
  as yellow `Incompatible` and `enable()` returns early. Now `["BL2", "TPS"]`.
- `WillowPlayerController.OverpowerChoiceValue` does not exist in TPS (the class has
  `NumOverpowerLevelsUnlocked`, nothing else Overpower-related; 0 matches in the `tps/` and
  `common/` trees). `player_level_for` read it whenever `GetCurrentPlaythrough()` was UVHM, which
  for a TPS UVHM character would raise `AttributeError` (pyunrealsdk `UObject.__getattr__` ->
  `py_find_field` -> `py::attribute_error`) inside every hook, making the mod a no-op for that
  character (Normal and TVHM never took the branch). Guarded by `has_overpower_levels()`, which
  looks the property up once with `UClass._find_prop` (ValueError when missing: unrealsdk's
  `UStruct::find*` throw `std::invalid_argument`, pybind11 maps that to ValueError). Field
  presence rather than `Game.get_current()`, because the latter logs an error and assumes BL2
  for an unknown executable name, and because AoDK (the BL2 build) presumably has the field.
- Every hook target exists in TPS with the same parameter names: both factory events (TPS's
  `CreatePopulationActor` has an extra optional `SpawnOwner` parameter at the end; we re-call
  `func(args)` with the struct, so it is passed through untouched; EnemyBalancer confirmed both
  `CreatePopulationActor` and `RestorePopulatedAIPawn` fire in TPS), `WillowPawn:SetGameStage`,
  `WillowAIPawn:SetExpLevel` (redeclared in TPS as in BL2), both
  `SetGameStageForSpawnedInventory`, `WillowInteractiveObject:SetGameStage`,
  `WillowVendingMachine:ResetInventory`, the three `QuestAcceptGFxMovie` list functions,
  `SetRewardCard`, `extCompleteConfirmed`, `GetSelectedIndex`, `ServerGrantMissionRewards`,
  `ReceiveWeaponReward`/`ReceiveItemReward` (same out `DefinitionData`),
  `WillowClientDisableLoadingMovie`, `MissionRewardsReceived` (no longer hooked since v0.7),
  `UpdateMissionStatus`,
  `NativeGetMissionIndex`, `GetCurrentPlaythrough`, `GetPlayersMissionStatus`. Fields:
  `MissionPlaythroughs` (TPS's `MissionPlaythroughData` has extra members but `MissionList` is
  still there), `MissionStatusPlayerData.GameStage`, `MissionDefinition.GameStage` /
  `bGameStageLocked`, `QuestAcceptGFxMovie.MissionList`, `PawnBalanceDefinition`,
  `WeaponDefinitionData` / `ItemDefinitionData.ManufacturerGradeIndex` + `GameStage`.
  `AIPawnBalanceDefinition` (`Grades`, `DefaultExpLevel`, `GetPawnArchetype`) is identical in
  both games and `PopulationFactoryBalancedAIPawn` differs only by an extra `GetMaxExtent` in
  TPS; neither has `GetPawnArchetypeForGrade`, so the no-fallback factory hook holds in TPS too.
- TPS mission API differences the mod does not use: `MissionDefinition.GetExpectedGameStage()`
  is BL2 only; TPS adds `GetMissionLevel(TestingWillowPC, bIncludeLevelAdjustment)`, an int
  `LevelAdjustment` field, `GetBadassRanksReward`, `GetOtherCurrencyReward`,
  `GetItemRewardInvPools`. The mod writes `GameStage` only; if TPS's reward roll goes through
  `GetMissionLevel(pc, True)` = stage + adjustment, a reward can sit `LevelAdjustment` above the
  mission's level by design. Probe in `docs/testing-probes.md` section 9.
- TPS-only object that matters: `WillowVendingMachineShift` (the SHiFT machine in Concordia)
  inherits `WillowInteractiveObject` directly, not `WillowVendingMachineBase`, and has its own
  `ResetInventory`, `GenerateGambleItemList`, `GetGambleItemOfTheDay`, `MaxGambleItems`;
  spawned by `PopulationFactoryVendingMachineShift` (`CreateInteractiveObject`). Without special
  handling the item band would treat it as a container. It is now classified as a vendor by name
  (`OPTIONAL_VENDOR_CLASS_NAMES`, looked up with `find_class` and skipped where the class doesn't
  exist; the required `WillowVendingMachineBase` is looked up outside the try so a typo still
  shows as a traceback) and its `ResetInventory` is hooked next to the ordinary one. Whether its
  factory calls `SetGameStage` at spawn, whether the shipped game exposes the gamble stock at all
  and whether that stock follows the stage are all unknown (nothing in
  `WillowShiftGambleInventoryDefinition` / `WillowShiftGambleItemDefinition` mentions a stage or
  level; no local source names its currency); harmless either way.
- Other `WillowInteractiveObject` subclasses only TPS has: `OzSupportDrone` (Wilhelm's Wolf and
  Saint) and `OzPlayerJumpPad`. Neither declares loot or stage members of its own; if the game
  ever calls `SetGameStage` on one, the item band would clamp it and log `container`. Left
  alone (a value at the player's level is always inside the band); watched in section 9.
- The grinder is `GrinderGFxMovie` + `GrinderRecipeDefinition` + `GrinderRecipe`; by the stub
  signatures (`GetGrindItemDefinitions(out ..., out TotalItemExpLevel, out TotalItemAwesomeLevel,
  ...)` feeding `GrinderRecipe.SpawnBalancedInventoryFromRecipe(TotalItemExpLevel, ...)`, no
  `GameStage` anywhere in the three classes) its output is levelled from the ingredients, so
  there is nothing to hook and the item floor never applies to it; unverified in-game. Also
  outside every hook in TPS: SHiFT machine rewards (`GetEntitlementLoot`,
  `ServerAwardItemRewardEarned`) and scripted weapon grants (`Behavior_SpawnWeapon*`).
- Intro-map containers: Bouncy Loot God's `always_on_level.py` refuses to lower an interactive
  object whose path starts with `MoonShotIntro_P.TheWorld` ("no loot in at least 1 chest") and
  likewise `Xmas_P.TheWorld` in BL2. v0.6 mirrors that: `on_interactive_object_game_stage` skips
  a lowering when `obj._path_name()` starts with `Xmas_P.` or `MoonShotIntro_P.`; raising is
  unaffected.
- Hooks on functions the running game doesn't have: `unrealsdk`'s `hook_manager.cpp add_hook`
  only inserts the entry into a table keyed by the function's object name (no object lookup,
  nothing that throws); matching happens when a function is called, by name and then full path.
  So `WillowVendingMachineShift:ResetInventory` registered in BL2 is inert, and the other target
  stacked on the same callback still matches. `HookType.get_active_count()` counts registrations
  (`has_hook`), so it reports the dead target as active; only resolving the function object
  proves it exists. `Mod.enable()` has no per-hook error isolation, so nothing that can raise may
  ever go into the hook-enable path.
- `unrealsdk.find_class` with a short name consults the SDK's class cache, filled once from
  `GObjects` on first use; a class loaded later (a script class from a DLC package) is only found
  through the fully-qualified form. Fine for the native WillowGame classes used here.
- Still Borderlands 2 wording that is correct for both: `UVHM_PLAYTHROUGH = 2` (TPS also has
  Normal/TVHM/UVHM), level caps are never hard-coded, `WillowPlayerPawn` exists in TPS.
- Not done: AoDK (probably the BL2 build, no stubs checked; `"AoDK"` in `supported_games` is
  probably the only change), TPS enemy vehicles, any in-game run. `docs/testing.md` section 8
  (plain) and `docs/testing-probes.md` section 9 (probes) are the first-run list.

## v0.7 (2026-10-09): missions follow the player, for good

Caleb's direction after v0.5/v0.6: "increase the actual level of missions to match the player's
level rather than forcing the reward to be the same level". So the mission's level itself is
raised and kept, and nothing is restored or patched afterwards. Reviewed by four agents plus
skeptics (SDK source, stubs, the ReBased analyses, prior art); unplayed.

What the game does (ReBased `NATIVE_MISSION_DISPATCH.md` B4, helios' 2026-09-23 sweep, stubs):

- `MissionTracker.ActivateMission` (native) resets progress, **locks the game stage** and grants
  the mission weapon at the `GameStageRegion` level, then the script hooks run in order:
  `WillowPlayerController.UpdateMissionStatus(Mission, Active)` per player,
  `ClientReceiveMissionStatus(MissionStatusData{Mission, Status}, optional GameStage)`,
  `TriggerMissionStatusChangedDelegates`. `AcceptMission(Mission, MissionDirector)` is the
  client-side entry of an NPC accept (synchronous in single-player; BouncyLootGod and mopioid's
  Loot Randomizer hook it); ECHO / cutscene / behavior accepts never call it. The player's record
  (`MissionStatusPlayerData`) is created by script on the controller (`AddMission`), most
  plausibly inside `UpdateMissionStatus`; whether a POST hook there already sees it, or only the
  later notifications do, cannot be read from stubs. Hence three idempotent accept-time hooks.
- A picked-up mission's level is `MissionDefinition.GameStage` with `bGameStageLocked` True;
  its XP and cash depend on that number only (no penalty for out-levelling). The per-player
  record `MissionStatusPlayerData.GameStage` (CPF_Edit) is what `SaveMissionSaveGameData` writes
  to disk and `ApplyMissionSaveGameData(SaveGame, bManageRewards)` /
  `FixupSavedMissionGameStage(PlaythroughIndex, out MStatus)` put back on load; the definition's
  fields are transient. BL2 and TPS declare all of these identically, as they do the new hook
  targets `AcceptMission`, `UpdateMissionStatus`, `ClientReceiveMissionStatus`,
  `OnExpLevelChange(bFeedback, bNaturalLevelup)` and `WillowClientDisableLoadingMovie()`.
  `GetLevelForMission(InMission)` returns a MAP name (helios), not a level.
- `ExpLevelUp(bCheated)` (script) increments `ExpLevel`, grants skill points, then calls
  `OnExpLevelChange` (ReBased `NATIVE_PROGRESSION`). It is also called once at character load
  with both flags off (RedxYeti's UltimateScavenger comment; RandomSkillSelector gates on
  `bNaturalLevelup`), when the PRI may still hold the previous character's level, so v0.7 skips
  that call and lets the map-load hook do the work. BouncyLootGod hooks `ExpLevelUp` POST
  instead; either works.
- `WillowClientDisableLoadingMovie` fires at the end of every map load, after Possess and the
  PRI swap (helios probe 2026-09-24), i.e. with the character's level and missions in place.

Design:

- `_level_mission(mission, pc, entry=None)`: `wanted = max(current, player)` for a locked,
  positive stage (raise only), else the player's level; writes `GameStage` + `bGameStageLocked`
  on the definition and `GameStage` on the player's record (looked up via
  `NativeGetMissionIndex` when not passed in); logs `mission <Name>: a -> b` only when the
  definition's stage changes (lock-only or record-only writes are silent). No read-back: the
  record is an in-place view (unrealsdk `WrappedStruct` over the array element), so a read-back
  can only ever return what was just written.
- Raise only (review finding): reward pools are gated by `MinGameStageRequirement`
  (`GD_Itempools.Scheduling.GameStage_NN`: 7 for most gear, 10 launchers, 15 relics, 16
  adaptive shields; DLC pools higher), Reward Reroller drops a pool below its gate and the native
  roll plausibly does the same, so lowering a mission locked above the player (a DLC mission
  accepted early, min 15/30 in Normal) could yield no reward at all. Raising never trips a gate.
- `_level_accepted_missions(pc)` walks `MissionPlaythroughs[GetCurrentPlaythrough()].MissionList`
  for `Status` in {1,2,3} (about 290 entries, a few property reads each; once per level-up and
  map load).
- Triggers: `AcceptMission` POST (after a `GetPlayersMissionStatus` check: the game can refuse
  an accept and the POST runs anyway), `UpdateMissionStatus` POST_UNCONDITIONAL (statuses 1..3),
  `ClientReceiveMissionStatus` POST (statuses 1..3; the last per-player notification, covers
  accepts with no NPC), `OnExpLevelChange` POST (flags checked), `WillowClientDisableLoadingMovie`
  POST (all accepted missions; also clears `_rolled_stages`), plus the v0.2/v0.4 backstops
  (grant; NPC list, reward card, `extCompleteConfirmed` with a bounds and status check now).
- Removed: `_saved_mission_stages`, `_restore_mission`, the `MissionRewardsReceived` hook, the
  Complete branch, the map-load clear, the accept-time rewrite of the reward item and the record
  read-back warning. `ServerGrantMissionRewards` PRE remembers `mission.GameStage` after
  levelling in `_rolled_stages[path]`; `ReceiveWeaponReward` / `ReceiveItemReward` warn only when
  `ManufacturerGradeIndex` is below that remembered stage (comparing with the live stage gave
  false positives: a repeatable mission re-accepted after a level-up with its old reward still
  unclaimed, or a level-up between roll and accept). No remembered roll (reroller path, a reward
  claimed in a later session, co-op client) means no check.
- Consequences, on purpose: raised levels persist in the save and stay after the option is
  turned off or the mod removed. A turn-in whose XP levels the player gives an item one level
  below the new level on the vanilla path (Complete is set before the XP, so the level-up walk
  skips the mission) and at the new level with Reward Reroller (it grants XP first, while the
  mission is still ReadyToTurnIn). The offer card and NPC list show the vanilla level until the
  mission is accepted (NotStarted missions are untouched); every raised mission reads as
  "Normal" difficulty in the log. A mission weapon keeps the region level it was granted at
  inside `ActivateMission`. In UVHM the saved stage includes the OP level. Co-op (untested):
  each hook uses the controller it fired for, so each player's record is written at that
  player's level and the grant hook re-levels the shared definition to the turning-in player
  right before the roll; the shared definition and the mission log show whichever player wrote
  last; the map-load walk only runs for local controllers.
- Open until played: whether the mission log number updates live (candidates: the definition's
  `GetGameStage()`, the record, in TPS `GetMissionLevel(pc, True)`; both copies are written so
  it should, `log_all_calls` probe in `docs/testing-probes.md` section 7); which accept-time
  hook first sees the record; whether `FixupSavedMissionGameStage` rewrites records on load (the mod would
  then re-raise on every load, logging a `mission` line each time); the TPS `LevelAdjustment`
  question from v0.6.

## v0.8 (2026-10-09): naming, the mission bound, the plain test plan

- Caleb asked for the games to be named everywhere ("BL2 & TPS"), for the description to say
  TPS *should* work but is untested, for `On-Level Mission Rewards` to become something like
  "Force Min Mission Level To Player Level", and for a test plan without console typing (he
  cannot paste into the in-game console).
- The option is now the spinner `Minimum Mission Level` (`Vanilla` / `Player Level` /
  `Within N Levels`), in the style of the other four bounds: `_level_mission` raises an accepted
  mission to `player - N`, never lowers. Everything else from v0.7 stands. The in-game mod name
  stays `Enemy and Item Scaling` (the mod list may truncate longer names; the games are in the
  description's first line, the README title and the Nexus title instead). Renaming the option
  orphans the old `On-Level Mission Rewards` value in the settings file; the changelog says so.
- `docs/testing.md` is now the plain checklist; the console probes and detailed scenarios moved
  to `docs/testing-probes.md` with only the option name updated (section 7).
- Caleb renamed the local checkout to `bl2-and-tps-enemy-and-item-scaling-sdk` the same day and
  then asked for the GitHub repository to follow: it is now
  `CalebEaston/bl2-and-tps-enemy-and-item-scaling-sdk` (GitHub redirects the old name; every
  URL in the docs and `pyproject.toml` was rewritten; the v0.6/v0.7 release pages moved with it).

## Willow2 mod database listing (2026-10-09)

Submitted as https://github.com/bl-sdk/bl-sdk.github.io/pull/261 from the fork
`CalebEaston/bl-sdk.github.io`, branch `add-enemy-item-scaling`, file
`_willow2_mods/EnemyItemScaling.md` (front matter only: `pyproject_url` pointing at the raw
`src/enemy_item_scaling/pyproject.toml` on `main`, `mod_categories: enemy loot gameplay`). The
site builds the page from the pyproject: title from `tool.sdkmod.name`, description from
`project.description`, links from `project.urls`, download from `tool.sdkmod.download`.

What the database's validators (`_validate_pyproject.py`, `_validate_categories.py`, run in CI
on every PR) require, and therefore what must stay true in `pyproject.toml`:
- `tool.sdkmod.download` must be a DIRECT `.sdkmod`/`.zip` link whose file name matches the
  single root folder inside: `releases/latest/download/enemy_item_scaling.sdkmod` (a releases
  page URL fails). GitHub keeps that URL pointing at the newest release, so no PR is needed per
  version; the site re-reads the pyproject on each build.
- `tool.sdkmod` may only contain name, version, mod_type, supported_games, coop_support,
  license {name, url}, download, auto_enable, uses_native_modules. No license is declared (the
  repo has no LICENSE file); add one to both if Caleb picks a licence.
- `pyproject_url` must be `raw.githubusercontent.com` (CORS), never `github.com/.../raw/`.
- Categories come from `_data/categories.yml` (enemy, loot, gameplay, gear, utility, ...).
Both validators passed locally before the PR (`<scratch venv>/bin/python _validate_pyproject.py
front_matter _willow2_mods/EnemyItemScaling.md`). `_data/reviews.yml` lists manually reviewed
mods; ours is unreviewed until a bl-sdk reviewer looks at it.

## Credits and prior art (audited 2026-10-09)

Caleb asked whether other mods were used and who to credit. A six-agent audit compared every
source below against `src/enemy_item_scaling/__init__.py` line by line: no code was copied or
closely adapted; what was taken is hook target names, game facts and the SDK's documented
re-call-and-Block idiom, none of which carries a licence obligation. Player-facing credits are in
the README's Credits section and the Nexus page text; this is the full list.

| Source | Author | Licence | What it gave this mod |
|---|---|---|---|
| PythonSDK: willow2-mod-manager, mods_base, pyunrealsdk, unrealsdk | apple1417 and bl-sdk contributors | LGPL-3.0 | the runtime and API; not bundled in the `.sdkmod` (players install it), so LGPL imposes nothing |
| Enemy Level Randomizer | apple1417 | GPL-3.0 | `WillowPawn:SetGameStage` target, player-pawn skip, the re-call idiom in a shipped mod |
| Apple's Borderlands Cheats, Vendor Edit | apple1417 | GPL-3.0 | facts: `ResetInventory` restocks a vendor; item level is `ManufacturerGradeIndex` |
| EnemyBalancer | galqawala | GPL-3.0 | the population-factory spawn hooks behind v0.5; live TPS confirmations |
| Enemy Randomizer (BL1) | RedxYeti | GPL-3.0 | origin of EnemyBalancer's factory re-invoke technique |
| Bouncy Loot God | EdricY; `MoonShotIntro_P` exclusion by Adaptor-Face | MIT (metadata only) | loot and container hook targets, intro-chest exclusion, mission `GameStage` write |
| Borderlands Loot Randomizer | mopioid | none found | where the per-player mission record lives |
| MapLoader, RogueLands (bl2sdk_Mods) | juso40 | MIT | the factory setup sequence (diagnosed the first bug report); the reward re-level pattern (v0.5/v0.6, a check since v0.7) |
| Pay To Loot, Random Skill Selector, Ultimate Scavenger | RedxYeti | GPL-3.0 | `ServerGrantMissionRewards` and map-load hooks; the load-time `OnExpLevelChange` call |
| Reward Reroller | ZetaDaemon | GPL-3.0 | compatibility target; its source set the timing of the mission writes |
| Helios Tracker research notes | ZooLSmith | GPL-3.0 | in-game probes: mission level locking, XP curve, vending, cutscenes |
| BL2_ReBased native-analysis notes | zuhuHix and OpenWillow contributors | MIT | mission dispatch and level-up rules (marked unverified by its authors) |
| bl-py-stubs | Justin99x | none found | dev only: BL2/TPS class and parameter names |
| BL2-SDK dump | RobChiocchio (after McSimp's Borderlands2SDK) | none found | dev only: function flags, struct layouts |
| FT/BLCMM Explorer | apocalyptech | BSD-3-Clause | dev only: item pool and vendor data |
| BLCM wiki, BLCMods | BLCM community | none found | dev only: GameStage scheduling gates, enemy health formulas |
| Official SDK install guide (bl-sdk.github.io) | bl-sdk contributors | none found | the README install steps are condensed from it, and say so |
| bl-sdk repos' ruff/pyright config | apple1417 | GPL-3.0 / LGPL-3.0 | the root `pyproject.toml` lint lists are copied verbatim; dev only, never shipped |

Looked at and not used: juso40's ScaledTVHM and BadassBounties, Rossays' Game Scaler, RedxYeti's
Projectile Randomizer. If code from any GPL source is ever copied in, the mod would have to be
GPL-3.0; keep borrowing ideas and facts, not code.
