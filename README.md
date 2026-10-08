# Enemy and Item Scaling

A Borderlands 2 PythonSDK mod that keeps enemies and loot within a band around your level, so the
areas you come back to stay worth fighting through and the gear that drops there stays worth
picking up.

Beat Knuckle Dragger at level 3, come back at level 15, and he spawns at 15 and drops level 15
loot. Each bound is its own setting, so you can raise only the enemies that fall behind, raise only
the loot, cap anything that runs ahead of you, or leave any of them vanilla. If you like vanilla
enemy scaling but are tired of farming for on-level gear, set only the item floor.

Only the host's settings matter in co-op: levels are decided on the host, so clients don't need the
mod installed.

## Configuration

Every option is a spinner with the same choices: `Vanilla`, `Player Level`, `Within 1 Level` up to
`Within 10 Levels`. "Player" means your character level plus any Overpower level you have selected.

| Option | Vanilla | Player Level | Within N Levels |
|---|---|---|---|
| **Minimum Enemy Level** | no floor | enemies below you are raised to your level | raised to at least `player - N` |
| **Maximum Enemy Level** | no cap | enemies above you are lowered to your level | lowered to at most `player + N` |
| **Minimum Item Level** | no floor | loot below you is raised to your level | raised to at least `player - N` |
| **Maximum Item Level** | no cap | loot above you is lowered to your level | lowered to at most `player + N` |
| **Log Adjustments** | | | prints every level change to the console, for testing |

Everything defaults to `Vanilla`, so the mod does nothing until you pick a bound.

Some combinations:

- **Everything matches me:** Minimum Enemy Level and Minimum Item Level to `Player Level`.
- **Vanilla enemies, on-level loot:** only Minimum Item Level to `Player Level`.
- **Pinned to a band:** all four to `Within 3 Levels`, and nothing spawns outside `player ± 3`.

Enemy and item bounds are independent. Raising an enemy doesn't by itself raise its loot and vice
versa, so set both if you want both.

## How it works

The mod hooks the game functions that assign a level to each enemy, to the loot an enemy will drop,
and to chests and other containers, at the moment they spawn. It reads the level the game chose,
and only when that level falls outside your band does it replace the call with the clamped level.
Inside the band, the game runs untouched. Nothing is written to game data or save files, so
disabling the mod restores vanilla behaviour immediately.

Things it does not cover yet: vending machine stock, mission rewards, and enemies that are already
alive when you level up (they keep their level until they respawn).

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

## Building from source

A `.sdkmod` is just a zip whose only top-level folder is the mod folder:

```sh
cd src
zip -r ../enemy_item_scaling.sdkmod enemy_item_scaling -x '*__pycache__*'
```

Or skip packaging and copy `src/enemy_item_scaling` into `sdk_mods` directly. Development notes
(type-checking against the SDK, pointing the game at this checkout, hot-reloading) are in
[CLAUDE.md](CLAUDE.md) and [docs/sdk-notes.md](docs/sdk-notes.md).

## Changelog

See [src/enemy_item_scaling/Readme.md](src/enemy_item_scaling/Readme.md).
