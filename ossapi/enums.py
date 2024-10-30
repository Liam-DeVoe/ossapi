from typing import Optional, List, Any

from ossapi.utils import EnumModel, Datetime, Model, Field, IntFlagModel

# ================
# Documented Enums
# ================


class ProfilePage(EnumModel):
    ME = "me"
    RECENT_ACTIVITY = "recent_activity"
    BEATMAPS = "beatmaps"
    HISTORICAL = "historical"
    KUDOSU = "kudosu"
    TOP_RANKS = "top_ranks"
    MEDALS = "medals"


class GameMode(EnumModel):
    OSU = "osu"
    TAIKO = "taiko"
    CATCH = "fruits"
    MANIA = "mania"


class PlayStyles(IntFlagModel):
    MOUSE = 1
    KEYBOARD = 2
    TABLET = 4
    TOUCH = 8

    @classmethod
    def _missing_(cls, value):
        """
        Allow instantiation via either strings or lists of ints / strings. The
        api returns a list of strings for User.playstyle.
        """
        if isinstance(value, list):
            value = iter(value)
            new_val = cls(next(value))
            for val in value:
                new_val |= cls(val)
            return new_val

        if value == "mouse":
            return PlayStyles.MOUSE
        if value == "keyboard":
            return PlayStyles.KEYBOARD
        if value == "tablet":
            return PlayStyles.TABLET
        if value == "touch":
            return PlayStyles.TOUCH
        return super()._missing_(value)


class RankStatus(EnumModel):
    GRAVEYARD = -2
    WIP = -1
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4

    @classmethod
    def _missing_(cls, value):
        """
        The api can return ``RankStatus`` values as either an int or a string,
        so if we try to instantiate with a string, return the corresponding
        enum attribute.
        """
        if value == "graveyard":
            return cls(-2)
        if value == "wip":
            return cls(-1)
        if value == "pending":
            return cls(0)
        if value == "ranked":
            return cls(1)
        if value == "approved":
            return cls(2)
        if value == "qualified":
            return cls(3)
        if value == "loved":
            return cls(4)
        return super()._missing_(value)


class UserAccountHistoryType(EnumModel):
    NOTE = "note"
    RESTRICTION = "restriction"
    SILENCE = "silence"
    # TODO undocumented
    TOURNAMENT_BAN = "tournament_ban"


class MessageType(EnumModel):
    HYPE = "hype"
    MAPPER_NOTE = "mapper_note"
    PRAISE = "praise"
    PROBLEM = "problem"
    REVIEW = "review"
    SUGGESTION = "suggestion"


class BeatmapsetEventType(EnumModel):
    APPROVE = "approve"
    BEATMAP_OWNER_CHANGE = "beatmap_owner_change"
    DISCUSSION_DELETE = "discussion_delete"
    DISCUSSION_LOCK = "discussion_lock"
    DISCUSSION_POST_DELETE = "discussion_post_delete"
    DISCUSSION_POST_RESTORE = "discussion_post_restore"
    DISCUSSION_RESTORE = "discussion_restore"
    DISCUSSION_UNLOCK = "discussion_unlock"
    DISQUALIFY = "disqualify"
    DISQUALIFY_LEGACY = "disqualify_legacy"
    GENRE_EDIT = "genre_edit"
    ISSUE_REOPEN = "issue_reopen"
    ISSUE_RESOLVE = "issue_resolve"
    KUDOSU_ALLOW = "kudosu_allow"
    KUDOSU_DENY = "kudosu_deny"
    KUDOSU_GAIN = "kudosu_gain"
    KUDOSU_LOST = "kudosu_lost"
    KUDOSU_RECALCULATE = "kudosu_recalculate"
    LANGUAGE_EDIT = "language_edit"
    LOVE = "love"
    NOMINATE = "nominate"
    NOMINATE_MODES = "nominate_modes"
    NOMINATION_RESET = "nomination_reset"
    NOMINATION_RESET_RECEIVED = "nomination_reset_received"
    QUALIFY = "qualify"
    RANK = "rank"
    REMOVE_FROM_LOVED = "remove_from_loved"
    NSFW_TOGGLE = "nsfw_toggle"


class BeatmapsetDownload(EnumModel):
    ALL = "all"
    NO_VIDEO = "no_video"
    DIRECT = "direct"


class UserListFilters(EnumModel):
    ALL = "all"
    ONLINE = "online"
    OFFLINE = "offline"


