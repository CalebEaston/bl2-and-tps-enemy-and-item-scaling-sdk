# Nexus Mods listing

Nexus can't be filled in automatically, so this is everything to paste into
https://www.nexusmods.com/borderlands2/mods/add . Attach `enemy_item_scaling.sdkmod` from the
GitHub release as the main file.

## Fields

- **Name:** Enemy and Item Scaling
- **Summary (one line):** Scales enemies, loot, vendors and mission rewards to your level, each
  one optional. Come back to an old area at level 15 and it's a level 15 area.
- **Category:** Gameplay (Nexus calls it "Gameplay Effects and Changes" on some games)
- **Version:** match the release tag, e.g. `0.2`
- **Language:** English
- **Requirements:** add `PythonSDK (willow2-mod-manager)` with the link
  https://github.com/bl-sdk/willow2-mod-manager/releases/latest
- **Permissions:** your call. The source is public on GitHub, so "open source, credit
  appreciated" fits.
- **Tags:** Gameplay, Loot, Levelling, Quality of Life
- **Source:** https://github.com/CalebEaston/bl2-enemy-and-item-scaling-sdk

## Description (BBCode)

Nexus descriptions are BBCode. Paste this as-is:

```
[size=5][b]Enemy and Item Scaling[/b][/size]

A PythonSDK mod that scales enemies and loot to your level.

Outside of UVHM, Borderlands 2 gives every area a fixed level range. Once you've out-levelled an area, everything in it is stuck behind you: the enemies die in a shot or two and nothing they drop is worth picking up. This mod puts a band around your level and keeps enemies and loot inside it. Go back to Knuckle Dragger at level 15 and he spawns at level 15, and so does the loot he drops.

Each side of the band is its own option. You can raise only the enemies that fall behind you, raise only the loot, cap anything that has run ahead of you, or leave any of them vanilla. The enemy and item settings are independent, so you can keep vanilla enemy scaling and still get the gear they drop on your level.

[size=4][b]Options[/b][/size]

The four level bounds take [b]Vanilla[/b], [b]Player Level[/b], or [b]Within 1[/b] to [b]Within 10 Levels[/b]:

[list]
[*][b]Minimum Enemy Level[/b] - enemies below this are raised to it
[*][b]Maximum Enemy Level[/b] - enemies above this are lowered to it
[*][b]Minimum Item Level[/b] - loot below this is raised to it (enemy drops, chests, slot machines, boss drops)
[*][b]Maximum Item Level[/b] - loot above this is lowered to it
[/list]

Two on/off switches:

[list]
[*][b]On-Level Mission Rewards[/b] - mission reward items come out at your level (the XP and cash scale with them)
[*][b]On-Level Vendors[/b] - vending machines stock at your level, item of the day included
[/list]

Everything starts off or on Vanilla, so the mod does nothing until you pick something. In co-op only the host's settings matter. Enemies already alive when you level up keep their level until they respawn.

[size=4][b]Installation[/b][/size]

This is an SDK mod, not a BLCMM text mod. If you've never used one:

[list=1]
[*]Install the PythonSDK: follow [url=https://bl-sdk.github.io/willow2-mod-db/]the official guide[/url] (install the Visual C++ Redistributable, extract the SDK zip into your game folder, and on Linux/Steam Deck add the launch options it lists). You're done when a [b]MODS[/b] entry appears on the main menu.
[*]Drop [b]enemy_item_scaling.sdkmod[/b] into your [b]sdk_mods[/b] folder.
[*]Restart the game, open [b]MODS[/b], enable Enemy and Item Scaling, and set the options you want.
[/list]

A step-by-step version with troubleshooting is in the [url=https://github.com/CalebEaston/bl2-enemy-and-item-scaling-sdk#installation]README on GitHub[/url].

[size=4][b]Notes[/b][/size]

[list]
[*]Source code and issue tracker: [url=https://github.com/CalebEaston/bl2-enemy-and-item-scaling-sdk]GitHub[/url]
[*]This mod was made with the help of AI (Claude Code), under my direction.
[*]New mod, not everything is tested yet. If something looks off, leave a comment here or open an issue on GitHub. Even a one-liner about what you were doing helps.
[/list]
```

## Before posting

- Cut a release first so the download exists (`docs/development.md`, "Cutting a release").
- Take two or three screenshots: the options menu, an enemy nameplate in an early area at your
  level, and a reward card or vendor at your level. Nexus listings without images get skipped.
- Nexus has its own changelog tab; paste the entries from `src/enemy_item_scaling/Readme.md`.
