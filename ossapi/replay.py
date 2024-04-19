from osrparse import GameMode as OsrparseGameMode, Replay as OsrparseReplay

from ossapi.models import GameMode, User, Beatmap
from ossapi.mod import Mod
from ossapi.enums import UserLookupKey

game_mode_map = {
    OsrparseGameMode.STD: GameMode.OSU,
    OsrparseGameMode.TAIKO: GameMode.TAIKO,
    OsrparseGameMode.CTB: GameMode.CATCH,
    OsrparseGameMode.MANIA: GameMode.MANIA,
}


class Replay(OsrparseReplay):
    """
    A replay played by a player.

    Notes
    -----
    This is a thin wrapper around an :class:`osrparse.replay.Replay` instance.
    It converts some attributes to more appropriate types and adds :meth:`.user`
    and :meth:`.beatmap` to retrieve api-related objects.
    """

    def __init__(self, replay, api):
        super().__init__(
            mode=game_mode_map[replay.mode],
            game_version=replay.game_version,
            beatmap_hash=replay.beatmap_hash,
            username=replay.username,
            replay_hash=replay.replay_hash,
            count_300=replay.count_300,
            count_100=replay.count_100,
            count_50=replay.count_50,
            count_geki=replay.count_geki,
            count_katu=replay.count_katu,
            count_miss=replay.count_miss,
            score=replay.score,
            max_combo=replay.max_combo,
            perfect=replay.perfect,
            mods=Mod(replay.mods.value),
            life_bar_graph=replay.life_bar_graph,
            timestamp=replay.timestamp,
            replay_data=replay.replay_data,
            replay_id=replay.replay_id,
            rng_seed=replay.rng_seed,
        )

        self._osrparse_mode = replay.mode
        self._osrparse_mods = replay.mods
        self._api = api
        self._beatmap = None
        self._user = None

    @property
    def beatmap(self) -> Beatmap:
        """
        The beatmap this replay was played on.

        Warnings
        --------
        Accessing this property for the first time will result in a web request
        to retrieve the beatmap from the api. We cache the return value, so
        further accesses are free.
        """
        if self._beatmap:
            return self._beatmap
        self._beatmap = self._api.beatmap(checksum=self.beatmap_hash)
        return self._beatmap

    @property
    def user(self) -> User:
        """
        The user that played this replay.

        Warnings
        --------
        Accessing this property for the first time will result in a web request
        to retrieve the user from the api. We cache the return value, so further
        accesses are free.
        """
        if self._user:
            return self._user
        self._user = self._api.user(self.username, key=UserLookupKey.USERNAME)
        return self._user

    def pack(self, *, dict_size=None, mode=None):
        r = OsrparseReplay(
            mode=self._osrparse_mode,
            game_version=self.game_version,
            beatmap_hash=self.beatmap_hash,
            username=self.username,
            replay_hash=self.replay_hash,
            count_300=self.count_300,
            count_100=self.count_100,
            count_50=self.count_50,
            count_geki=self.count_geki,
            count_katu=self.count_katu,
            count_miss=self.count_miss,
            score=self.score,
            max_combo=self.max_combo,
            perfect=self.perfect,
            mods=self._osrparse_mods,
            life_bar_graph=self.life_bar_graph,
            timestamp=self.timestamp,
            replay_data=self.replay_data,
            replay_id=self.replay_id,
            rng_seed=self.rng_seed,
        )
        return r.pack(dict_size=dict_size, mode=mode)
