from functools import cache
from typing import TYPE_CHECKING, Any

import unrealsdk
from mods_base import BoolOption, SpinnerOption, build_mod, get_pc, hook
from unrealsdk import logging
from unrealsdk.hooks import Block, Type, prevent_hooking_direct_calls

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
on_level_mission_rewards = BoolOption(
    "On-Level Mission Rewards",
    False,
    description=(
        "Mission reward items are generated at your level instead of the mission's level.\n"
        "The mission's XP and cash rewards scale with it."
    ),
)
on_level_vendors = BoolOption(
    "On-Level Vendors",
    False,
    description=(
        "Vending machines stock items at your level, including the item of the day.\n"
        "Applies when a machine spawns or restocks."
    ),
)
log_adjustments = BoolOption(
    "Log Adjustments",
    False,
    description="Print every level change to the console. Useful when testing.",
)

LOG_PREFIX = "[Enemy and Item Scaling]"


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


# GetCurrentPlaythrough() is 0-based: Normal, TVHM, UVHM. Overpower levels only exist in UVHM.
UVHM_PLAYTHROUGH = 2


def player_level_for(pc: UObject) -> int | None:
    """
    Gets a player's effective level: experience level, plus the Overpower level in UVHM.

    Args:
        pc: The player's WillowPlayerController.
    Returns:
        The level that enemies and loot are measured against, or None while the player isn't
        loaded yet (a level of 0 would otherwise drag every spawn down to nothing).
    """
    pri = pc.PlayerReplicationInfo
    if pri is None:
        return None
    level = int(pri.ExpLevel)
    if level <= 0:
        return None
    if pc.GetCurrentPlaythrough() == UVHM_PLAYTHROUGH:
        level += int(pc.OverpowerChoiceValue)
    return level


def get_player_level() -> int | None:
    """
    Gets the local player's effective level, or None while they aren't loaded yet.

    Returns:
        See `player_level_for`.
    """
    pc = get_pc(possibly_loading=True)
    return None if pc is None else player_level_for(pc)


@cache
def _player_pawn_class() -> UClass:
    return unrealsdk.find_class("WillowPlayerPawn")


@cache
def _vending_machine_class() -> UClass:
    return unrealsdk.find_class("WillowVendingMachineBase")


def _is_player_pawn(obj: UObject) -> bool:
    return obj.Class._inherits(_player_pawn_class())


def _is_vending_machine(obj: UObject) -> bool:
    return obj.Class._inherits(_vending_machine_class())


def _replace_level(
    kind: str,
    obj: UObject,
    setter: BoundFunction,
    requested: int,
    *,
    wanted: int,
    player_level: int,
) -> type[Block] | None:
    """
    Re-issues a level-setter call with a different level, if it differs from the requested one.

    Args:
        kind: What is being scaled, for the log line.
        obj: The object whose level is being set.
        setter: The level setter the game is calling, bound to `obj`.
        requested: The level the game asked for.
        wanted: The level we want instead.
        player_level: The player's level, for the log line.
    Returns:
        Block if the call was replaced, None to let the original run untouched.
    """
    if wanted == requested:
        return None

    if log_adjustments.value:
        logging.info(
            f"{LOG_PREFIX} {kind} {obj.Name}: {requested} -> {wanted} (player {player_level})",
        )

    # The args struct is a copy, so the only way to change the level is to call the setter
    # ourselves and block the original call. Direct calls in here don't re-trigger our hooks.
    with prevent_hooking_direct_calls():
        setter(wanted)
    return Block


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
    if player_level is None:
        return None
    wanted = clamp_level(requested, player_level, floor_offset, ceiling_offset)
    return _replace_level(kind, obj, setter, requested, wanted=wanted, player_level=player_level)


def _apply_on_level(
    kind: str,
    obj: UObject,
    setter: BoundFunction,
    requested: int,
    *,
    enabled: BoolOption,
) -> type[Block] | None:
    """
    Replaces a level-setter call with the player's level, when the toggle is on.

    Args:
        kind: What is being scaled, for the log line.
        obj: The object whose level is being set.
        setter: The level setter the game is calling, bound to `obj`.
        requested: The level the game asked for.
        enabled: The toggle for this source.
    Returns:
        Block if the call was replaced, None to let the original run.
    """
    if not enabled.value:
        return None
    player_level = get_player_level()
    if player_level is None:
        return None
    return _replace_level(
        kind,
        obj,
        setter,
        requested,
        wanted=player_level,
        player_level=player_level,
    )


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
    """
    Scales the level of chests, slot machines and other containers, and of vending machines.

    Vending machines are interactive objects too, but they get their own toggle rather than the
    item band.
    """
    requested = int(args.NewGameStage)
    if _is_vending_machine(obj):
        return _apply_on_level("vendor", obj, func, requested, enabled=on_level_vendors)
    return _apply_band(
        "container",
        obj,
        func,
        requested,
        floor=min_item_level,
        ceiling=max_item_level,
    )


