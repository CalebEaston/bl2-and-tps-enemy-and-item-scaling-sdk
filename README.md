# Enemy and Item Scaling (BL2 & TPS)

> This mod was made with AI (Claude Code). The code and docs were written with it,
> under my direction.

An SDK mod for Borderlands 2 and Borderlands: The Pre-Sequel that scales enemies, loot and
missions to your level. The Pre-Sequel side should work (both games share the code the mod hooks
into) but hasn't been tested yet.

**[Download the latest release](https://github.com/CalebEaston/bl2-and-tps-enemy-and-item-scaling-sdk/releases/latest)**,
drop `enemy_item_scaling.sdkmod` into your `sdk_mods` folder, restart the game. First time using SDK
mods? See [Installation](#installation).

Outside of UVHM, both games give every area a fixed level range. Once you've out-levelled an
area, everything in it is stuck behind you: the enemies die in a shot or two and nothing they drop
is worth picking up. This mod puts a band around your level and keeps enemies, loot and the missions you have accepted inside it.
Go back to Knuckle Dragger at level 15 and he spawns at level 15, and so does the loot he drops.

Each side of the band is its own option. You can raise only the enemies that fall behind you,
raise only the loot or only your missions, cap anything that has run ahead of you, or leave any of them vanilla. The
enemy and item settings are independent, so you can keep vanilla enemy scaling and still get the
gear they drop on your level.

This is a new mod and I haven't been able to test everything, so if something looks off, leave a
comment or [open an issue](https://github.com/CalebEaston/bl2-and-tps-enemy-and-item-scaling-sdk/issues).
Even a one-liner about what you were doing helps. Pre-Sequel support is new in v0.6 and hasn't
been play-tested yet, so reports from there are especially welcome.

## Options

The five level bounds take `Vanilla` (off), `Player Level` (exactly your level), or `Within 1`
to `Within 10 Levels` (that many levels below you for a minimum, above you for a maximum):

- **Minimum Enemy Level** - enemies below this are raised to it
- **Maximum Enemy Level** - enemies above this are lowered to it
- **Minimum Item Level** - loot below this is raised to it (enemy drops, chests, slot machines,
  boss drops)
- **Maximum Item Level** - loot above this is lowered to it
- **Minimum Mission Level** - missions you have accepted that fall below this are raised to it
  and keep moving up with you as you level: the mission log shows the raised level, and the
  reward item, XP and cash come at that level when you turn them in. A mission is never
  lowered. Works with Reward Reroller: rerolls come out at that level too.

An enemy that gets raised or lowered drops loot at its new level, and the item settings apply on
top of that. In The Pre-Sequel the Grinder is left alone: its output takes its level from the
items you feed it.

One on/off switch:

- **On-Level Vendors** - vending machines below your level stock at your level, item of the day
  included. A machine above your level (a DLC area you are early for, say) keeps its own level:
  pulling it down can leave it with nothing to sell.

And **Log Adjustments** prints each change, each vending machine you open and each mission you
turn in to the console and to `<game>\Binaries\Win32\Plugins\unrealsdk.log`.

Everything starts off or on `Vanilla`. Each setting works on its own. In co-op only the
host's settings matter. Enemies already alive when you level up keep their level until they
respawn. A mission that was raised is saved with your character and keeps that level even if
you set the bound back to `Vanilla`. If turning a mission in is what levels you up, its reward
can be one level below your new level: it was rolled at the level you had when you handed it
in. Each game keeps its own copy of the settings.

## Installation

This is an SDK mod, not a BLCMM text mod, so it needs the PythonSDK installed once. The same SDK
and the same mod file work for Borderlands 2 and The Pre-Sequel; install them into whichever game
you want, or both. If you have never used SDK mods, follow all three parts in order.

### 1. Install the PythonSDK (once)

These steps are condensed from the official guide at https://bl-sdk.github.io/willow2-mod-db/ ,
which is the place to look if anything here is out of date.

1. Install the latest [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x86.exe)
   (x86, since both games are 32-bit).
2. Download `willow2-sdk.zip` from the latest release at
   https://github.com/bl-sdk/willow2-mod-manager/releases/latest . Do not download the
   "Source code" links.
3. Find your game folder. In Steam, right-click the game, then `Manage` > `Browse local files`.
   The Steam defaults are `C:\Program Files (x86)\Steam\steamapps\common\Borderlands 2` and
   `C:\Program Files (x86)\Steam\steamapps\common\BorderlandsPreSequel`; on Epic, Borderlands 2
   is at `C:\Program Files\Epic Games\Borderlands 2`.
4. Extract the zip directly into that game folder so its contents merge with what is there. Say yes
   to overwriting. You should now have `<game>\sdk_mods` and
   `<game>\Binaries\Win32\Plugins\unrealsdk.dll`.
5. **Linux / Steam Deck only:** in Steam, open the game's `Properties`, force a specific Proton
   version under `Compatibility` (recent Proton GE builds work best), then under `General` set the
   launch options to:
   ```
   WINEDLLOVERRIDES="ddraw=n,b" %command% -pf_tricks=vcrun2022
   ```
6. Start the game. A new `MODS` entry on the main menu means the SDK is installed.

### 2. Install this mod

1. Get `enemy_item_scaling.sdkmod` from this repository's
   [Releases](https://github.com/CalebEaston/bl2-and-tps-enemy-and-item-scaling-sdk/releases) page. To
   build it yourself instead, see
   [Building the .sdkmod by hand](docs/development.md#building-the-sdkmod-by-hand).
2. Drop the `.sdkmod` file straight into `<game>\sdk_mods`. (If you instead have the folder
   `enemy_item_scaling`, put that folder in `sdk_mods` so that
   `sdk_mods\enemy_item_scaling\__init__.py` exists; avoid ending up with the folder nested inside
   another copy of itself.)
3. Restart the game. Mods only load on startup.

### 3. Enable and configure

1. From the main menu open `MODS`, select `Enemy and Item Scaling`, and enable it. New mods start
   disabled.
2. Open its options and set the bounds you want. The settings are saved when you leave the options
   screen and persist between sessions.

### Requirements

- Borderlands 2 or Borderlands: The Pre-Sequel (the Windows builds; on Linux they run through
  Proton as above). All DLC is fine but not required.
- PythonSDK / Willow2 Mod Manager v3.8 or newer.
- Microsoft Visual C++ Redistributable (x86).
- No other mods are required.

### Troubleshooting

- **No `MODS` entry on the main menu:** check that `<game>\sdk_mods` exists (the zip was extracted
  one folder too deep or too shallow if not), then reinstall the Visual C++ Redistributable.
- **Game crashes on launch after installing the SDK:** install the latest Visual C++
  Redistributable. On Proton, `-pf_tricks=vcrun2022` in the launch options does this; failing that,
  run `protontricks 49520 vcrun2022` for Borderlands 2 or `protontricks 261640 vcrun2022` for
  The Pre-Sequel.
- **The mod isn't in the list:** make sure the file is `sdk_mods\enemy_item_scaling.sdkmod` or the
  folder is `sdk_mods\enemy_item_scaling\`, then restart the game. Errors while loading mods are
  written to `<game>\Binaries\Win32\Plugins\unrealsdk.log`.
- **Want to see it working:** turn on `Log Adjustments`, open the console (press the tilde key
  twice) and watch for `[Enemy and Item Scaling] spawn PawnBalance_...: 5 -> 15 (player 15)`
  lines as enemies spawn.
- **More help:** the SDK's [Modding Support Discord](https://discord.gg/bXeqV8Ef9R).

## For modders

The mod's source is `src/enemy_item_scaling/`. Notes on the SDK, the hooks used, prior art and
the dev loop are in [docs/](docs/), starting with [docs/development.md](docs/development.md).

## Credits

No code from other mods is included, but this one builds on what they figured out:

- [apple1417](https://github.com/apple1417) and the bl-sdk contributors, for the
  [PythonSDK](https://github.com/bl-sdk/willow2-mod-manager) this runs on, and apple1417's
  [Enemy Level Randomizer](https://github.com/apple1417/willow2-sdk-mods/tree/master/enemy_level_randomizer),
  [Borderlands Cheats](https://github.com/apple1417/willow2-sdk-mods/tree/master/apples_borderlands_cheats) and
  [Vendor Edit](https://github.com/apple1417/willow2-sdk-mods/tree/master/vendor_edit).
- galqawala's [EnemyBalancer](https://github.com/galqawala/EnemyBalancer), whose spawn hooks set
  enemy levels, a technique from RedxYeti's
  [Enemy Randomizer](https://github.com/RedxYeti/Yeti-BL1-SDK-Mods/tree/main/EnemyRandomizer).
- EdricY's [Bouncy Loot God](https://github.com/EdricY/Bouncy-Loot-God) for the loot and chest
  hooks, and [Adaptor-Face](https://github.com/Adaptor-Face) for finding the Pre-Sequel intro
  chest that spawns empty when lowered.
- mopioid's [Loot Randomizer](https://github.com/mopioid/Borderlands-Loot-Randomizer), juso40's
  [MapLoader and RogueLands](https://github.com/juso40/bl2sdk_Mods), and RedxYeti's
  [Pay To Loot, Random Skill Selector](https://github.com/RedxYeti/bl2-willow2-sdkmods) and
  [Ultimate Scavenger](https://github.com/RedxYeti/Yeti-BL2-SDK-Mods/tree/main/UltimateScavengerMod),
  for how missions, rewards and level-ups work.
- The research notes in ZooLSmith's [Helios Tracker](https://github.com/ZooLSmith/helios-tracker)
  and in [BL2_ReBased](https://github.com/zuhuHix/BL2_ReBased), by zuhuHix and the OpenWillow
  contributors.
- Works alongside ZetaDaemon's
  [Reward Reroller](https://github.com/ZetaDaemon/bl-sdk-mods/tree/main/RewardReroller).

## Changelog

See [src/enemy_item_scaling/Readme.md](src/enemy_item_scaling/Readme.md).
