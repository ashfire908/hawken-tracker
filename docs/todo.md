# TODO

* Frontend
    * Layout
    * URLs are defined
    * JS for leaderboards/player match list implemented
* Permissions
    * List-based parameter lookup
    * Player match listing vs Listing players in matches
    * Optimize permission queries
    * Determine default privacy levels
* Player profiles
* Group support
    * Per-group player privacy
    * Determine how roles will work
    * Figure out permission cascading
    * Group profile pages
    * Member management
* Rank tracking over time
    * Weekly snapshots of positions for comparison (rank move up/down)?
    * Time period?
    * Should the ranked stat value be tracked as well?
* Seasons
* Fix to\_next()/to\_last()
* Graphs and analytics
    * Distribution of players per stat
* Region
    * Filter players by region
    * Rank players by region as well as global
* Compensation for players who don't play much
    * Exclude players who haven't played in the last X days?
    * Decay their rating/ranking during inactivity and progressively remove the decay when activity goes back up?
* Migrate to an explicit opt-in/out system (make the default null and people can explicitly opt in or out, so it can be experimented with at launch)

## Other stuff

* Forum signature generator

## Misc suggestions

* User-selectable stylesheets (i.e. so clans can iframe it into their websites with minimal effort)
* Tested to work against the Steam overlay browser
