# osuAPI

OsuAPI is a python wrapper for the osu api. Endpoints are implemented as necessary for the [circleguard](https://github.com/circleguard/circleguard) project. Passed keys (endpoint parameter key/value pairs, not the api key) are checked to make sure the api will accept them, and that all required keys are present. No attempt is made to check http status codes or retry requests that fail.

Currently, only the `get_replay` and `get_scores` endpoints are implemented. Should you be a completionist, you are more than welcome to PR the rest in.

### Usage

To install:
```bash
$ pip install git+https://github.com/circleguard/osu-api
```

To use:
```python
from osuAPI import OsuAPI

api = OsuAPI("key")
api.get_replay({m: "0", b: "1776628", u: "3256299"})
# either strings or ints will work. Returns something like `{"content":"XQAAIA....3fISw=","encoding":"base64"}`
```
