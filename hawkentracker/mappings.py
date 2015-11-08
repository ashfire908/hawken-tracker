# -*- coding: utf-8 -*-
# Hawken Tracker - Mappings

from enum import Enum, IntEnum, unique

from hawkentracker.util import CaseInsensitiveDict


# Tracker Enums
@unique
class UpdateFlag(Enum):
    all_players = "players"
    all_matches = "matches"
    update_callsigns = "callsigns"


@unique
class UpdateStatus(IntEnum):
    not_started = 0
    in_progress = 1
    failed = 2
    complete = 3


@unique
class UpdateStage(IntEnum):
    not_started = 0
    complete = 1
    players = 2
    matches = 3
    global_rankings = 4


@unique
class LinkStatus(IntEnum):
    none = 0
    pending = 1
    linked = 2


@unique
class JoinPrivacy(IntEnum):
    open = 0
    approval = 1
    invite_only = 2


@unique
class Confirmation(IntEnum):
    player = 0
    group = 1
    both = 2
    player_blocked = 3
    group_blocked = 4
    both_blocked = 5


@unique
class CoreRole(IntEnum):
    anonymous = 1
    unconfirmed = 2
    user = 3


@unique
class IngesterStatus(str, Enum):
    unset = "unset"
    processed = "processed"
    failed = "failed"
    skipped = "skipped"
    error = "error"


# Event enums/mappings
@unique
class WinReason(str, Enum):
    # These aren't technically lowercase, but we convert it to lower because of TimeLimit/timelimit.
    team_score_limit = "teamscorelimit"
    time_limit = "timelimit"
    triggered = "triggered"
    base_destroyed = "basedestroyed"
    no_players = "noplayers"


@unique
class GameType(IntEnum):
    siege = 0
    deathmatch = 1
    team_deathmatch = 2
    # unused = 3
    missile_assault = 4
    horde_deprecated = 5
    asymmetrical_siege = 6
    coop_bot_destruction = 7
    capture_the_flag = 8
    any = 9  # ???
    vr_training = 10
    coop_team_deathmatch = 11
    explore = 12
    invalid = 99


@unique
class GameTypeStorm(str, Enum):
    siege = "HawkenSG"
    deathmatch = "HawkenDM"
    team_deathmatch = "HawkenTDM"
    missile_assault = "HawkenMA"
    # horde_deprecated = unknown
    # asymmetrical_siege = unknown
    coop_bot_destruction = "HawkenCoOp"
    # capture_the_flag = unknown
    # any = unknown
    # vr_training = unknown
    coop_team_deathmatch = "HawkenBotsTdm"
    # explore = unknown

    # Not a real game type
    entry_game = "R_EntryGame"


@unique
class Map(str, Enum):
    uptown = "Alleys"
    prosk = "Andromeda"
    bunker = "Bunker"
    facility = "Facility"
    fight_club = "fightclub"
    last_eco = "LastEco"
    last_eco_winter = "lasteco-winter"
    bazaar = "Sahara"
    origin = "Titan"
    tutorial_vr = "tutorialvr"
    front_line = "Valkirie"
    wreckage = "Wreckage"
    main_menu = "RobotsMainMenu"


@unique
class MapStorm(str, Enum):
    uptown = "VS-Alleys"
    prosk = "VS-Andromeda"
    bunker = "VS-Bunker"
    facility = "VS-Facility"
    facility_coop = "CO-Facility"
    fight_club = "vs-fightclub"
    last_eco = "VS-LastEco"
    last_eco_winter = "vs-lasteco-winter"
    bazaar = "VS-Sahara"
    origin = "VS-Titan"
    tutorial_vr = "TR-TutorialVR"
    front_line = "VS-Valkirie"
    front_line_coop = "CO-Valkirie"
    wreckage = "VS-Wreckage"
    main_menu = "RobotsMainMenu"


# Redis ranked fields
ranking_fields = ("mmr", "time_played", "xp", "xp_per_min", "hc", "hc_per_min", "kda", "kill_steal_ratio",
                  "critical_assist_ratio", "damage_ratio", "win_loss", "dm_win_loss", "tdm_win_loss", "ma_win_loss",
                  "sg_win_loss", "coop_win_loss", "cooptdm_win_loss")

