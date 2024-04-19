from json.decoder import JSONDecodeError
import logging
from datetime import datetime, timezone
from typing import List
import time

import requests
from requests import RequestException

from ossapi.mod import Mod

# log level below debug
TRACE = 5


class APIException(Exception):
    """An error involving the osu! api."""


class InvalidKeyException(APIException):
    def __init__(self):
        super().__init__("Please provide a valid api key")


class ReplayUnavailableException(APIException):
    pass


class OssapiV1:
    """
    A simple api wrapper. Every public method takes a dict as its argument,
    mapping keys to values.

    No attempt is made to ratelimit the connection or catch request errors.
    This is left to the user implementation.
    """

    # how long in seconds to wait for a request to finish before raising a
    # requests.Timeout` exception
    TIMEOUT = 15
    BASE_URL = "https://osu.ppy.sh/api/"
    # how long in seconds it takes the api to refresh our ratelimits after our
    # first request
    RATELIMIT_REFRESH = 60

    def __init__(self, key):
        self._key = key
        self.log = logging.getLogger(__name__)
        # when we started our requests cycle
        self.start_time = datetime.min

    def _get(self, endpoint, params, type_, list_=False, _beatmap_id=None):
        # _beatmap_id parameter exists because api v1 is badly designed and
        # returns models which are missing some information if you already
        # passed that value in the api call. So we need to supply it here so
        # we can make our models homogeneous.
        difference = datetime.now() - self.start_time
        if difference.seconds > self.RATELIMIT_REFRESH:
            self.start_time = datetime.now()

        params["k"] = self._key
        url = f"{self.BASE_URL}{endpoint}"
        self.log.debug(f"making request to url {url} with params {params}")

        try:
            r = requests.get(url, params=params, timeout=self.TIMEOUT)
        except RequestException as e:
            self.log.warning(
                f"Request exception: {e}. Likely a network issue; "
                "sleeping for 5 seconds then retrying"
            )
            time.sleep(5)
            return self._get(endpoint, params, type_, list_, _beatmap_id)

        self.log.log(TRACE, f"made request to url {r.request.url}")

        try:
            data = r.json()
        except JSONDecodeError:
            self.log.warning(
                "the api returned invalid json. Likely a "
                "temporary issue, waiting and retrying"
            )
            time.sleep(3)
            return self._get(endpoint, params, type_, list_, _beatmap_id)

        self.log.log(TRACE, f"got data from api: {data}")

        if "error" in data:
            error = data["error"]
            if error == "Replay not available.":
                raise ReplayUnavailableException("Could not find any replay data")
            if error == "Requesting too fast! Slow your operation, cap'n!":
                self._enforce_ratelimit()
                return self._get(endpoint, params, type_, list_, _beatmap_id)
            if error == "Replay retrieval failed.":
                raise ReplayUnavailableException("Replay retrieval failed")
            if error == "Please provide a valid API key.":
                raise InvalidKeyException()
            raise APIException(f"Unknown error when requesting a replay: {error}.")

        if list_:
            ret = []
            for entry in data:
                if _beatmap_id:
                    entry["beatmap_id"] = _beatmap_id
                ret.append(type_(entry))
        else:
            ret = type_(data)

        return ret

    def _enforce_ratelimit(self):
        """
        Sleeps the thread until we have refreshed our ratelimits.
        """
        difference = datetime.now() - self.start_time
        seconds_passed = difference.seconds

        # sleep the remainder of the reset cycle so we guarantee it's been that
        # long since the first request
        sleep_seconds = self.RATELIMIT_REFRESH - seconds_passed
        sleep_seconds = max(sleep_seconds, 0)
        self.log.info("Ratelimited, sleeping for %s seconds.", sleep_seconds)
        time.sleep(sleep_seconds)

    def get_beatmaps(
        self,
        since=None,
        beatmapset_id=None,
        beatmap_id=None,
        user=None,
        user_type=None,
        mode=None,
        include_converts=None,
        beatmap_hash=None,
        limit=None,
        mods=None,
    ) -> List["Beatmap"]:
        params = {
            "since": since,
            "s": beatmapset_id,
            "b": beatmap_id,
            "u": user,
            "type": user_type,
            "m": mode,
            "a": include_converts,
            "h": beatmap_hash,
            "limit": limit,
            "mods": mods,
        }
        return self._get("get_beatmaps", params, Beatmap, list_=True)

    def get_match(self, match_id) -> "MatchInfo":
        params = {"mp": match_id}
        return self._get("get_match", params, MatchInfo)

    def get_scores(
        self, beatmap_id, user=None, mode=None, mods=None, user_type=None, limit=None
    ) -> List["Score"]:
        params = {
            "b": beatmap_id,
            "u": user,
            "m": mode,
            "mods": mods,
            "type": user_type,
            "limit": limit,
        }
        return self._get(
            "get_scores", params, Score, list_=True, _beatmap_id=beatmap_id
        )

    def get_replay(
        self,
        beatmap_id=None,
        user=None,
        mode=None,
        score_id=None,
        user_type=None,
        mods=None,
    ) -> str:
        params = {
            "b": beatmap_id,
            "u": user,
            "m": mode,
            "s": score_id,
            "type": user_type,
            "mods": mods,
        }
        r = self._get("get_replay", params, Replay)
        return r.content

    def get_user(self, user, mode=None, user_type=None, event_days=None) -> "User":
        params = {"u": user, "m": mode, "type": user_type, "event_days": event_days}
        users = self._get("get_user", params, User, list_=True)
        # api returns a list of users even though we never get more than one
        # user, just extract it manually
        return users[0] if users else users

    def get_user_best(
        self, user, mode=None, limit=None, user_type=None
    ) -> List["Score"]:
        params = {"u": user, "m": mode, "limit": limit, "type": user_type}
        return self._get("get_user_best", params, Score, list_=True)

    def get_user_recent(
        self, user, mode=None, limit=None, user_type=None
    ) -> List["Score"]:
        params = {"u": user, "m": mode, "limit": limit, "type": user_type}
        return self._get("get_user_recent", params, Score, list_=True)


