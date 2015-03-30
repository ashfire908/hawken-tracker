// Leaderboard data
var leaderboard_map = {
  "rank": "Rank",
  "player": "Player",
  "region": "Region",
  "mmr": "MMR",
  "time_played": "Time Played",
  "xp_per_min": "XP/Min",
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
};
var leaderboard_cols = Object.keys(leaderboard_map);
var leaderboard_ignore = ["rank", "player", "region"];
var leaderboard_always = ["mmr", "kda"];
var leaderboard_endpoint = null;

// Player matches data
var playermatches_map = {
  "id": "Match Id",
  "server_name": "Server Name",
  "server_region": "Region",
  "server_gametype": "Game Type",
  "server_map": "Map",
  "first_seen": "Joined",
  "last_seen": "Left"
};
var playermatches_cols = Object.keys(playermatches_map);

// Duration formatter
Number.prototype.toHHMMSS = function () {
    var seconds = Math.floor(this);
    var hours = Math.floor(seconds / 3600);
    seconds -= hours * 3600;
    var minutes = Math.floor(seconds / 60);
    seconds -= minutes * 60;

    if (hours < 10) {hours = "0" + hours;}
    if (minutes < 10) {minutes = "0" + minutes;}
    if (seconds < 10) {seconds = "0" + seconds;}
    return hours + ":" + minutes + ":" + seconds;
};

// Player lookup
function lookup_player() {
  var player = $("#lookup input").val().trim();
  if (player != "") {
    window.open("/player/" + player, "_self", false);
  }
}

// Get the leaderboard url
function leaderboard_url(sort, extra) {
  var params = {
    "sort": sort
  };

  extra = leaderboard_always.filter(function(element) { return element != sort; });
  if (extra.length > 0) {
    params["extra"] = extra.join(",");
  }

  return leaderboard_endpoint + "?" + $.param(params);
}

// Format player
function format_player(data, type, row) {
  if (type != "display") {
    return data;
  }

  if (data == null) {
    return "[Private]";
  }

  return '<a href="/player/' + data + '">' + data + '</a>';
}

// Format match
function format_match(data, type, row) {
  if (type != "display") {
    return data;
  }

  if (data == null) {
    return "[Private]";
  }

  return '<a href="/match/' + data + '">' + data + '</a>';
}

// Format fixed number
function format_fixed(data, type, row) {
  if (type != "display" || data == null) {
    return data;
  }

  return (Math.round(data * 100) / 100).toFixed(2);
}

// Format percent
function format_percent(data, type, row) {
  if (type != "display" || data == null) {
    return data;
  }

  return String(Math.round(data * 1000) / 10) + "%";
}

// Format duration
function format_duration(data, type, row) {
  if (type != "display" || data == null) {
    return data;
  }

  return data.toHHMMSS();
}


// Setup the leaderboard
function setup_leaderboard(table, menu, label, endpoint, sort) {
  // Set the endpoint
  leaderboard_endpoint = endpoint;

  // Build the column info and rank menu
  var cols = [];
  menu = $(menu);
  for (var i = 0; i < leaderboard_cols.length; i++) {
    var name = leaderboard_cols[i];
    var ignore = $.inArray(name, leaderboard_ignore) != -1;
    var info = {
      "data": name,
      "name": name,
      "title": leaderboard_map[name],
      "visible": ignore || name == sort || $.inArray(name, leaderboard_always) != -1
    };

    // Set the renderer and default
    switch (name) {
      case "rank":
        info["width"] = "60px";
        break;
      case "player":
        info["render"] = format_player;
        break;
      case "region":
        info["defaultContent"] = "[Private]";
        break;
      case "mmr":
      case "xp_per_min":
      case "hc_per_min":
      case "kda":
      case "damage_ratio":
      case "win_loss":
      case "dm_win_loss":
      case "tdm_win_loss":
      case "ma_win_loss":
        info["width"] = "100px";
        info["render"] = format_fixed;
        info["defaultContent"] = "";
        break;
      case "sg_win_loss":
      case "coop_win_loss":
        info["width"] = "120px";
        info["render"] = format_fixed;
        info["defaultContent"] = "";
        break;
      case "cooptdm_win_loss":
        info["width"] = "140px";
        info["render"] = format_fixed;
        info["defaultContent"] = "";
        break;
      case "kill_steal_ratio":
      case "critical_assist_ratio":
        info["width"] = "100px";
        info["render"] = format_percent;
        info["defaultContent"] = "";
        break;
      case "time_played":
        info["width"] = "100px";
        info["render"] = format_duration;
        info["defaultContent"] = "";
        break;
      default:
        info["defaultContent"] = "";
    }

    cols.push(info);

    // Create menu item
    if (!ignore) {
      menu.append($("<li/>").append($("<a/>", {
        "data-sort": name,
        "class": "toggle-sort",
        "text": leaderboard_map[name]
      })));
    }
  }

  // Init the table
  $(table).DataTable({
    "ajax": leaderboard_url(sort),
    "columns": cols,
    "lengthMenu": [[25, 50, -1], [25, 50, "All"]],
    "processing": true
  });

  // Setup the sorters
  $(".toggle-sort").click(function (e) {
    e.preventDefault();

    sort_leaderboard(table, label, $(this).attr("data-sort"));
  });
}

// Select leaderboard sort
function sort_leaderboard(table, label, sort) {
  table = $(table).DataTable();
  for (var i = 0; i < leaderboard_cols.length; i++) {
    var name = leaderboard_cols[i];
    if ($.inArray(name, leaderboard_ignore) != -1 || name == sort || $.inArray(name, leaderboard_always) != -1) {
      table.column(i).visible(true);
    } else {
      table.column(i).visible(false);
    }
  }

  // Reload the table data
  table.ajax.url(leaderboard_url(sort));
  table.ajax.reload();

  // Update the label
  $(label).text(leaderboard_map[sort]);
}

// Setup the player matches table
function setup_player_matches(table, endpoint) {
  // Build the column info and rank menu
  var cols = [];
  var default_sort = 0;
  for (var i = 0; i < playermatches_cols.length; i++) {
    var name = playermatches_cols[i];
    var info = {
      "data": name,
      "name": name,
      "title": playermatches_map[name]
    };

    if (name == "id") {
      info["render"] = format_match;
    }

    if (name == "last_seen") {
      default_sort = i;
    }

    cols.push(info);
  }

  // Init the table
  $(table).DataTable({
    "ajax": {
      "url": endpoint,
      "type": "POST"
    },
    "order": [[default_sort, "desc"]],
    "columns": cols,
    "processing": true,
    "serverSide": true
  });
}

// Setup the match players table
function setup_match_players(table) {
  $(table).dataTable({
    "paging": false,
    "searching": false
  });
}

// All our base event handlers
$(document).ready(function() {
  // Lookup player on enter or button click
  $("#lookup input").keypress(function (e) {
    if (e.which == 13) {
      lookup_player();
    }
  });
  $("#lookup button").click(function() {
    lookup_player();
  });
});