class UserListSorts(EnumModel):
    LAST_VISIT = "last_visit"
    RANK = "rank"
    USERNAME = "username"


class UserListViews(EnumModel):
    CARD = "card"
    LIST = "list"
    BRICK = "brick"


class KudosuAction(EnumModel):
    GIVE = "vote.give"
    RESET = "vote.reset"
    REVOKE = "vote.revoke"


class EventType(EnumModel):
    ACHIEVEMENT = "achievement"
    BEATMAP_PLAYCOUNT = "beatmapPlaycount"
    BEATMAPSET_APPROVE = "beatmapsetApprove"
    BEATMAPSET_DELETE = "beatmapsetDelete"
    BEATMAPSET_REVIVE = "beatmapsetRevive"
    BEATMAPSET_UPDATE = "beatmapsetUpdate"
    BEATMAPSET_UPLOAD = "beatmapsetUpload"
    RANK = "rank"
    RANK_LOST = "rankLost"
    USER_SUPPORT_FIRST = "userSupportFirst"
    USER_SUPPORT_AGAIN = "userSupportAgain"
    USER_SUPPORT_GIFT = "userSupportGift"
    USERNAME_CHANGE = "usernameChange"


# used for `EventType.BEATMAPSET_APPROVE`
class BeatmapsetApproval(EnumModel):
    RANKED = "ranked"
    APPROVED = "approved"
    QUALIFIED = "qualified"
    LOVED = "loved"


class ForumTopicType(EnumModel):
    NORMAL = "normal"
    STICKY = "sticky"
    ANNOUNCEMENT = "announcement"


class ChangelogMessageFormat(EnumModel):
    HTML = "html"
    MARKDOWN = "markdown"


# ==================
# Undocumented Enums
# ==================


class UserRelationType(EnumModel):
    # undocumented
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/
    # UserRelationTransformer.php#L20
    FRIEND = "friend"
    BLOCK = "block"


class Grade(EnumModel):
    SSH = "XH"
    SS = "X"
    SH = "SH"
    S = "S"
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    F = "F"


class RoomType(EnumModel):
    # https://github.com/ppy/osu-web/blob/3d1586392102b05f2a3b264905c4dbb7b2d43
    # 0a2/resources/js/interfaces/room-json.ts#L10
    PLAYLISTS = "playlists"
    HEAD_TO_HEAD = "head_to_head"
    TEAM_VERSUS = "team_versus"


class RoomCategory(EnumModel):
    # https://github.com/ppy/osu-web/blob/3d1586392102b05f2a3b264905c4dbb7b2d
    # 430a2/resources/js/interfaces/room-json.ts#L7
    NORMAL = "normal"
    SPOTLIGHT = "spotlight"
    FEATURED_ARTIST = "featured_artist"
    DAILY_CHALLENGE = "daily_challenge"


class MatchEventType(EnumModel):
    # https://github.dev/ppy/osu-web/blob/3d1586392102b05f2a3b264905c4dbb7b2
    # d430a2/app/Models/LegacyMatch/Event.php#L30
    PLAYER_LEFT = "player-left"
    PLAYER_JOINED = "player-joined"
    PLAYER_KICKED = "player-kicked"
    MATCH_CREATED = "match-created"
    MATCH_DISBANDED = "match-disbanded"
    HOST_CHANGED = "host-changed"
    OTHER = "other"


class ScoringType(EnumModel):
    # https://github.com/ppy/osu-web/blob/3d1586392102b05f2a3b264905c4dbb7b2d4
    # 30a2/app/Models/LegacyMatch/Game.php#L40
    SCORE = "score"
    ACCURACY = "accuracy"
    COMBO = "combo"
    SCORE_V2 = "scorev2"


class TeamType(EnumModel):
    # https://github.com/ppy/osu-web/blob/3d1586392102b05f2a3b264905c4dbb7b2d43
    # 0a2/app/Models/LegacyMatch/Game.php#L47
    HEAD_TO_HEAD = "head-to-head"
    TAG_COOP = "tag-coop"
    TEAM_VS = "team-vs"
    TAG_TEAM_VS = "tag-team-vs"


class Variant(EnumModel):
    # can't start a python identifier with an integer
    KEY_4 = "4k"
    KEY_7 = "7k"


# ===============
# Parameter Enums
# ===============


class ScoreType(EnumModel):
    BEST = "best"
    FIRSTS = "firsts"
    RECENT = "recent"