# ideally we'd use the ossapiv2 machinery (dataclasses + annotations) for these
# models instead of this manual drudgery. Unfortunately said machinery requires
# python 3.8+ and I'm not willing to drop support for python 3.7 quite yet
# (I'd be okay with dropping 3.6 though). This is a temporary meassure until
# such a time when I can justify dropping 3.7.
# Should be a 'write once and forget about it' kind of thing anyway since v1 is
# extremely stable, but would be nice to migrate over to v2's way of doing
# things at some point.


class Model:
    def __init__(self, data):
        self._data = data

    def _get(self, attr, optional=False):
        if attr not in self._data and optional:
            return None
        return self._data[attr]

    def _date(self, attr):
        attr = self._data[attr]
        if attr is None:
            return None

        date = datetime.strptime(attr, "%Y-%m-%d %H:%M:%S")
        # all api provided datetimes are in utc
        return date.replace(tzinfo=timezone.utc)

    def _int(self, attr):
        attr = self._data[attr]
        if attr is None:
            return None

        return int(attr)

    def _float(self, attr):
        attr = self._data[attr]
        if attr is None:
            return None

        return float(attr)

    def _bool(self, attr):
        attr = self._data[attr]
        if attr is None:
            return None

        if attr == "1":
            return True
        return False

    def _mod(self, attr):
        attr = self._data[attr]
        if attr is None:
            return None

        return Mod(int(attr))


class Beatmap(Model):
    def __init__(self, data):
        super().__init__(data)

        self.approved = self._get("approved")
        self.submit_date = self._date("submit_date")
        self.approved_date = self._date("approved_date")
        self.last_update = self._date("last_update")
        self.artist = self._get("artist")
        self.beatmap_id = self._int("beatmap_id")
        self.beatmapset_id = self._int("beatmapset_id")
        self.bpm = self._get("bpm")
        self.creator = self._get("creator")
        self.creator_id = self._int("creator_id")
        self.star_rating = self._float("difficultyrating")
        self.stars_aim = self._float("diff_aim")
        self.stars_speed = self._float("diff_speed")
        self.circle_size = self._float("diff_size")
        self.overrall_difficulty = self._float("diff_overall")
        self.approach_rate = self._float("diff_approach")
        self.health = self._float("diff_drain")
        self.hit_length = self._float("hit_length")
        self.source = self._get("source")
        self.genre_id = self._int("genre_id")
        self.language_id = self._int("language_id")
        self.title = self._get("title")
        self.total_length = self._float("total_length")
        self.version = self._get("version")
        self.beatmap_hash = self._get("file_md5")
        self.mode = self._int("mode")
        self.tags = self._get("tags")
        self.favourite_count = self._int("favourite_count")
        self.rating = self._float("rating")
        self.playcount = self._int("playcount")
        self.passcount = self._int("passcount")
        self.count_hitcircles = self._int("count_normal")
        self.count_sliders = self._int("count_slider")
        self.count_spinners = self._int("count_spinner")
        self.max_combo = self._int("max_combo")
        self.storyboard = self._bool("storyboard")
        self.video = self._bool("video")
        self.download_unavailable = self._bool("download_unavailable")
        self.audio_unavailable = self._bool("audio_unavailable")


