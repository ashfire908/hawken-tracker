# Permissions

## Abilites

Abilities are flags that can be checked to determine if the current auth status will allow for the action to be performed.

### User

User abilites control all aspects of the user accounts themselves.

* user.list - _List all registered users_
* user.create.self - _Create an account_
* user.create.other - _Create an account on behalf of another user_
* user.{user}.view - _View information for a user_
* user.{user}.delete - _Delete a user_
* user.{user}.settings - _Edit a user's settings_
* user.{user}.role - _Edit a user's role_
* user.{user}.password - _Edit a user's password_
* user.{user}.link.list - _List a user's associated players_
* user.{user}.link.{player}.add - _Link a user to a player_
* user.{user}.link.{player}.remove - _Unlink a user from a player_

### Player

Player abilites control all aspects of the known players.

* player.list.public - _List all public players_
* player.list.all - _List all known players_
* player.search - _Search for a player by stored player data_
* player.blacklist.access - _Access a blacklisted player's data_
* player.blacklist.view - _View a player's blacklist data_
* player.blacklist.change - _Change a player's blacklist data_
* player.{player}.view - _View a player's page_
* player.{player}.region - _View a player's region_
* player.{player}.leaderboard - _View a player within leaderboards_
* player.{player}.rankings - _View a player's rankings on their page_
* player.{player}.stats.ranked - _View a player's ranked stats_
* player.{player}.stats.overall - _View a player's global stats_
* player.{player}.stats.mech - _View a player's mech stats_
* player.{player}.match.list - _View a player's list of matches_
* player.{player}.match.{match}.view - _View a player within the match listing_
* player.{player}.group - _View a player's joined groups and group-related info_
* player.{player}.link.user - _View a player's linked username_
* player.{player}.link.players - _View a player's other associated players_
* player.{player}.settings - _Set a player's settings_

### Match

* match.list - _List all known matches_
* match.search - _Search for matches by stored match data_
* match.{match}.view - _View information for a match_
* match.{match}.players - _View player info for a match_
* match.{match}.stats - _View stats for a match_

### Group

**Not Implemented Yet**

* group.list.public - _List public groups_
* group.list.all - _List all groups, regardless of privacy_
* group.search - _Search for groups by group data_
* group.{group}.create - _Create a group_
* group.{group}.view - _View a group's information_
* group.{group}.edit - _Edit a group's settings_
* group.{group}.delete - _Delete a group_
* group.{group}.rankings - _View a group's rankings_
* group.{group}.matches - _View a group's matches_
* group.{group}.member.list - _View a group's player roster_
* group.{group}.member.{player}.add - _Add a player to a group (with full confirmation status)_
* group.{group}.member.{player}.invite - _Invite a player to a group (with player-pending confirmation status)_
* group.{group}.member.{player}.join - _Join a player to a group (with group-pending confirmation status)_
* group.{group}.member.{player}.approve - _Accept a player's request to join a group_
* group.{group}.member.{player}.accept - _Accept a group's request to join a group_
* group.{group}.member.{player}.edit.role - _Edit a player's role with a group_
* group.{group}.member.{player}.edit.membership - _Edit a player's membership with a group_
* group.{group}.member.{player}.remove - _Remove a player from a group_
* group.{group}.member.{player}.ignore - _Set a group as blocked for a player, blocking invites from the group for the player_
* group.{group}.member.{player}.block - _Set a player as blocked for a group, blocking a player from attempting to join a group_

## Roles

Roles are collections of permissions. They are assigned to either users or members of a group, and is the dynamic portion of the permissions system. User and group roles are completely distinct from each other. User roles can be flagged with 'superadmin', granting the user full permissions in all situations. Group roles have no such option. Permissions granted by a user role are applied site-wide, while permissions granted by a group role are only applied within the context of that group (or when permissions cascading is enabled).

## Permissions

Permissions are abilites with a power level set. To be granted the ability, the user must have been granted a power level equal to or greater than has been assigned to the ability within the current context.

## Groups

**Not Implemented Yet**

Groups have additional permission mechanics beyond the global user permissions.

### Permission Cascading

Normally access to a player's stats is determined by the current user's role and permissions. However, if the player in question shares a group with the current user, and the player enabled permissions cascading, the user can be granted additional access by the player according to the powers set within the player's group privacy settings.