# -*- coding: utf-8 -*-
# Hawken Tracker - Mappings

from enum import IntEnum, unique
from hawkentracker.util import CaseInsensitiveDict


# Database enums
@unique
class Role(IntEnum):
    anonymous = 0
    user = 1
    group_member = 2
    group_manager = 3
    group_admin = 4
    admin = 5


@unique
class ListingPrivacy(IntEnum):
    public = 0
    unlisted = 1
    private = 2


@unique
class JoinPrivacy(IntEnum):
    public = 0
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


# Redis ranked fields
ranking_fields = ("mmr", "time_played", "xp_per_min", "hc_per_min", "kda", "kill_steals", "critical_assists",
                  "damage", "win_loss", "dm_win_loss", "tdm_win_loss", "ma_win_loss", "sg_win_loss", "coop_win_loss",
                  "cooptdm_win_loss")

# Privacy defaults
default_privacy = {
    "leaderboard": Role.anonymous,
    "rank": Role.admin,
    "stats": Role.admin,
    "match": Role.user
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
    "Comp-UK": "Comp Europe"
})

map_names = CaseInsensitiveDict({
    "VS-Alleys": "Uptown",
    "VS-Andromeda": "Prosk",
    "VS-Bunker": "Bunker",
    "VS-Facility": "Facility",
    "VS-FightClub": "Fight Club",
    "VS-LastEco": "Last Eco",
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
    "xp_per_min": "XP/Min",
    "hc_per_min": "HC/Min",
    "kda": "KDA Ratio",
    "kill_steals": "Steals/Kills",
    "critical_assists": "Critical/Assists",
    "damage": "Damage Ratio",
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
    "xp_per_min": "XP per Min",
    "hc_per_min": "HC per Min",
    "kda": "Kills + Assists / Deaths",
    "kill_steals": "Kill Steals / Kills",
    "critical_assists": "Critical / Assists",
    "damage": "Damage Ratio",
    "win_loss": "Win/Loss",
    "dm_win_loss": "DM Win/Loss",
    "tdm_win_loss": "TDM Win/Loss",
    "ma_win_loss": "MA Win/Loss",
    "sg_win_loss": "Siege Win/Loss",
    "coop_win_loss": "Coop Win/Loss",
    "cooptdm_win_loss": "Coop TDM Win/Loss"
}
