# Detailed test plan and console probes

The developer version: console probes (which need typing or pasting into the console) and the
full scenarios with expected log lines. The plain playtest checklist is [testing.md](testing.md).

This is the order to check things in, and what each check settles. Turn on `Log Adjustments` for
all of it. Log lines look like `[Enemy and Item Scaling] spawn PawnBalance_Marauder: 3 -> 15
(player 15)` with the kind being `spawn` (the factory hook), `enemy` / `enemy level` (the two
safety nets; silent when the factory hook already did the work), `loot`, `container` or
`vendor`, and only appear when a level actually changed. The lines `vendor restock X: a -> b`
and `mission M: a -> b` have no `(player N)` suffix.

First playtest (2026-10-08, v0.2-v0.4, Southern Shelf, player 4 then 6): enemies kept their
nameplate level while their drops scaled (fixed in v0.5 by hooking the population factory, see
scenario 1), and "This Town Ain't Big Enough" gave a level-3 reward at player level 6 with the
mission toggle believed on (v0.5 answered it with a player's-copy write and an accept-time
rewrite of the item, both replaced in v0.7 by raising the mission itself, see section 7; whether
the toggle was on and what the log said is still to be confirmed).

## 0. Console probes (before trusting anything)

Open the console (tilde twice) after enabling the mod from the `MODS` menu.

Mod registered and hooks live (expect `True` and a list of non-zero counts, one per hook
function; stacked hooks show 2 or 3. A count only proves the hook is registered, not that the
function exists in this game: the vendor-reset entry shows 2 in both games although its
Pre-Sequel target never fires in Borderlands 2. The hook-target probe below is the one that
proves existence):

```
py import enemy_item_scaling as m; print(m.mod.is_enabled, [h.get_active_count() for h in m.mod.hooks])
```

Player-level fields resolve (all three must print; repeat in Normal mode with an OP-unlocked
character and check that `OverpowerChoiceValue` is what you expect there). In The Pre-Sequel
leave `pc.OverpowerChoiceValue` out: the field only exists in Borderlands 2 and the mod doesn't
read it there (`m.has_overpower_levels()` must print `False`).

```
py from mods_base import get_pc; pc = get_pc(); print(pc.PlayerReplicationInfo.ExpLevel, pc.OverpowerChoiceValue, pc.GetCurrentPlaythrough())
```