class RankingFilter(EnumModel):
    ALL = "all"
    FRIENDS = "friends"


class RankingType(EnumModel):
    CHARTS = "charts"
    COUNTRY = "country"
    PERFORMANCE = "performance"
    SCORE = "score"


class UserLookupKey(EnumModel):
    ID = "id"
    USERNAME = "username"


class UserBeatmapType(EnumModel):
    FAVOURITE = "favourite"
    GRAVEYARD = "graveyard"
    LOVED = "loved"
    MOST_PLAYED = "most_played"
    RANKED = "ranked"
    PENDING = "pending"
    GUEST = "guest"
    NOMINATED = "nominated"


class BeatmapDiscussionPostSort(EnumModel):
    NEW = "id_desc"
    OLD = "id_asc"


class BeatmapsetStatus(EnumModel):
    ALL = "all"
    RANKED = "ranked"
    QUALIFIED = "qualified"
    DISQUALIFIED = "disqualified"
    NEVER_QUALIFIED = "never_qualified"


class ChannelType(EnumModel):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"
    MULTIPLAYER = "MULTIPLAYER"
    SPECTATOR = "SPECTATOR"
    TEMPORARY = "TEMPORARY"
    PM = "PM"
    GROUP = "GROUP"
    ANNOUNCE = "ANNOUNCE"


class CommentableType(EnumModel):
    NEWS_POST = "news_post"
    CHANGELOG = "build"
    BEATMAPSET = "beatmapset"


class CommentSort(EnumModel):
    NEW = "new"
    OLD = "old"
    TOP = "top"


class ForumTopicSort(EnumModel):
    NEW = "id_desc"
    OLD = "id_asc"


class SearchMode(EnumModel):
    ALL = "all"
    USERS = "user"
    WIKI = "wiki_page"


class MultiplayerScoresSort(EnumModel):
    NEW = "score_desc"
    OLD = "score_asc"


class BeatmapsetDiscussionVote(EnumModel):
    UPVOTE = 1
    DOWNVOTE = -1


class BeatmapsetDiscussionVoteSort(EnumModel):
    NEW = "id_desc"
    OLD = "id_asc"


class BeatmapsetSearchCategory(EnumModel):
    ANY = "any"
    HAS_LEADERBOARD = "leaderboard"
    RANKED = "ranked"
    QUALIFIED = "qualified"
    LOVED = "loved"
    FAVOURITES = "favourites"
    PENDING = "pending"
    WIP = "wip"
    GRAVEYARD = "graveyard"
    MY_MAPS = "mine"


class BeatmapsetSearchMode(EnumModel):
    # made up value. this is the default option and doesn't cause a value to
    # appear in the query string.
    ANY = -1
    OSU = 0
    TAIKO = 1
    CATCH = 2
    MANIA = 3


class BeatmapsetSearchExplicitContent(EnumModel):
    HIDE = "hide"
    SHOW = "show"


class BeatmapsetSearchGenre(EnumModel):
    # default option, made up value
    ANY = 0
    UNSPECIFIED = 1
    VIDEO_GAME = 2
    ANIME = 3
    ROCK = 4
    POP = 5
    OTHER = 6
    NOVELTY = 7
    HIP_HOP = 9
    ELECTRONIC = 10
    METAL = 11
    CLASSICAL = 12
    FOLK = 13
    JAZZ = 14


class BeatmapsetSearchLanguage(EnumModel):
    # default option, made up value
    ANY = 0
    UNSPECIFIED = 1
    ENGLISH = 2
    JAPANESE = 3
    CHINESE = 4
    INSTRUMENTAL = 5
    KOREAN = 6
    FRENCH = 7
    GERMAN = 8
    SWEDISH = 9
    SPANISH = 10
    ITALIAN = 11
    RUSSIAN = 12
    POLISH = 13
    OTHER = 14


class BeatmapsetSearchSort(EnumModel):
    TITLE_DESCENDING = "title_desc"
    TITLE_ASCENDING = "title_asc"

    ARTIST_DESCENDING = "artist_desc"
    ARTIST_ASCENDING = "artist_asc"

    DIFFICULTY_DESCENDING = "difficulty_desc"
    DIFFICULTY_ASCENDING = "difficulty_asc"

    RANKED_DESCENDING = "ranked_desc"
    RANKED_ASCENDING = "ranked_asc"

    RATING_DESCENDING = "rating_desc"
    RATING_ASCENDING = "rating_asc"

    PLAYS_DESCENDING = "plays_desc"
    PLAYS_ASCENDING = "plays_asc"

    FAVORITES_DESCENDING = "favourites_desc"
    FAVORITES_ASCENDING = "favourites_asc"


