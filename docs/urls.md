# URL map

* / - Main page; Leaderboards
* /login - Login page
* /login/forgot - Forgotten login page
* /login/reset - Password reset page
* /login/verify/<token> - Verify user email
* /logout - Logout page
* /register - Register user account
* /create/user - Create a new user account (admin)
* /create/group - Create a new group
* /account - Account dashboard for the current user
* /account/settings - Settings for the current user
* /account/password - Change password for the current user
* /account/link/<target> - Link an account with a player
* /account/unlink/<target> - Unlink an account with a player
* /account/delete - Delete the current account
* /search/user - Search users
* /search/player - Search players
* /search/match - Search matches
* /search/group - Search groups
* /user - List of registered users
* /user/<user> - User profile page
* /user/<user>/settings - Change a user's settings (admin)
* /user/<user>/password - Change a user's password (admin)
* /user/<user>/link/<target> - Link a user with a player
* /user/<user>/unlink/<target> - Unlink a user with a player
* /user/<user>/delete
* /player - List of players
* /player/<target> - View a player
* /player/<target>/settings - Edit a player's settings
* /player/<target>/blacklist - Edit a player's blacklist status
* /match - List of matches
* /match/<id> - View a match
* /group - List of groups
* /group/<group> - View a group
* /group/<group>/roster - View a group's roster
* /group/<group>/join - Join a group
* /group/<group>/leave - Leave a group
* /group/<group>/preferences - Edit your preferences for a group
* /group/<group>/dashboard - Dashbord for managing a group
* /group/<group>/edit - Edit a group's properties
* /group/<group>/delete - Delete a group
* /group/<group>/member/edit - Edit a group member's role
* /group/<group>/member/invite - Invite a player to the group
* /group/<group>/member/remove - Remove a player from the group
* /data/leaderboard/global - DataTables endpoint for global leaderboards
* /data/leaderboard/group/<group> - DataTables endpoint for group leaderboard
* /data/player/<player>/matches - DataTables endpoint for player's matches