Every hook target exists and has the parameter name the code reads (a `ValueError` names a missing
function; it's fine if exactly one of the two `SetGameStageForSpawnedInventory` paths is missing):

```
py import unrealsdk; print([(f, [p.Name for p in unrealsdk.find_object('Function', f)._properties()]) for f in ('WillowGame.PopulationFactoryBalancedAIPawn:CreatePopulationActor', 'WillowGame.PopulationFactoryBalancedAIPawn:RestorePopulatedAIPawn', 'WillowGame.WillowPawn:SetGameStage', 'WillowGame.WillowAIPawn:SetExpLevel', 'WillowGame.WillowPawn:SetGameStageForSpawnedInventory', 'WillowGame.WillowAIPawn:SetGameStageForSpawnedInventory', 'WillowGame.WillowInteractiveObject:SetGameStage', 'WillowGame.WillowPlayerController:ReceiveWeaponReward', 'WillowGame.WillowPlayerController:ReceiveItemReward', 'WillowGame.WillowPlayerController:AcceptMission', 'WillowGame.WillowPlayerController:UpdateMissionStatus', 'WillowGame.WillowPlayerController:ClientReceiveMissionStatus', 'WillowGame.WillowPlayerController:OnExpLevelChange', 'WillowGame.WillowPlayerController:WillowClientDisableLoadingMovie', 'WillowGame.WillowPlayerController:ServerGrantMissionRewards')])
```

Expect `GameStage` among the factory functions' params, `NewGameStage` for the `SetGameStage`
functions, `NewExpLevel` for `SetExpLevel`, `NewInventoryGameStage` for the inventory ones,
`Mission`, `DefinitionData` for the reward ones, `Mission`, `MissionDirector` for
`AcceptMission`, `Mission`, `NewMissionStatus` for `UpdateMissionStatus`, `MissionStatusData`,
`GameStage` for `ClientReceiveMissionStatus`, `bFeedback`, `bNaturalLevelup` for
`OnExpLevelChange`, nothing for `WillowClientDisableLoadingMovie` and `Mission`,
`bGrantAltReward` for `ServerGrantMissionRewards`.

## 1. Enemy floor

Level 15+ character, Normal mode. `Minimum Enemy Level = Player Level`, the other four `Vanilla`.
Go to Southern Shelf (vanilla level 1-5).

- Expect one `spawn PawnBalance_...: 2..5 -> 15 (player 15)` line per bullymong/bandit spawn, and
  no `enemy` / `enemy level` lines for those same spawns (the factory already passed 15 in).
- Nameplates should read 15 and enemies should be noticeably tougher.
- Playtest result before v0.5: with only the `WillowPawn:SetGameStage` hook, nameplates stayed at
  the vanilla level while drops scaled. The factory sets `ExpLevel` (nameplate, and the input of
  the health/damage formulas) from its own `GameStage` argument right after `SetGameStage`, so
  the argument is what has to change.
- If an enemy type stops spawning at all with the floor on (an empty den that fills when the
  floor is set back to `Vanilla`), the factory returned nothing for that stage; report the
  enemy type and the levels.
- If an enemy still shows a vanilla level with no `spawn` line, it came through neither factory
  function; look for an `enemy` / `enemy level` line for it, and if there is none either, find
  its spawn path (`SpawnAIPawn`, `Behavior_SpawnFromPopulationSystem`).

## 2. Item floor

Same map. `Minimum Enemy Level = Vanilla`, `Minimum Item Level = Player Level`.

- Expect `loot WillowAIPawn_N: 3 -> 15` at each spawn and `container WillowInteractiveObject_N:
  3 -> 15` for chests.
- Kill enemies and compare the level of the gun they were holding against any other drop. Open the
  Liar's Berg red chest: items should be 15 (plus or minus the chest's variance).
- If the held weapon is 15 but pool drops stay at 3, enemy death drops take their level from the
  enemy's own stage, not the inventory stage. Then the item floor can only reach them through the
  enemy floor; note it in the README and look at `ItemPool:SpawnBalancedInventoryFromPool` for v2.

## 3. Ceiling

Fresh character around level 5. `Maximum Enemy Level = Player Level`. Go to Three Horns Divide
(vanilla 8-11). Expect `enemy ... : 9 -> 5` lines and level-5 nameplates.

## 4. Vanilla

All five spinners on `Vanilla` and `On-Level Vendors` off: no log lines at all, on any map.

## 5. Within N

`Minimum Enemy Level = Within 3 Levels` at level 15 in Southern Shelf: lines end in `-> 12`.

## 6. After every map load

Search `<game>/Binaries/Win32/Plugins/unrealsdk.log` for `Traceback`, `NoneType` and
`(player 0)`. Any hit is a failure of the player-level guard in `get_player_level()`.

## Things only the game can tell us

- Whether `WillowGame.WillowVehicle:SetGameStage` is a separate function (enemy-driven vehicles
  would then keep their vanilla level until a hook is added for it).
- Whether vending machines go through `WillowInteractiveObject:SetGameStage` (they are
  interactive objects); if they do, the item band already affects their stock.
- Whether down-levelling chests in Mercenary Day (`Xmas_P`) breaks them, as Bouncy-Loot-God's
  exclusion suggests.

## 7. Mission rewards (v0.7: missions follow the player)

`Minimum Mission Level = Player Level`, `Log Adjustments` on, a character a few levels above a side
mission it hasn't accepted yet (e.g. level 15 in Southern Shelf).

