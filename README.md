[![PyPI version](https://badge.fury.io/py/ossapi.svg)](https://pypi.org/project/ossapi/)

# ossapi ([documentation](https://circleguard.github.io/ossapi/))

ossapi is a python wrapper for the osu! api. ossapi supports both [api v2](https://osu.ppy.sh/docs/index.html) and [api v1](https://github.com/ppy/osu-api/wiki) and has every endpoint in both versions implemented.

To install:

```bash
pip install ossapi
```

To upgrade:

```bash
pip install -U ossapi
```

To get started, read the docs: https://circleguard.github.io/ossapi/.

If you need support or would like to contribute, feel free to join the circleguard discord: <https://discord.gg/e84qxkQ>.

## Quickstart

[The docs](https://circleguard.github.io/ossapi/) have an [in depth quickstart](https://circleguard.github.io/ossapi/creating-a-client.html), but here's a super short version:

```python
from ossapi import Ossapi
# create a new client at https://osu.ppy.sh/home/account/edit#oauth
client_id = None
client_secret = None
callback_url = None # choose a port on localhost, eg http://localhost:727/

# client credentials authentication...
api = Ossapi(client_id, client_secret)

# ...or authorization grant authentication
api = Ossapi(client_id, client_secret, callback_url)

# go wild with endpoint calls! See docs for all endpoints
print(api.user("tybug2"))
```


## API v1 Usage

You can get your api v1 key at <https://osu.ppy.sh/p/api/>. Note that due to a [redirection bug](https://github.com/ppy/osu-web/issues/2867), you may need to log in and wait 30 seconds before being able to access the api page through the above link.

Basic usage:

```python
from ossapi import Ossapi

api = Ossapi("key")
print(api.get_beatmaps(user=53378)[0].submit_date)
print(api.get_match(69063884).games[0].game_id)
print(api.get_scores(221777)[0].username)
print(len(api.get_replay(beatmap_id=221777, user=6974470)))
print(api.get_user(12092800).playcount)
print(api.get_user_best(12092800)[0].pp)
print(api.get_user_recent(12092800)[0].beatmap_id)
```
