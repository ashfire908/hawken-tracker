# -*- coding: utf-8 -*-
# Hawken Tracker - Mappings

from enum import Enum, IntEnum, unique
from hawkentracker.util import CaseInsensitiveDict

# Internal enums
@unique
class UpdateFlag(Enum):
    players = "players"
    matches = "matches"
    callsigns = "callsigns"


# Database enums
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