- Accept the mission: expect one `mission <Mission_...>: 5 -> 15` line as you accept it (three
  hooks can print it, `UpdateMissionStatus`, `ClientReceiveMissionStatus` and `AcceptMission`;
  the first to see the level prints, the others are silent), and the mission log showing it at
  level 15 straight away. If the log still shows 5, the log reads something other than the
  mission's stage: run `py import unrealsdk; unrealsdk.hooks.log_all_calls(True)` with the log
  open for a second, turn it off again, and grep the calls log for `GetGameStage`,
  `GetExpectedGameStage` and `GetMissionLevel`.
- Accept a plot mission that is handed out by an ECHO or a cutscene rather than an NPC: same
  line, same log level. That is the `ClientReceiveMissionStatus` hook earning its keep.
- Level up with it still open: one `mission ...` line per accepted mission that was below the
  new level; the log numbers follow.
- Save-quit-continue: the mission log must still show the raised level and the load must not
  print a `mission` line for it. A `mission X: 5 -> 15` line on every load means the game put
  the vanilla stage back on load (`FixupSavedMissionGameStage`, which the mod does not hook)
  instead of using the saved record; the mod raises it again each time, so the feature still
  works, but report it with the line.
- Turn it in: the reward card shows gear at your level and the XP is what a level-15 mission
  gives (noticeably more than the log said before you accepted). No `reward item ... (please
  report this)` warning. If that warning appears, the roll read something other than
  `GameStage` (`MissionDefinition.ExpLevel`? in The Pre-Sequel `LevelAdjustment`?), and
  rewriting the item at `ReceiveWeaponReward` / `ReceiveItemReward` (the v0.5 approach) goes
  back in.
- Turn in a mission whose XP levels you up: the reward is either one level below your new level
  (vanilla order: the mission is marked complete before the XP, so the level-up skips it) or at
  the new level (Reward Reroller grants the XP first). Both are expected; only an item below the
  level the mission had when it was rolled is a report.
- A mission accepted above your level (a DLC mission taken early): never lowered. Expect no
  `mission` line for it until you catch up with it.
- With Reward Reroller: rerolls come out at your level.
- Set the bound back to `Vanilla`: missions already raised keep their level (it is in the save); newly
  accepted ones stay vanilla.

## 8. Vendors (v2)

`On-Level Vendors` on, level 15+ character, Southern Shelf (vanilla vendors around level 3-5).

- On map load expect `vendor WillowVendingMachine_N: 3 -> 15` per machine (it is logged as
  `vendor`, not `container`). If no vendor line appears at all, the factory sets the machine's
  stage natively and the restock hook is the only lever: wait for a restock or pay for one.
- Open a weapon vendor: stock should be level 13-15 (vanilla rolls `-2..0` below the machine's
  level) and the item of the day exactly 15.
- Pay to reset a machine (or wait 20 minutes): expect a `vendor restock ...` line only if your
  level changed since the machine spawned, and the new stock at the new level. If the paid reset
  logs but the 20-minute restock never does, the timer bypasses `ResetInventory`; stack
  `@hook("WillowGame.WillowVendingMachine:ClearInventory")` on the same callback.
- With the toggle off, vendors must be untouched even when the item bounds are set.

## 9. The Pre-Sequel (v0.6)

Same mod file, same SDK zip, installed into the Pre-Sequel game folder (`BorderlandsPreSequel`,
Steam app id 261640 for `protontricks`). Nothing here has been played yet; the hook targets were
only checked against the game's class stubs.

- Main menu `MODS`: the mod's status must read `Disabled`/`Enabled`, not the yellow
  `Incompatible` the manager shows for a game missing from `supported_games` (v0.5 and earlier
  declared `supported_games = ["BL2"]`, which locks the toggle in any other game).
