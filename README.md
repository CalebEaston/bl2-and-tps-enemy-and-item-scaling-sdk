# Enemy and Item Scaling

> This mod was made with the help of AI (Claude Code). The code and docs were written with it,
> under my direction.

A Borderlands 2 SDK mod that scales enemies and loot to your level.

**[Download the latest release](https://github.com/CalebEaston/bl2-enemy-and-item-scaling-sdk/releases/latest)**,
drop `enemy_item_scaling.sdkmod` into your `sdk_mods` folder, restart the game. First time using SDK
mods? See [Installation](#installation).

Outside of UVHM, Borderlands 2 gives every area a fixed level range. Once you've out-levelled an
area, everything in it is stuck behind you: the enemies die in a shot or two and nothing they drop
is worth picking up. This mod puts a band around your level and keeps enemies and loot inside it.
Go back to Knuckle Dragger at level 15 and he spawns at level 15, and so does the gun he drops.

Each side of the band is its own option. You can raise only the enemies that fall behind you,
raise only the loot, cap anything that has run ahead of you, or leave any of them vanilla. The
enemy and item settings are independent, so you can keep vanilla enemy scaling and still get gear
at your level instead of farming for it.

## Options

All four take `Vanilla`, `Player Level`, or `Within 1` to `Within 10 Levels`:

- **Minimum Enemy Level** - enemies below this are raised to it
- **Maximum Enemy Level** - enemies above this are lowered to it
- **Minimum Item Level** - loot below this is raised to it
- **Maximum Item Level** - loot above this is lowered to it
- **Log Adjustments** - prints each change to the console

Everything starts on `Vanilla`. Enemy and item settings don't affect each other. In co-op only the
host's settings matter.

Not covered yet: vendors, mission rewards, and enemies already alive when you level up.

## Installation

This is an SDK mod, not a BLCMM text mod, so it needs the PythonSDK installed once. If you have
never used SDK mods, follow all three parts in order.

### 1. Install the PythonSDK (once)

These steps are condensed from the official guide at https://bl-sdk.github.io/willow2-mod-db/ ,
which is the place to look if anything here is out of date.

1. Install the latest [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x86.exe)
   (x86, since Borderlands 2 is a 32-bit game).
2. Download `willow2-sdk.zip` from the latest release at
   https://github.com/bl-sdk/willow2-mod-manager/releases/latest . Do not download the
   "Source code" links.
3. Find your game folder. In Steam, right-click Borderlands 2, then `Manage` > `Browse local files`.
   The defaults are `C:\Program Files (x86)\Steam\steamapps\common\Borderlands 2` for Steam and
   `C:\Program Files\Epic Games\Borderlands 2` for Epic.
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
   [Releases](https://github.com/CalebEaston/bl2-enemy-and-item-scaling-sdk/releases) page. If
   there is no release yet, see "Building from source" below.
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

- Borderlands 2 (the Windows build; on Linux it runs through Proton as above). All DLC is fine but
  not required.
- PythonSDK / Willow2 Mod Manager v3.8 or newer.
- Microsoft Visual C++ Redistributable (x86).
- No other mods are required.

### Troubleshooting

- **No `MODS` entry on the main menu:** check that `<game>\sdk_mods` exists (the zip was extracted
  one folder too deep or too shallow if not), then reinstall the Visual C++ Redistributable.
- **Game crashes on launch after installing the SDK:** install the latest Visual C++
  Redistributable. On Proton, `-pf_tricks=vcrun2022` in the launch options does this; failing that,
  run `protontricks 49520 vcrun2022`.
- **The mod isn't in the list:** make sure the file is `sdk_mods\enemy_item_scaling.sdkmod` or the
  folder is `sdk_mods\enemy_item_scaling\`, then restart the game. Errors while loading mods are
  written to `<game>\Binaries\Win32\Plugins\unrealsdk.log`.
- **Want to see it working:** turn on `Log Adjustments`, open the console (press the tilde key
  twice) and watch for `[Enemy and Item Scaling] enemy ...: 5 -> 15 (player 15)` lines as enemies
  spawn.
- **More help:** the SDK's [Modding Support Discord](https://discord.gg/bXeqV8Ef9R).

## For modders

The mod's source is `src/enemy_item_scaling/`. Notes on the SDK, the hooks used, prior art and
the dev loop are in [docs/](docs/), starting with [docs/development.md](docs/development.md).

## Changelog

See [src/enemy_item_scaling/Readme.md](src/enemy_item_scaling/Readme.md).
