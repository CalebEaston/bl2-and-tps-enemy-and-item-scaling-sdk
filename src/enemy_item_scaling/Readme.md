## Changelog

### Enemy and Item Scaling v0.3
- `On-Level Mission Rewards` now also works with mods that roll mission rewards themselves, such
  as Reward Reroller: an accepted mission reports your level to them, so rolls and rerolls come
  out on level.

### Enemy and Item Scaling v0.2
- Added `On-Level Mission Rewards`: mission reward items, and the XP and cash with them, are
  generated at your level.
- Added `On-Level Vendors`: vending machines stock at your level when they spawn and when they
  restock. Vendors are no longer touched by the item bounds.

### Enemy and Item Scaling v0.1
- Initial skeleton: four level bounds (minimum/maximum enemy level, minimum/maximum item level),
  each either vanilla or within 0-10 levels of the player, plus a console logging toggle.