- Probes from section 0, minus `OverpowerChoiceValue`:
  `py import enemy_item_scaling as m; print(m.mod.is_enabled, m.has_overpower_levels(), [h.get_active_count() for h in m.mod.hooks])`
  expects `True False [...]`, and the hook-target probe must list every function (the
  `CreatePopulationActor` params end in an extra `SpawnOwner`, which is expected).
- Scenario 1 (enemy floor) in Regolith Range or Serenity's Waste with a high-level character:
  `spawn PawnBalance_...` lines and matching nameplates. Scenario 2 (item floor): `loot` lines.
- Claptastic Voyage with the enemy floor on: EnemyBalancer saw `.exe` badasses there come
  through neither factory function, so expect `enemy <name>: a -> b` and `enemy level <name>`
  lines instead of `spawn` lines for them, with nameplates and health to match.
- A fresh character with `Maximum Item Level = Player Level`: every chest in the intro
  (`MoonShotIntro_P`) must still spawn loot. The mod refuses to lower containers there (and in
  Mercenary Day's `Xmas_P`), mirroring Bouncy Loot God, which found an empty chest otherwise. A
  `container` line for one of them means the path prefix is wrong; report the object's path.
- Wilhelm's Wolf and Saint drones and the jump pads are interactive objects too
  (`OzSupportDrone`, `OzPlayerJumpPad`). Expect no `container OzSupportDrone...` lines; if they
  appear, report them.
- Concordia with `On-Level Vendors` on: a `vendor WillowVendingMachine_N: a -> b` line per
  ordinary machine, and ideally a `vendor WillowVendingMachineShift_N: a -> b` line for the SHiFT
  machine (it is a plain interactive object there, so it is classified as a vendor by name; if
  its factory never calls `SetGameStage` there will be no `vendor WillowVendingMachineShift_N`
  line at map load, only a `vendor restock WillowVendingMachineShift_N: a -> b` line when it
  resets). Whether its gamble items (if the shipped machine offers any) follow the stage is
  unknown; compare their level before and after.
- Section 7 (mission rewards) in Concordia: a side mission you accept there is raised as you
  accept it; one accepted earlier and left over is raised as the map loads (one `mission` line
  at load instead of at accept). The Pre-Sequel adds `MissionDefinition.GetMissionLevel(pc, bIncludeLevelAdjustment)` and a
  `LevelAdjustment` field that Borderlands 2 lacks. Before turning in, with `i` the mission's
  index in your log, print
  `py from mods_base import get_pc; pc = get_pc(); m = pc.MissionPlaythroughs[pc.GetCurrentPlaythrough()].MissionList[i].MissionDef; print(m.Name, m.GetGameStage(), m.GetMissionLevel(pc, True), m.LevelAdjustment)`
  and compare with the reward card. A reward above the mission's logged level by exactly
  `LevelAdjustment` is the game's own offset, not a bug.
- Not covered in The Pre-Sequel by design: the Grinder (its output is levelled from the items
  fed in), SHiFT machine rewards and scripted weapon grants.
- Search the log for `Traceback` after the first map load: an `AttributeError` naming a field
  means that field is Borderlands 2 only and needs the same treatment as `OverpowerChoiceValue`.

## Things only the game can tell us (v2)

- Whether raid-boss dedicated drops (`Behavior_SpawnItems`) take the pawn's enemy level or its
  loot level: kill a boss with Minimum Enemy Level vanilla and Minimum Item Level = Player Level
  and compare the dedicated drop's level with the pool drops.
- Whether a mission turned in *below* its level (a low character, or a co-op client) still gets
  an item: reward pools have minimum-level gates (most gear pools open at 7, relics at 15), and
  the native roll may drop a gated pool rather than clamp. Turn in a gated mission at level 5
  with `Minimum Mission Level` set.
- Co-op (untested): `ServerGrantMissionRewards` is expected to run once per player on the host
  with that player's controller; since v0.7 every write goes to the one shared mission object,
  so the last write wins and a client's turn-in can leave the host's mission at the client's
  level. Note what the reward card shows for each player.
