# ossapi ([documentation](https://tybug.github.io/ossapi/)) [![PyPI version](https://badge.fury.io/py/ossapi.svg)](https://pypi.org/project/ossapi/)

ossapi is the definitive python wrapper for the osu! api. ossapi has complete coverage of [api v2](https://osu.ppy.sh/docs/index.html) and [api v1](https://github.com/ppy/osu-api/wiki), and provides both sync (`Ossapi`) and async (`OssapiAsync`) versions for api v2.

If you need support or would like to contribute, feel free to ask in the `#ossapi` channel of the [circleguard discord](https://discord.gg/e84qxkQ).

* [Installation](#installation)
* [Quickstart](#quickstart)
* [Async](#async)
* [Endpoints](#endpoints)
  * [Beatmap Packs](#endpoints-beatmap-packs)
  * [Beatmaps](#endpoints-beatmaps)
  * [Beatmapsets](#endpoints-beatmapsets)
  * [Changelog](#endpoints-changelog)
  * [Chat](#endpoints-chat)
  * [Comments](#endpoints-comments)
  * [Events](#endpoints-events)
  * [Forums](#endpoints-forums)
  * [Friends](#endpoints-friends)
  * [Home](#endpoints-home)
  * [Matches](#endpoints-matches)
  * [Me](#endpoints-me)
  * [News](#endpoints-news)
  * [OAuth](#endpoints-oauth)
  * [Rankings](#endpoints-rankings)
  * [Rooms](#endpoints-rooms)
  * [Scores](#endpoints-scores)
  * [Seasonal Backgrounds](#endpoints-seasonal-backgrounds)
  * [Spotlights](#endpoints-spotlights)
  * [Users](#endpoints-users)
  * [Wiki](#endpoints-wiki)
* [Other domains](#other-domains)
* [API v1 Usage](#api-v1-usage)


## Installation

To install:

```bash
pip install ossapi
# or, if you want to use OssapiAsync:
pip install ossapi[async]
```

To upgrade:

```bash
pip install -U ossapi
```

To get started, read the docs: https://tybug.github.io/ossapi/.

## Quickstart

[The docs](https://tybug.github.io/ossapi/) have an [in depth quickstart](https://tybug.github.io/ossapi/creating-a-client.html), but here's a super short version for api v2:

```python
from ossapi import Ossapi

# create a new client at https://osu.ppy.sh/home/account/edit#oauth
api = Ossapi(client_id, client_secret)

# see docs for full list of endpoints
print(api.user("tybug").username)
print(api.user(12092800, mode="osu").username)
print(api.beatmap(221777).id)
```

## Async

ossapi provides an async variant, `OssapiAsync`, which has an identical interface to `Ossapi`:

```python
import asyncio
from ossapi import OssapiAsync

api = OssapiAsync(client_id, client_secret)

async def main():
    await api.user("tybug")

asyncio.run(main())
```

[Read more about OssapiAsync on the docs.](https://tybug.github.io/ossapi/async.html)

## Other domains

You can use ossapi to interact with the api of other deployments of the osu website, such as https://dev.ppy.sh.

```python
from ossapi import Ossapi

api = Ossapi(client_id, client_secret, domain="dev")
# get the dev server pp leaderboards
ranking = api.ranking("osu", "performance").ranking
# pearline06, as of 2023
print(ranking[0].user.username)
```

[Read more about domains on the docs.](https://tybug.github.io/ossapi/domains.html)

## Endpoints

All endpoints for api v2.

* Beatmap Packs<a name="endpoints-beatmap-packs"></a>
  * [`api.beatmap_pack`](https://tybug.github.io/ossapi/beatmap%20packs.html#ossapi.ossapiv2.Ossapi.beatmap_pack)
  * [`api.beatmap_packs`](https://tybug.github.io/ossapi/beatmap%20packs.html#ossapi.ossapiv2.Ossapi.beatmap_packs)
* Beatmaps<a name="endpoints-beatmaps"></a>
  * [`api.beatmap`](https://tybug.github.io/ossapi/beatmaps.html#ossapi.ossapiv2.Ossapi.beatmap)
  * [`api.beatmap_attributes`](https://tybug.github.io/ossapi/beatmaps.html#ossapi.ossapiv2.Ossapi.beatmap_attributes)
  * [`api.beatmap_scores`](https://tybug.github.io/ossapi/beatmaps.html#ossapi.ossapiv2.Ossapi.beatmap_scores)
  * [`api.beatmap_user_score`](https://tybug.github.io/ossapi/beatmaps.html#ossapi.ossapiv2.Ossapi.beatmap_user_score)
  * [`api.beatmap_user_scores`](https://tybug.github.io/ossapi/beatmaps.html#ossapi.ossapiv2.Ossapi.beatmap_user_scores)
  * [`api.beatmaps`](https://tybug.github.io/ossapi/beatmaps.html#ossapi.ossapiv2.Ossapi.beatmaps)
* Beatmapsets<a name="endpoints-beatmapsets"></a>
  * [`api.beatmapset`](https://tybug.github.io/ossapi/beatmapsets.html#ossapi.ossapiv2.Ossapi.beatmapset)
  * [`api.beatmapset_discussion_posts`](https://tybug.github.io/ossapi/beatmapsets.html#ossapi.ossapiv2.Ossapi.beatmapset_discussion_posts)
  * [`api.beatmapset_discussion_votes`](https://tybug.github.io/ossapi/beatmapsets.html#ossapi.ossapiv2.Ossapi.beatmapset_discussion_votes)
  * [`api.beatmapset_discussions`](https://tybug.github.io/ossapi/beatmapsets.html#ossapi.ossapiv2.Ossapi.beatmapset_discussions)
  * [`api.beatmapset_events`](https://tybug.github.io/ossapi/beatmapsets.html#ossapi.ossapiv2.Ossapi.beatmapset_events)
  * [`api.search_beatmapsets`](https://tybug.github.io/ossapi/beatmapsets.html#ossapi.ossapiv2.Ossapi.search_beatmapsets)
* Changelog<a name="endpoints-changelog"></a>
  * [`api.changelog_build`](https://tybug.github.io/ossapi/changelog.html#ossapi.ossapiv2.Ossapi.changelog_build)
  * [`api.changelog_build_lookup`](https://tybug.github.io/ossapi/changelog.html#ossapi.ossapiv2.Ossapi.changelog_build_lookup)
  * [`api.changelog_listing`](https://tybug.github.io/ossapi/changelog.html#ossapi.ossapiv2.Ossapi.changelog_listing)
* Chat<a name="endpoints-chat"></a>
  * [`api.send_announcement`](https://tybug.github.io/ossapi/chat.html#ossapi.ossapiv2.Ossapi.send_announcement)
  * [`api.send_pm`](https://tybug.github.io/ossapi/chat.html#ossapi.ossapiv2.Ossapi.send_pm)
* Comments<a name="endpoints-comments"></a>
  * [`api.comment`](https://tybug.github.io/ossapi/comments.html#ossapi.ossapiv2.Ossapi.comment)
  * [`api.comments`](https://tybug.github.io/ossapi/comments.html#ossapi.ossapiv2.Ossapi.comments)
* Events<a name="endpoints-events"></a>
  * [`api.events`](https://tybug.github.io/ossapi/events.html#ossapi.ossapiv2.Ossapi.events)
* Forums<a name="endpoints-forums"></a>
  * [`api.forum_create_topic`](https://tybug.github.io/ossapi/forums.html#ossapi.ossapiv2.Ossapi.forum_create_topic)
  * [`api.forum_edit_post`](https://tybug.github.io/ossapi/forums.html#ossapi.ossapiv2.Ossapi.forum_edit_post)
  * [`api.forum_edit_topic`](https://tybug.github.io/ossapi/forums.html#ossapi.ossapiv2.Ossapi.forum_edit_topic)
  * [`api.forum_reply`](https://tybug.github.io/ossapi/forums.html#ossapi.ossapiv2.Ossapi.forum_reply)
  * [`api.forum_topic`](https://tybug.github.io/ossapi/forums.html#ossapi.ossapiv2.Ossapi.forum_topic)
* Friends<a name="endpoints-friends"></a>
  * [`api.friends`](https://tybug.github.io/ossapi/friends.html#ossapi.ossapiv2.Ossapi.friends)
* Home<a name="endpoints-home"></a>
  * [`api.search`](https://tybug.github.io/ossapi/home.html#ossapi.ossapiv2.Ossapi.search)
* Matches<a name="endpoints-matches"></a>
  * [`api.match`](https://tybug.github.io/ossapi/matches.html#ossapi.ossapiv2.Ossapi.match)
  * [`api.matches`](https://tybug.github.io/ossapi/matches.html#ossapi.ossapiv2.Ossapi.matches)
* Me<a name="endpoints-me"></a>
  * [`api.get_me`](https://tybug.github.io/ossapi/me.html#ossapi.ossapiv2.Ossapi.get_me)
* News<a name="endpoints-news"></a>
  * [`api.news_listing`](https://tybug.github.io/ossapi/news.html#ossapi.ossapiv2.Ossapi.news_listing)
  * [`api.news_post`](https://tybug.github.io/ossapi/news.html#ossapi.ossapiv2.Ossapi.news_post)
* OAuth<a name="endpoints-oauth"></a>
  * [`api.revoke_token`](https://tybug.github.io/ossapi/oauth.html#ossapi.ossapiv2.Ossapi.revoke_token)
* Rankings<a name="endpoints-rankings"></a>
  * [`api.ranking`](https://tybug.github.io/ossapi/rankings.html#ossapi.ossapiv2.Ossapi.ranking)
* Rooms<a name="endpoints-rooms"></a>
  * [`api.multiplayer_scores`](https://tybug.github.io/ossapi/rooms.html#ossapi.ossapiv2.Ossapi.multiplayer_scores)
  * [`api.room`](https://tybug.github.io/ossapi/rooms.html#ossapi.ossapiv2.Ossapi.room)
  * [`api.room_leaderboard`](https://tybug.github.io/ossapi/rooms.html#ossapi.ossapiv2.Ossapi.room_leaderboard)
  * [`api.rooms`](https://tybug.github.io/ossapi/rooms.html#ossapi.ossapiv2.Ossapi.rooms)
* Scores<a name="endpoints-scores"></a>
  * [`api.download_score`](https://tybug.github.io/ossapi/scores.html#ossapi.ossapiv2.Ossapi.download_score)
  * [`api.download_score_mode`](https://tybug.github.io/ossapi/scores.html#ossapi.ossapiv2.Ossapi.download_score_mode)
  * [`api.score`](https://tybug.github.io/ossapi/scores.html#ossapi.ossapiv2.Ossapi.score)
  * [`api.score_mode`](https://tybug.github.io/ossapi/scores.html#ossapi.ossapiv2.Ossapi.score_mode)
* Seasonal Backgrounds<a name="endpoints-seasonal-backgrounds"></a>
  * [`api.seasonal_backgrounds`](https://tybug.github.io/ossapi/seasonal%20backgrounds.html#ossapi.ossapiv2.Ossapi.seasonal_backgrounds)
* Spotlights<a name="endpoints-spotlights"></a>
  * [`api.spotlights`](https://tybug.github.io/ossapi/spotlights.html#ossapi.ossapiv2.Ossapi.spotlights)
* Users<a name="endpoints-users"></a>
  * [`api.user`](https://tybug.github.io/ossapi/users.html#ossapi.ossapiv2.Ossapi.user)
  * [`api.user_beatmaps`](https://tybug.github.io/ossapi/users.html#ossapi.ossapiv2.Ossapi.user_beatmaps)
  * [`api.user_kudosu`](https://tybug.github.io/ossapi/users.html#ossapi.ossapiv2.Ossapi.user_kudosu)
  * [`api.user_recent_activity`](https://tybug.github.io/ossapi/users.html#ossapi.ossapiv2.Ossapi.user_recent_activity)
  * [`api.user_scores`](https://tybug.github.io/ossapi/users.html#ossapi.ossapiv2.Ossapi.user_scores)
  * [`api.users`](https://tybug.github.io/ossapi/users.html#ossapi.ossapiv2.Ossapi.users)
  * [`api.users_lookup`](https://tybug.github.io/ossapi/users.html#ossapi.ossapiv2.Ossapi.users_lookup)
* Wiki<a name="endpoints-wiki"></a>
  * [`api.wiki_page`](https://tybug.github.io/ossapi/wiki.html#ossapi.ossapiv2.Ossapi.wiki_page)

## API v1 Usage

You can get your api v1 key at <https://osu.ppy.sh/home/account/edit#legacy-api>.

Basic usage:

```python
from ossapi import OssapiV1

api = OssapiV1("key")
print(api.get_beatmaps(user=53378)[0].submit_date)
print(api.get_match(69063884).games[0].game_id)
print(api.get_scores(221777)[0].username)
print(len(api.get_replay(beatmap_id=221777, user=6974470)))
print(api.get_user(12092800).playcount)
print(api.get_user_best(12092800)[0].pp)
print(api.get_user_recent(12092800)[0].beatmap_id)
```