class User(Model):
    def __init__(self, data):
        super().__init__(data)

        self.user_id = self._int("user_id")
        self.username = self._get("username")
        self.join_date = self._date("join_date")
        self.count_300 = self._int("count300")
        self.count_100 = self._int("count100")
        self.count_50 = self._int("count50")
        self.playcount = self._int("playcount")
        self.ranked_score = self._int("ranked_score")
        self.total_score = self._int("total_score")
        self.rank = self._int("pp_rank")
        self.level = self._float("level")
        self.pp_raw = self._float("pp_raw")
        self.accuracy = self._float("accuracy")
        self.count_rank_ss = self._int("count_rank_ss")
        self.count_rank_ssh = self._int("count_rank_ssh")
        self.count_rank_s = self._int("count_rank_s")
        self.count_rank_sh = self._int("count_rank_sh")
        self.count_rank_a = self._int("count_rank_a")
        self.country = self._get("country")
        self.seconds_played = self._int("total_seconds_played")
        self.country_rank = self._int("pp_country_rank")

        self.events = []
        for event in data["events"]:
            event = Event(event)
            self.events.append(event)


class Event(Model):
    def __init__(self, data):
        super().__init__(data)

        self.display_html = self._get("display_html")
        self.beatmap_id = self._int("beatmap_id")
        self.beatmapset_id = self._int("beatmapset_id")
        self.date = self._date("date")
        self.epic_factor = self._int("epicfactor")


class Score(Model):
    def __init__(self, data):
        super().__init__(data)

        self.beatmap_id = self._int("beatmap_id")
        self.replay_id = self._int("score_id")
        self.score = self._int("score")
        self.username = self._get("username", optional=True)
        self.count_300 = self._int("count300")
        self.count_100 = self._int("count100")
        self.count_50 = self._int("count50")
        self.count_miss = self._int("countmiss")
        self.max_combo = self._int("maxcombo")
        self.count_katu = self._int("countkatu")
        self.count_geki = self._int("countgeki")
        self.perfect = self._bool("perfect")
        self.mods = self._mod("enabled_mods")
        self.user_id = self._int("user_id")
        self.date = self._date("date")
        self.rank = self._get("rank")
        # get_user_recent doesn't provide pp or replay_available at all
        self.pp = self._float("pp") if "pp" in data else None
        self.replay_available = (
            self._bool("replay_available") if "replay_available" in data else None
        )


class Replay(Model):
    def __init__(self, data):
        super().__init__(data)
        self.content = self._get("content")


class MatchInfo(Model):
    def __init__(self, data):
        super().__init__(data)

        self.match = Match(data["match"])

        self.games = []
        for game in data["games"]:
            game = MatchGame(game)
            self.games.append(game)


class Match(Model):
    def __init__(self, data):
        super().__init__(data)

        self.match_id = self._int("match_id")
        self.name = self._get("name")
        self.start_time = self._date("start_time")
        self.end_time = self._date("end_time")


class MatchGame(Model):
    def __init__(self, data):
        super().__init__(data)

        self.game_id = self._int("game_id")
        self.start_time = self._date("start_time")
        self.end_time = self._date("end_time")
        self.beatmap_id = self._int("beatmap_id")
        self.play_mode = self._int("play_mode")
        self.match_type = self._int("match_type")
        self.scoring_type = self._int("scoring_type")
        self.team_type = self._int("team_type")
        self.mods = self._mod("mods")

        self.scores = []
        for score in data["scores"]:
            score = MatchScore(score)
            self.scores.append(score)


class MatchScore(Model):
    def __init__(self, data):
        super().__init__(data)

        self.slot = self._int("slot")
        self.team = self._int("team")
        self.user_id = self._int("user_id")
        self.score = self._int("score")
        self.max_combo = self._int("maxcombo")
        self.rank = self._int("rank")
        self.count_300 = self._int("count300")
        self.count_100 = self._int("count100")
        self.count_50 = self._int("count50")
        self.count_miss = self._int("countmiss")
        self.max_combo = self._int("maxcombo")
        self.count_katu = self._int("countkatu")
        self.count_geki = self._int("countgeki")
        self.perfect = self._bool("perfect")
        self.passed = self._bool("pass")
        self.mods = self._mod("enabled_mods")
