# Playtest checklist

Plain steps, nothing to type into the console. Every setting is under the main menu's `MODS`
entry, `Enemy and Item Scaling` (enable the mod there first). Turn on `Log Adjustments` for all
of it: the mod then writes one line to `<game>\Binaries\Win32\Plugins\unrealsdk.log` for every
level it changes (`<game>` is the folder that contains `sdk_mods`). The file is emptied each
time the game starts, so copy lines out before relaunching. Searching it for
`Enemy and Item Scaling` finds every line of ours. The developer version with console probes is
[testing-probes.md](testing-probes.md).

Each section stands on its own; do them in any order, across as many sessions as you like. If
you only have time for a few, sections 1, 2 and 7 matter most.

A log line looks like `[Enemy and Item Scaling] spawn PawnBalance_Marauder: 3 -> 15 (player 15)`:
what was changed, the game's internal name for it, the level the game wanted, the level it
got, and your level. The `(player 15)` tail is left off the examples below; `mission` and
`vendor restock` lines never have one. The word after the prefix:

- `spawn`: an enemy, as the game built it
- `enemy` / `enemy level`: an enemy that came in by an unusual path (rare; fine as long as the
  nameplate shows the level the line says it was raised to)
- `loot`: an enemy's drops
- `container`: a chest, slot machine or similar
- `vendor` / `vendor restock`: a vending machine
- `mission`: an accepted mission
- `reward item ... (please report this)`: the one line that should never appear

## 1. Enemies

Settings: `Minimum Enemy Level = Player Level`, the other four bounds `Vanilla`,
`On-Level Vendors` off. Go somewhere well below your level (Southern Shelf at level 15 or more).

- Nameplates show your level and enemies take real effort to kill.
- The log has one `spawn ...: 3 -> 15` line per enemy.
- If an enemy still shows its old level: note what it was (bandit, bullymong, its nameplate)
  and the level it showed, and send every `spawn`, `enemy` and `enemy level` line from that
  visit. The names in the log are internal; I will match them up.
- If an enemy type stops appearing at all (an empty camp that is full again after you set the
  bound back to `Vanilla` and save-quit-continue): note the enemy type and your level.

## 2. Loot

Settings: `Minimum Item Level = Player Level`, the other four bounds `Vanilla`. Same area.

- Enemies keep their old level, but what they drop is at your level, give or take a level (the
  game adds its own small variance). Chests too.
- The log has a `loot ...: 3 -> 15` line per enemy and a `container ...` line per chest.
- If the gun an enemy was holding is on level but the rest of its drops are not: say so.

## 3. Ceiling

Settings: `Maximum Enemy Level = Player Level`, the other four bounds `Vanilla`. A low character
(around level 5) somewhere above you (Three Horns Divide). Enemies come down to your level; the
log shows `spawn ...: 9 -> 5`.

## 4. Within N

Settings: `Minimum Enemy Level = Within 3 Levels`, the other four bounds `Vanilla`, at level 15
in Southern Shelf: nameplates show 12 and the `spawn` lines read `3 -> 12 (player 15)`.

## 5. Vanilla

All five bounds on `Vanilla` and `On-Level Vendors` off: searching the log for
`Enemy and Item Scaling` finds nothing, on any map.

## 6. Vendors

Settings: `On-Level Vendors` on, all five bounds `Vanilla`. A high character in an early area.

- When the map loads, the log gets a `vendor WillowVendingMachine_N: 3 -> 15` line per machine.
- Open a weapon vendor: the stock is around your level (the game rolls up to two below), the
  item of the day exactly your level.
- Gain a level somewhere, then come back to a machine after it has restocked (about twenty
  minutes after the map loaded): the stock is at your new level and the log has a
  `vendor restock WillowVendingMachine_N: 15 -> 16` line. If you did not level up there is no
  line and nothing to check, so skip this rather than wait.
- Turn `On-Level Vendors` off, set `Minimum Item Level = Player Level`, then save-quit and
  continue (the machine keeps its level until the map reloads): the vendor is back at the
  area's level and there is no `vendor` or `container` line for it.
- If there is no `vendor` line at map load but the stock is right anyway: say so.

## 7. Missions

Settings: `Minimum Mission Level = Player Level`, the other four bounds `Vanilla`. A character a
few levels above a side mission you have not accepted yet. "Journal" below means the game's
own mission list; "log" means `unrealsdk.log`.

- Accept it: the journal shows it at your level straight away, and the log gets a
  `mission M_...: 5 -> 15` line (for example `mission M_ThisTown: 5 -> 15` for This Town Ain't
  Big Enough; the name is the game's internal one, not the title you see). If the journal still
  shows the old level: say so, with the mission's title, the level the journal shows, and every
  `mission` line from that session.
- On a character that is ahead of the story, take a main-story mission that is handed to you by
  ECHO or a cutscene rather than by a person: the journal shows it at your level and the log
  gets the same `mission` line.
- Level up while missions are open: they move with you, one `mission` line each.
- Save, quit, continue: the journal still shows the raised level and the load prints no new
  `mission` line for that mission. (A `mission` line on every load means the game put the old
  level back on load and the mod raised it again. It still works; tell me anyway.)
- Turn it in: the reward card shows gear at your level. (XP and cash follow the level too, but
  there is nothing to compare them against; if the gear is wrong, note the XP number as well.)
- If the turn-in itself levels you up, the reward may be one level below your new level. That
  is the game's order of events, not a bug. With Reward Reroller it comes out at the new level.
- If you hold a mission above your level (a DLC mission taken early, say): it keeps its level
  and gets no `mission` line until you out-level it. If it drops to your level, send the line.
- Set the bound back to `Vanilla`: missions already raised keep their level (it is in the
  save); new ones stay vanilla.
- Any `reward item ... (please report this)` line in the log: send it.

## 8. The Pre-Sequel

Same mod file, same SDK zip, installed into the Pre-Sequel folder. Nothing here has been played
yet.

- Main menu `MODS`: the mod must be enableable, not shown as yellow `Incompatible`.
- Run sections 1 and 2 in Regolith Range or Serenity's Waste, and section 7 with a side mission
  picked up in Concordia.
- Claptastic Voyage with `Minimum Enemy Level = Player Level`: the `.exe` enemies may log as
  `enemy` / `enemy level` instead of `spawn`. Fine, as long as the nameplates show your level.
- A new character with `Maximum Item Level = Player Level`: every chest in the intro still
  spawns loot. If one is empty, say which, and send any `container` lines from the intro.
- Concordia with `On-Level Vendors` on: the SHiFT machine may get a
  `vendor WillowVendingMachineShift_N` line at map load, or only a
  `vendor restock WillowVendingMachineShift_N` line when it resets; either is fine, say which
  you saw (its gamble stock following your level would be a bonus, not a promise).
- Playing Wilhelm with `Minimum Item Level = Player Level` and
  `Maximum Item Level = Player Level`: no `container OzSupportDrone...` lines while Wolf and
  Saint are out. If you see them, send them.
- Any block containing `Traceback` or `AttributeError` after the first map load: send the whole
  block.

## What to send

The log lines mentioned above, your level, the area, which game (Borderlands 2 or The
Pre-Sequel), the mod version shown in the `MODS` menu, and which options were set. One line
about what you were doing is enough. Post it at
https://github.com/CalebEaston/bl2-and-tps-enemy-and-item-scaling-sdk/issues or wherever you
got the mod.
