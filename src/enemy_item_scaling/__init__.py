from functools import cache
from typing import TYPE_CHECKING, Any

import unrealsdk
from mods_base import BoolOption, SpinnerOption, build_mod, get_pc, hook
from unrealsdk import logging
from unrealsdk.hooks import Block, prevent_hooking_direct_calls

if TYPE_CHECKING:
    from unrealsdk.unreal import BoundFunction, UClass, UObject, WrappedStruct

# Injected by build_mod() from pyproject.toml
__version__: str
__version_info__: tuple[int, ...]

VANILLA = "Vanilla"

# Spinner label -> how far from the player's level the bound sits. None means the bound is off.
LEVEL_CHOICES: dict[str, int | None] = {
    VANILLA: None,
    "Player Level": 0,
    "Within 1 Level": 1,
    **{f"Within {n} Levels": n for n in range(2, 11)},
}


def _level_spinner(identifier: str, description: str) -> SpinnerOption:
    return SpinnerOption(identifier, VANILLA, list(LEVEL_CHOICES), description=description)


min_enemy_level = _level_spinner(
    "Minimum Enemy Level",
    "Enemies that would spawn below this are raised to it.\n"
    "'Player Level' makes every under-levelled enemy match you exactly.",
)
max_enemy_level = _level_spinner(
    "Maximum Enemy Level",
    "Enemies that would spawn above this are lowered to it.",
)
min_item_level = _level_spinner(
    "Minimum Item Level",
    "Loot that would drop below this is raised to it. Independent of the enemy settings,"
    " so you can keep vanilla enemies and still get on-level gear.",
)
max_item_level = _level_spinner(
    "Maximum Item Level",
    "Loot that would drop above this is lowered to it.",
)
log_adjustments = BoolOption(
    "Log Adjustments",
    False,
    description="Print every level change to the console. Useful when testing.",
)


def clamp_level(
    level: int,
    player_level: int,
    floor_offset: int | None,
    ceiling_offset: int | None,
) -> int:
    """
    Clamps a level into the band [player - floor_offset, player + ceiling_offset].

    Args:
        level: The level the game chose.
        player_level: The player's effective level.
        floor_offset: How far below the player the floor sits, or None for no floor.
        ceiling_offset: How far above the player the ceiling sits, or None for no ceiling.
    Returns:
        The clamped level. Equal to the input whenever it was already inside the band.
    """
    if floor_offset is not None:
        level = max(level, player_level - floor_offset)
    if ceiling_offset is not None:
        level = min(level, player_level + ceiling_offset)
    return level


def get_player_level() -> int:
    """
    Gets the local player's effective level: their experience level plus any Overpower level.

    Returns:
        The level that enemies and loot are measured against.
    """
    pc = get_pc()
    return int(pc.PlayerReplicationInfo.ExpLevel) + int(pc.OverpowerChoiceValue)


@cache
def _player_pawn_class() -> UClass:
    return unrealsdk.find_class("WillowPlayerPawn")


def _is_player_pawn(obj: UObject) -> bool:
    return obj.Class._inherits(_player_pawn_class())


def _apply_band(
    kind: str,
    obj: UObject,
    setter: BoundFunction,
    requested: int,
    *,
    floor: SpinnerOption,
    ceiling: SpinnerOption,
) -> type[Block] | None:
    """
    Replaces a level-setter call when the requested level falls outside the configured band.

    Args:
        kind: What is being scaled, for the log line.
        obj: The object whose level is being set.
        setter: The level setter the game is calling, bound to `obj`.
        requested: The level the game asked for.
        floor: The spinner holding the lower bound.
        ceiling: The spinner holding the upper bound.
    Returns:
        Block if the call was replaced with a clamped one, None to let the original run.
    """
    floor_offset = LEVEL_CHOICES.get(floor.value)
    ceiling_offset = LEVEL_CHOICES.get(ceiling.value)
    if floor_offset is None and ceiling_offset is None:
        return None

    player_level = get_player_level()
    wanted = clamp_level(requested, player_level, floor_offset, ceiling_offset)
    if wanted == requested:
        return None

    if log_adjustments.value:
        logging.info(
            f"[Enemy and Item Scaling] {kind} {obj.Name}: {requested} -> {wanted}"
            f" (player {player_level})",
        )

    # The args struct is a copy, so the only way to change the level is to call the setter
    # ourselves and block the original call. Direct calls in here don't re-trigger our hooks.
    with prevent_hooking_direct_calls():
        setter(wanted)
    return Block


@hook("WillowGame.WillowPawn:SetGameStage")
def on_pawn_game_stage(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    func: BoundFunction,
) -> type[Block] | None:
    """Scales an enemy's level as it spawns."""
    if _is_player_pawn(obj):
        return None
    requested = int(args.NewGameStage)
    return _apply_band(
        "enemy",
        obj,
        func,
        requested,
        floor=min_enemy_level,
        ceiling=max_enemy_level,
    )


@hook("WillowGame.WillowPawn:SetGameStageForSpawnedInventory")
@hook("WillowGame.WillowAIPawn:SetGameStageForSpawnedInventory")
def on_pawn_loot_game_stage(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    func: BoundFunction,
) -> type[Block] | None:
    """Scales the level of the loot an enemy will drop."""
    if _is_player_pawn(obj):
        return None
    requested = int(args.NewInventoryGameStage)
    return _apply_band("loot", obj, func, requested, floor=min_item_level, ceiling=max_item_level)


@hook("WillowGame.WillowInteractiveObject:SetGameStage")
def on_interactive_object_game_stage(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    func: BoundFunction,
) -> type[Block] | None:
    """Scales the level of chests, lockers and other containers."""
    requested = int(args.NewGameStage)
    return _apply_band(
        "container",
        obj,
        func,
        requested,
        floor=min_item_level,
        ceiling=max_item_level,
    )


mod = build_mod(
    options=[min_enemy_level, max_enemy_level, min_item_level, max_item_level, log_adjustments],
)