class NewsPostKey(EnumModel):
    SLUG = "slug"
    ID = "id"


# `RoomType` is already taken as a model name (and more appropriate elsewhere)
class RoomSearchMode(EnumModel):
    ACTIVE = "active"
    ALL = "all"
    ENDED = "ended"
    PARTICIPATED = "participated"
    OWNED = "owned"


class EventsSort(EnumModel):
    NEW = "id_desc"
    OLD = "id_asc"


class BeatmapPackType(EnumModel):
    STANDARD = "standard"
    FEATURED = "featured"
    TOURNAMENT = "tournament"
    LOVED = "loved"
    CHART = "chart"
    THEME = "theme"
    ARTIST = "artist"


# =================
# Documented Models
# =================


class Failtimes(Model):
    exit: Optional[List[int]]
    fail: Optional[List[int]]


class Ranking(Model):
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/CountryTransformer.php#L30
    active_users: int
    play_count: int
    ranked_score: int
    performance: int


class Country(Model):
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/CountryTransformer.php#L10
    code: str
    name: str

    # optional fields
    # ---------------
    display: Optional[int]
    ranking: Optional[Ranking]


class Cover(Model):
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserCompactTransformer.php#L158
    custom_url: Optional[str]
    url: str
    # api should really return an int here instead...open an issue?
    id: Optional[str]


class ProfileBanner(Model):
    id: int
    tournament_id: int
    image: str
    image_2x: Field(name="image@2x", type=str)


class UserAccountHistory(Model):
    description: Optional[str]
    id: int
    length: int
    permanent: bool
    timestamp: Datetime
    type: UserAccountHistoryType


class UserBadge(Model):
    awarded_at: Datetime
    description: str
    image_url: str
    image_2x_url: Field(name="image@2x_url", type=str)
    url: str


class GroupDescription(Model):
    html: str
    markdown: str


class UserGroup(Model):
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserGroupTransformer.php#L10
    id: int
    identifier: str
    name: str
    short_name: str
    colour: Optional[str]
    description: Optional[GroupDescription]
    playmodes: Optional[List[GameMode]]
    is_probationary: bool
    has_listing: bool
    has_playmodes: bool


class Covers(Model):
    """
    https://osu.ppy.sh/docs/index.html#beatmapsetcompact-covers
    """

    cover: str
    cover_2x: Field(name="cover@2x", type=str)
    card: str
    card_2x: Field(name="card@2x", type=str)
    list: str
    list_2x: Field(name="list@2x", type=str)
    slimcover: str
    slimcover_2x: Field(name="slimcover@2x", type=str)


class _LegacyStatistics(Model):
    # I think any of these attributes can be null if the corresponding gamemode
    # doesn't have the judgment as a possible judgement. eg taiko doesn't have 50s
    # and catch doesn't have geki.
    count_50: Optional[int]
    count_100: Optional[int]
    count_300: Optional[int]
    count_geki: Optional[int]
    count_katu: Optional[int]
    count_miss: Optional[int]


class Statistics(Model):
    # these values simply aren't present if they are 0. oversight?
    miss: Optional[int]
    meh: Optional[int]
    ok: Optional[int]
    good: Optional[int]
    great: Optional[int]

    # TODO: are these weird values returned by the api anywhere?
    # e.g. legacy_combo_increase in particular.
    perfect: Optional[int]
    small_tick_miss: Optional[int]
    small_tick_hit: Optional[int]
    large_tick_miss: Optional[int]
    large_tick_hit: Optional[int]
    small_bonus: Optional[int]
    large_bonus: Optional[int]
    ignore_miss: Optional[int]
    ignore_hit: Optional[int]
    combo_break: Optional[int]
    slider_tail_hit: Optional[int]
    legacy_combo_increase: Optional[int]

    @staticmethod
    def override_attributes(data, api):
        if api.api_version < 20220705:
            return _LegacyStatistics

        # see note in Score.override_attributes for when this exception of legacy
        # statistics even on new api versions can occur.
        if (
            any(
                f"count_{v}" in data
                for v in ["50", "100", "300", "geki", "katu", "miss"]
            )
            and "great" not in data
        ):
            return _LegacyStatistics


class Availability(Model):
    download_disabled: bool
    more_information: Optional[str]


