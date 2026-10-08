## Changelog

### Enemy and Item Scaling v0.4
- `On-Level Mission Rewards` now levels the mission as soon as its reward card is shown, and
  keeps it there until you take the reward. That makes it work with Reward Reroller (its rolls
  and rerolls come out on level); the v0.3 attempt did not reach legacy mods.

### Enemy and Item Scaling v0.3
- Attempted Reward Reroller support (did not work; superseded by v0.4).

### Enemy and Item Scaling v0.2
- Added `On-Level Mission Rewards`: mission reward items, and the XP and cash with them, are
  generated at your level.
- Added `On-Level Vendors`: vending machines stock at your level when they spawn and when they
  restock. Vendors are no longer touched by the item bounds.

### Enemy and Item Scaling v0.1
- Initial skeleton: four level bounds (minimum/maximum enemy level, minimum/maximum item level),
  each either vanilla or within 0-10 levels of the player, plus a console logging toggle.
