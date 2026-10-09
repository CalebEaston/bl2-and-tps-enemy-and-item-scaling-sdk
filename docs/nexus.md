# Nexus Mods listing

Nexus can't be filled in automatically, so this is everything to paste into
https://www.nexusmods.com/borderlands2/mods/add . Attach `enemy_item_scaling.sdkmod` from the
GitHub release as the main file. For a Pre-Sequel listing the same text goes on The
Pre-Sequel's own Nexus page, https://www.nexusmods.com/borderlandsthepresequel/mods/add .

## Fields

- **Name:** Enemy and Item Scaling (BL2 & TPS)
- **Summary (one line):** Scales enemies, loot, vendors and missions to your level in BL2 and
  TPS (TPS untested), each one optional. Come back to an old area at level 15 and it's a level
  15 area.
- **Category:** Gameplay (Nexus calls it "Gameplay Effects and Changes" on some games)
- **Version:** match the release tag without the `v`, e.g. `0.8`
- **Language:** English
- **Requirements:** add `PythonSDK (willow2-mod-manager)` with the link
  https://github.com/bl-sdk/willow2-mod-manager/releases/latest
- **Permissions:** your call. The source is public on GitHub, so "open source, credit
  appreciated" fits.
- **Tags:** Gameplay, Loot, Levelling, Quality of Life
- **Source:** https://github.com/CalebEaston/bl2-and-tps-enemy-and-item-scaling-sdk

## Description (BBCode)

Nexus descriptions are BBCode. Paste this as-is:

```
[size=5][b]Enemy and Item Scaling (BL2 & TPS)[/b][/size]

A PythonSDK mod for Borderlands 2 and Borderlands: The Pre-Sequel that scales enemies, loot and missions to your level. The Pre-Sequel side should work (both games share the code the mod hooks into) but hasn't been tested yet.

Outside of UVHM, both games give every area a fixed level range. Once you've out-levelled an area, everything in it is stuck behind you: the enemies die in a shot or two and nothing they drop is worth picking up. This mod puts a band around your level and keeps enemies, loot and the missions you have accepted inside it. Go back to Knuckle Dragger at level 15 and he spawns at level 15, and so does the loot he drops.

Each side of the band is its own option. You can raise only the enemies that fall behind you, raise only the loot or only your missions, cap anything that has run ahead of you, or leave any of them vanilla. The enemy and item settings are independent, so you can keep vanilla enemy scaling and still get the gear they drop on your level.

[size=4][b]Options[/b][/size]

The five level bounds take [b]Vanilla[/b], [b]Player Level[/b], or [b]Within 1[/b] to [b]Within 10 Levels[/b]:

[list]
[*][b]Minimum Enemy Level[/b] - enemies below this are raised to it
[*][b]Maximum Enemy Level[/b] - enemies above this are lowered to it
[*][b]Minimum Item Level[/b] - loot below this is raised to it (enemy drops, chests, slot machines, boss drops)
[*][b]Maximum Item Level[/b] - loot above this is lowered to it
[*][b]Minimum Mission Level[/b] - missions you have accepted that fall below this are raised to it and keep following you as you level up (never lowered), so the reward item, XP and cash come at that level when you turn them in
[/list]

One on/off switch:

[list]
[*][b]On-Level Vendors[/b] - vending machines stock at your level, item of the day included
[/list]

Everything starts off or on Vanilla, so the mod does nothing until you pick something. In co-op only the host's settings matter. Enemies already alive when you level up keep their level until they respawn. A mission that was raised is saved with your character and keeps that level even if you set the bound back to Vanilla.

[size=4][b]Installation[/b][/size]

This is an SDK mod, not a BLCMM text mod. If you've never used one:

[list=1]
[*]Install the PythonSDK: follow [url=https://bl-sdk.github.io/willow2-mod-db/]the official guide[/url] (install the Visual C++ Redistributable, extract the SDK zip into your game folder, and on Linux/Steam Deck add the launch options it lists). You're done when a [b]MODS[/b] entry appears on the main menu.
[*]Drop [b]enemy_item_scaling.sdkmod[/b] into your [b]sdk_mods[/b] folder.
[*]Restart the game, open [b]MODS[/b], enable Enemy and Item Scaling, and set the options you want.
[/list]

A step-by-step version with troubleshooting is in the [url=https://github.com/CalebEaston/bl2-and-tps-enemy-and-item-scaling-sdk#installation]README on GitHub[/url].

[size=4][b]Credits[/b][/size]

No code from other mods is included, but this one builds on what they figured out:

[list]
[*]apple1417 and the bl-sdk contributors, for the [url=https://github.com/bl-sdk/willow2-mod-manager]PythonSDK[/url] this runs on, and apple1417's [url=https://github.com/apple1417/willow2-sdk-mods/tree/master/enemy_level_randomizer]Enemy Level Randomizer[/url], [url=https://github.com/apple1417/willow2-sdk-mods/tree/master/apples_borderlands_cheats]Borderlands Cheats[/url] and [url=https://github.com/apple1417/willow2-sdk-mods/tree/master/vendor_edit]Vendor Edit[/url].
[*]galqawala's [url=https://github.com/galqawala/EnemyBalancer]EnemyBalancer[/url], whose spawn hooks set enemy levels, a technique from RedxYeti's [url=https://github.com/RedxYeti/Yeti-BL1-SDK-Mods/tree/main/EnemyRandomizer]Enemy Randomizer[/url].
[*]EdricY's [url=https://github.com/EdricY/Bouncy-Loot-God]Bouncy Loot God[/url] for the loot and chest hooks, and [url=https://github.com/Adaptor-Face]Adaptor-Face[/url] for finding the Pre-Sequel intro chest that spawns empty when lowered.
[*]mopioid's [url=https://github.com/mopioid/Borderlands-Loot-Randomizer]Loot Randomizer[/url], juso40's [url=https://github.com/juso40/bl2sdk_Mods]MapLoader and RogueLands[/url], and RedxYeti's [url=https://github.com/RedxYeti/bl2-willow2-sdkmods]Pay To Loot, Random Skill Selector[/url] and [url=https://github.com/RedxYeti/Yeti-BL2-SDK-Mods/tree/main/UltimateScavengerMod]Ultimate Scavenger[/url], for how missions, rewards and level-ups work.
[*]The research notes in ZooLSmith's [url=https://github.com/ZooLSmith/helios-tracker]Helios Tracker[/url] and in [url=https://github.com/zuhuHix/BL2_ReBased]BL2_ReBased[/url], by zuhuHix and the OpenWillow contributors.
[*]Works alongside ZetaDaemon's [url=https://github.com/ZetaDaemon/bl-sdk-mods/tree/main/RewardReroller]Reward Reroller[/url].
[/list]

[size=4][b]Notes[/b][/size]

[list]
[*]Source code and issue tracker: [url=https://github.com/CalebEaston/bl2-and-tps-enemy-and-item-scaling-sdk]GitHub[/url]
[*]This mod was made with AI (Claude Code). The code and docs were written with it, under my direction.
[*]New mod, not everything is tested yet. If something looks off, leave a comment here or open an issue on GitHub. Even a one-liner about what you were doing helps. Pre-Sequel support is new in v0.6 and hasn't been play-tested yet, so reports from there are especially welcome.
[/list]
```

## Before posting

- Cut a release first so the download exists (`docs/development.md`, "Cutting a release").
- Take two or three screenshots: the options menu, an enemy nameplate in an early area at your
  level, and a reward card or vendor at your level. Nexus listings without images get skipped.
- Nexus has its own changelog tab; paste the entries from `src/enemy_item_scaling/Readme.md`.