# Roles and permissions
default_privacy = {
    "user.user.view": 0,
    "user.user.link.list": 0,
    "player.player.view": 0,
    "player.player.region": 0,
    "player.player.leaderboard": 0,
    "player.player.rankings": 0,
    "player.player.stats.ranked": 0,
    "player.player.stats.overall": 0,
    "player.player.stats.mech": 0,
    "player.player.match.list": 0,
    "player.player.match.match.view": 0,
    "player.player.group": 100,  # Groups are not implemented
    "player.player.link.players": 0
}

# Region groupings
region_groupings = {
    "Asia": "Asia-Oceania",
    "Asia-Oceana": "Asia-Oceania",
    "Asia-Oceania": "Asia-Oceania",
    "Atlantic": "Atlantic",
    "Australia": "Asia-Oceania",
    "Comp-UK": "Europe",
    "Comp-US-East": "North-America",
    "Comp-US-West": "North-America",
    "Europe": "Europe",
    "Japan": "Asia-Oceania",
    "Middle-East": "Middle-East",
    "North-America": "North-America",
    "Oceania": "Asia-Oceania",
    "SaoPaulo": "South-America",
    "Singapore": "Asia-Oceania",
    "South-America": "South-America",
    "UK": "Europe",
    "US-Central": "North-America",
    "US-East": "North-America",
    "US-West": "North-America"
}

# Human-readable API mappings
region_names = CaseInsensitiveDict({
    "US-East": "USA East",
    "US-West": "USA West",
    "US-Central": "USA Central",
    "UK": "Europe",
    "Japan": "Japan",
    "Singapore": "Singapore",
    "Australia": "Australia",
    "Comp-US-East": "Comp USA East",
    "Comp-US-West": "Comp USA West",
    "Comp-UK": "Comp Europe",
    "SaoPaulo": "Brazil"
})

map_names = CaseInsensitiveDict({
    "VS-Alleys": "Uptown",
    "VS-Andromeda": "Prosk",
    "VS-Bunker": "Bunker",
    "VS-Facility": "Facility",
    "VS-FightClub": "Fight Club",
    "VS-LastEco": "Last Eco",
    "VS-LastEco-Winter": "Last Eco (Winter)",
    "VS-Sahara": "Bazaar",
    "VS-Titan": "Origin",
    "VS-Valkirie": "Front Line",
    "VS-Wreckage": "Wreckage",
    "CO-Facility": "Co-Op Facility",
    "CO-Valkirie": "Co-Op Front Line"
})

gametype_names = CaseInsensitiveDict({
    "HawkenTDM": "Team Deathmatch",
    "HawkenDM": "Deathmatch",
    "HawkenSG": "Siege",
    "HawkenMA": "Missile Assault",
    "HawkenCoOp": "Co-Op Bot Destruction",
    "HawkenBotsTDM": "Co-Op Team Deathmatch"
})

# Human-readable field names
ranking_names = {
    "mmr": "MMR",
    "time_played": "Time Played",
    "xp": "XP",
    "xp_per_min": "XP/Min",
    "hc": "HC",
    "hc_per_min": "HC/Min",
    "kda": "KDA Ratio",
    "kill_steal_ratio": "Steals/Kills",
    "critical_assist_ratio": "Critical/Assists",
    "damage_ratio": "Damage Ratio",
    "win_loss": "Win/Loss",
    "dm_win_loss": "DM Win/Loss",
    "tdm_win_loss": "TDM Win/Loss",
    "ma_win_loss": "MA Win/Loss",
    "sg_win_loss": "Siege Win/Loss",
    "coop_win_loss": "Coop Win/Loss",
    "cooptdm_win_loss": "Coop TDM Win/Loss"
}

ranking_names_full = {
    "mmr": "MMR",
    "time_played": "Time Played",
    "xp": "Total XP",
    "xp_per_min": "XP per Min",
    "hc": "Total HC",
    "hc_per_min": "HC per Min",
    "kda": "Kills + Assists / Deaths",
    "kill_steal_ratio": "Kill Steals / Kills",
    "critical_assist_ratio": "Critical / Assists",
    "damage_ratio": "Damage Ratio",
    "win_loss": "Win/Loss",
    "dm_win_loss": "DM Win/Loss",
    "tdm_win_loss": "TDM Win/Loss",
    "ma_win_loss": "MA Win/Loss",
    "sg_win_loss": "Siege Win/Loss",
    "coop_win_loss": "Coop Win/Loss",
    "cooptdm_win_loss": "Coop TDM Win/Loss"
}
