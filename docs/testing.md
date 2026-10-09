# In-game test plan

This is the order to check things in, and what each check settles. Turn on `Log Adjustments` for
all of it. Log lines look like `[Enemy and Item Scaling] spawn PawnBalance_Marauder: 3 -> 15
(player 15)` with the kind being `spawn` (the factory hook), `enemy` / `enemy level` (the two
safety nets; silent when the factory hook already did the work), `loot`, `container` or
`vendor`, and only appear when a level actually changed. The lines `vendor restock X: a -> b`,
`mission reward M: a -> b (player's copy c)` and `reward item M: a -> b` have no `(player N)`
suffix.

First playtest (2026-10-08, v0.2-v0.4, Southern Shelf, player 4 then 6): enemies kept their
nameplate level while their drops scaled (fixed in v0.5 by hooking the population factory, see
scenario 1), and "This Town Ain't Big Enough" gave a level-3 reward at player level 6 with the
mission toggle believed on (v0.5 adds the player's-copy write and the accept-time safety net;
whether the toggle was on and what the log said is still to be confirmed).

## 0. Console probes (before trusting anything)

Open the console (tilde twice) after enabling the mod from the `MODS` menu.

Mod registered and hooks live (expect `True [1, 2, 1]`):

```
py import enemy_item_scaling as m; print(m.mod.is_enabled, [h.get_active_count() for h in m.mod.hooks])
```

Player-level fields resolve (all three must print; repeat in Normal mode with an OP-unlocked
character and check that `OverpowerChoiceValue` is what you expect there):

```
py from mods_base import get_pc; pc = get_pc(); print(pc.PlayerReplicationInfo.ExpLevel, pc.OverpowerChoiceValue, pc.GetCurrentPlaythrough())
```

Every hook target exists and has the parameter name the code reads (a `ValueError` names a missing
function; it's fine if exactly one of the two `SetGameStageForSpawnedInventory` paths is missing):

```
py import unrealsdk; print([(f, [p.Name for p in unrealsdk.find_object('Function', f)._properties()]) for f in ('WillowGame.PopulationFactoryBalancedAIPawn:CreatePopulationActor', 'WillowGame.PopulationFactoryBalancedAIPawn:RestorePopulatedAIPawn', 'WillowGame.WillowPawn:SetGameStage', 'WillowGame.WillowAIPawn:SetExpLevel', 'WillowGame.WillowPawn:SetGameStageForSpawnedInventory', 'WillowGame.WillowAIPawn:SetGameStageForSpawnedInventory', 'WillowGame.WillowInteractiveObject:SetGameStage', 'WillowGame.WillowPlayerController:ReceiveWeaponReward', 'WillowGame.WillowPlayerController:ReceiveItemReward')])
```

Expect `GameStage` among the factory functions' params, `NewGameStage` for the `SetGameStage`
functions, `NewExpLevel` for `SetExpLevel`, `NewInventoryGameStage` for the inventory ones and
`Mission`, `DefinitionData` for the reward ones.

## 1. Enemy floor

Level 15+ character, Normal mode. `Minimum Enemy Level = Player Level`, the other three `Vanilla`.
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

All four spinners on `Vanilla`: no log lines at all, on any map.

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

## 7. Mission rewards (v2)

`On-Level Mission Rewards` on, level 15+ character, a cheap leftover level-5 side mission (e.g. in
Southern Shelf). Before turning in, probe that the hook target exists and the fields are there:

```
py import unrealsdk; print([p.Name for p in unrealsdk.find_object('Function', 'WillowGame.WillowPlayerController:ServerGrantMissionRewards')._properties()])
```

Expect `Mission` and `bGrantAltReward`. Open the NPC's mission list: expect one
`mission reward <Mission_...>: 5 -> 15` line. Turn the mission in: probably a second
`mission reward ...: 5 -> 15 (player's copy 5)` line from the grant hook (if the Complete status
restores the stage just before it; otherwise the grant hook logs nothing), the reward card
showing level 15 gear, and the XP reward noticeably larger than the mission log said. If a `reward item <Mission_...>: 5 -> 15 (the roll
ignored the mission's level; please report this)` warning appears when the item is taken, the
roll ignored both stage writes and only the accept-time safety net saved it: the item is level
15 but the card showed 5. Then the roll's input is something else again
(`MissionDefinition.ExpLevel`? the `UnclaimedRewards` path?) and the display-time rewrite of
`MissionRewardGFxObject:SetUpRewardsPage` (`obj.RewardData`) is the next thing to try. A
`reward item ...: 15 -> 16 (player 16)` info line is normal: the mission's XP levelled you up
between the roll and the accept. A `could not write the player's copy` warning means the nested
struct write did not take; see `docs/sdk-notes.md`.

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

## Things only the game can tell us (v2)

- Whether raid-boss dedicated drops (`Behavior_SpawnItems`) take the pawn's enemy level or its
  loot level: kill a boss with Minimum Enemy Level vanilla and Minimum Item Level = Player Level
  and compare the dedicated drop's level with the pool drops.
- Whether a mission turned in *below* its level (a low character, or a co-op client) still gets
  an item: reward pools have minimum-level gates (most gear pools open at 7, relics at 15), and
  the native roll may drop a gated pool rather than clamp. Turn in a gated mission at level 5
  with the toggle on.
- Co-op: whether `ServerGrantMissionRewards` runs once per player on the host with that player's
  controller (expected, untested), so each player gets rewards at their own level.
