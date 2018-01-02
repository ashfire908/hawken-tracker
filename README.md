# Hawken Tracker

Hawken Tracker is a website that tracks player activity within [Hawken](https://www.playhawken.com/) and provides leaderboards as well as other planned features via a web interface. It is made in Python 3.x, and built on top of the [Hawken Python API library](https://github.com/ashfire908/hawken-api "Currently closed-source"), [Flask](http://flask.pocoo.org/), [Jade (now called Pug)](https://github.com/pugjs/pug), [SQLAlchemy](https://www.sqlalchemy.org/) + [PostgreSQL](https://www.postgresql.org/), and [Redis](https://redis.io/).

## History

Prior to the Hawken Tracker, there was a quick-and-dirty script in late 2013 to build a list of players from the server list, and then fetch all their MMRs every day and generate a leaderboard from that. This script was eventually taken down due to limited features, poor optimization, and under Hawken developer concerns that it may be negatively impacting the game. Thus, the Hawken Tracker was born.

Development of a formal website and tracking system was developed from then through 2015, going through multiple phases, before being eventually dropped, due to lack of intrest, a competing leaderboard getting setup, and the lack of a frontend developer on the project. This repo is what remains of the project.

## License

Hawken Tracker is released under the [MIT LICENSE](LICENSE).