@hook("WillowGame.WillowVendingMachine:ResetInventory")
def on_vending_machine_reset(
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    """
    Re-levels a vending machine right before it restocks.

    A machine keeps the level it spawned with, so without this the 20 minute restock (and paid
    resets) would keep producing stock at the level you had when you entered the map.
    """
    if not on_level_vendors.value:
        return
    player_level = get_player_level()
    if player_level is None:
        return
    current = int(obj.GameStage)
    if current == player_level:
        return

    if log_adjustments.value:
        logging.info(f"{LOG_PREFIX} vendor restock {obj.Name}: {current} -> {player_level}")
    # Same pair of setters the game's own factory calls when it spawns the machine
    with prevent_hooking_direct_calls():
        obj.SetGameStage(player_level)
        obj.SetExpLevel(player_level)


# Mission stages we changed so rewards roll at the player's level, keyed by mission path and
# holding the original (GameStage, bGameStageLocked). Restored once the reward has been taken.
_saved_mission_stages: dict[str, tuple[int, bool]] = {}

# EMissionStatus values for a mission the player has accepted but not finished with:
# Active, RequiredObjectivesComplete, ReadyToTurnIn.
MISSION_ACCEPTED_STATUSES = frozenset({1, 2, 3})


def _level_mission(mission: UObject, pc: UObject) -> None:
    """
    Sets a mission's game stage to a player's level, remembering what it was.

    The native reward roll, the XP and cash, and any mod that asks `mission.GetGameStage()`
    all read this field while the mission is locked, so writing it is what makes rewards come
    out on level regardless of who does the rolling.

    Args:
        mission: The MissionDefinition.
        pc: The WillowPlayerController whose level to use.
    """
    player_level = player_level_for(pc)
    if player_level is None:
        return
    current = int(mission.GameStage)
    locked = bool(mission.bGameStageLocked)
    if current == player_level and locked:
        return

    if log_adjustments.value:
        logging.info(f"{LOG_PREFIX} mission reward {mission.Name}: {current} -> {player_level}")
    _saved_mission_stages.setdefault(mission._path_name(), (current, locked))
    mission.GameStage = player_level
    # Accepted missions are already locked; make sure of it so the game doesn't recompute the
    # stage from the mission's region.
    mission.bGameStageLocked = True


@hook("WillowGame.QuestAcceptGFxMovie:UpdateMissionList", Type.POST)
@hook("WillowGame.QuestAcceptGFxMovie:DetermineQuestEntries", Type.POST)
@hook("WillowGame.QuestAcceptGFxMovie:extPopulateQuestEntries", Type.POST)
def on_mission_list_updated(
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    """
    Levels every accepted mission in an NPC's mission list as soon as the list is built.

    This happens before anything can be turned in, whichever order other mods' hooks run in,
    which is what makes mods that roll rewards themselves (Reward Reroller) see the level.
    """
    if not on_level_mission_rewards.value:
        return
    pc = obj.WPCOwner
    if pc is None:
        return
    for entry in obj.MissionList:
        if int(entry.MissionStatus) in MISSION_ACCEPTED_STATUSES and entry.MissionDef is not None:
            _level_mission(entry.MissionDef, pc)


@hook("WillowGame.QuestAcceptGFxMovie:SetRewardCard")
def on_reward_card(
    _obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    """
    Levels an accepted mission when its reward card is shown, before anything can turn it in.

    This is early enough for mods that roll the rewards themselves on the turn-in confirm,
    such as Reward Reroller, whose calls never go through the hooks below.
    """
    if not on_level_mission_rewards.value:
        return
    mission = args.MissionDef
    pc = args.WPC
    if mission is None or pc is None:
        return
    if int(pc.GetPlayersMissionStatus(mission)) not in MISSION_ACCEPTED_STATUSES:
        return
    _level_mission(mission, pc)


@hook("WillowGame.QuestAcceptGFxMovie:extCompleteConfirmed")
def on_complete_confirmed(
    obj: UObject,
    _args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    """
    Backstop: levels the mission as the turn-in is confirmed.

    Only beats another mod's hook on the same function if ours registered first (true when
    both were enabled at launch), so the mission-list hook above is the one to rely on.
    """
    if not on_level_mission_rewards.value:
        return
    pc = obj.WPCOwner
    if pc is None:
        return
    mission = obj.MissionList[obj.GetSelectedIndex()].MissionDef
    if mission is None:
        return
    _level_mission(mission, pc)


@hook("WillowGame.WillowPlayerController:ServerGrantMissionRewards")
def on_grant_mission_rewards(
    obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    """
    Levels a mission to the player it is rewarding, right before the game rolls the rewards.

    Covers completions that never show a reward card (scripted ones). Expected to run on the
    host once per player (untested in co-op), so the level comes from that player's controller.
    """
    if not on_level_mission_rewards.value:
        return
    mission = args.Mission
    if mission is None:
        return
    _level_mission(mission, obj)


def _restore_mission(mission: UObject) -> None:
    """
    Puts a mission's stage back to what the game had, if we changed it.

    Args:
        mission: The MissionDefinition.
    """
    saved = _saved_mission_stages.pop(mission._path_name(), None)
    if saved is None:
        return
    mission.GameStage, mission.bGameStageLocked = saved


# EMissionStatus.MS_Complete
MISSION_COMPLETE = 4


@hook("WillowGame.WillowPlayerController:MissionRewardsReceived", Type.POST_UNCONDITIONAL)
def on_mission_rewards_received(
    _obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    """Restores the mission once the player has taken the reward (rerolls included)."""
    mission = args.Mission
    if mission is not None:
        _restore_mission(mission)


@hook("WillowGame.WillowPlayerController:UpdateMissionStatus", Type.POST_UNCONDITIONAL)
def on_mission_status_updated(
    _obj: UObject,
    args: WrappedStruct,
    _ret: Any,
    _func: BoundFunction,
) -> None:
    """
    Restores the mission when it is marked complete.

    In the vanilla flow this fires before the reward roll, and the ServerGrantMissionRewards
    hook simply levels the mission again; with Reward Reroller it fires when the reward is
    accepted, after the rolls. Either way nothing is left levelled once the mission is done.
    """
    if int(args.NewMissionStatus) != MISSION_COMPLETE:
        return
    mission = args.Mission
    if mission is not None:
        _restore_mission(mission)


mod = build_mod(
    options=[
        min_enemy_level,
        max_enemy_level,
        min_item_level,
        max_item_level,
        on_level_mission_rewards,
        on_level_vendors,
        log_adjustments,
    ],
)