class Hype(Model):
    current: int
    required: int


class NominationsRequired(Model):
    main_ruleset: int
    non_main_ruleset: int


class Nominations(Model):
    current: int
    required_meta: NominationsRequired
    eligible_main_rulesets: Optional[List[GameMode]]


class Nomination(Model):
    beatmapset_id: int
    rulesets: List[GameMode]
    reset: bool
    user_id: int


class Kudosu(Model):
    total: int
    available: int


class KudosuGiver(Model):
    url: str
    username: str


class KudosuPost(Model):
    url: Optional[str]
    # will be "[deleted beatmap]" for deleted beatmaps. See
    # https://osu.ppy.sh/docs/index.html#kudosuhistory
    title: str


class KudosuVote(Model):
    user_id: int
    score: int

    def user(self):
        return self._fk_user(self.user_id)


class EventUser(Model):
    username: str
    url: str
    previousUsername: Optional[str]


class EventBeatmap(Model):
    title: str
    url: str


class EventBeatmapset(Model):
    title: str
    url: str


class EventAchivement(Model):
    icon_url: str
    id: int
    name: str
    # TODO `grouping` can probably be enumified (example value: "Dedication"),
    # need to find full list first though
    grouping: str
    ordering: int
    slug: str
    description: str
    mode: Optional[GameMode]
    instructions: Optional[Any]


class GithubUser(Model):
    display_name: str
    github_username: Optional[str]
    github_url: Optional[str]
    id: Optional[int]
    osu_username: Optional[str]
    user_id: Optional[int]
    user_url: Optional[str]

    def user(self):
        return self._fk_user(self.user_id)


class ChangelogSearch(Model):
    from_: Field(name="from", type=Optional[str])
    limit: int
    max_id: Optional[int]
    stream: Optional[str]
    to: Optional[str]


class NewsSearch(Model):
    limit: int
    sort: str
    # undocumented
    year: Optional[int]


class ForumPostBody(Model):
    html: str
    raw: str


class ForumPollText(Model):
    bbcode: str
    html: str


class ForumPollTitle(Model):
    bbcode: str
    html: str


class ReviewsConfig(Model):
    max_blocks: int


class RankHighest(Model):
    rank: int
    updated_at: Datetime


class BeatmapPackUserCompletionData(Model):
    beatmapset_ids: List[int]
    completed: bool


# ===================
# Undocumented Models
# ===================


class UserMonthlyPlaycount(Model):
    # undocumented
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserMonthlyPlaycountTransformer.php
    start_date: Datetime
    count: int


class UserPage(Model):
    # undocumented (and not a class on osu-web)
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserCompactTransformer.php#L270
    html: str
    raw: str


class UserLevel(Model):
    # undocumented (and not a class on osu-web)
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserStatisticsTransformer.php#L27
    current: int
    progress: int


class UserGradeCounts(Model):
    # undocumented (and not a class on osu-web)
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserStatisticsTransformer.php#L43
    ss: int
    ssh: int
    s: int
    sh: int
    a: int


class UserReplaysWatchedCount(Model):
    # undocumented
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserReplaysWatchedCountTransformer.php
    start_date: Datetime
    count: int


class UserAchievement(Model):
    # undocumented
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserAchievementTransformer.php#L10
    achieved_at: Datetime
    achievement_id: int


class UserProfileCustomization(Model):
    # undocumented
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserCompactTransformer.php#L363
    # https://github.com/ppy/osu-web/blob/master/app/Models/UserProfileCustomization.php
    audio_autoplay: Optional[bool]
    audio_muted: Optional[bool]
    audio_volume: Optional[int]
    beatmapset_download: Optional[BeatmapsetDownload]
    beatmapset_show_nsfw: Optional[bool]
    beatmapset_title_show_original: Optional[bool]
    comments_show_deleted: Optional[bool]
    forum_posts_show_deleted: bool
    ranking_expanded: bool
    user_list_filter: Optional[UserListFilters]
    user_list_sort: Optional[UserListSorts]
    user_list_view: Optional[UserListViews]


class RankHistory(Model):
    # undocumented
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/RankHistoryTransformer.php
    mode: GameMode
    data: List[int]


class Weight(Model):
    percentage: float
    pp: float


class RoomPlaylistItemStats(Model):
    count_active: int
    count_total: int
    ruleset_ids: List[int]


class RoomDifficultyRange(Model):
    min: float
    max: float
