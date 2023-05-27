# opt-in to forward type annotations
# https://docs.python.org/3.7/whatsnew/3.7.html#pep-563-postponed-evaluation-
# of-annotations
from __future__ import annotations
from typing import Optional, TypeVar, Generic, Any, List, Union, Dict
from dataclasses import dataclass

from ossapi.mod import Mod
from ossapi.enums import (UserAccountHistory, ProfileBanner, UserBadge, Country,
    Cover, UserGroup, UserMonthlyPlaycount, UserPage, UserReplaysWatchedCount,
    UserAchievement, UserProfileCustomization, RankHistory, Kudosu, PlayStyles,
    ProfilePage, GameMode, RankStatus, Failtimes, Covers, Hype, Availability,
    Nominations, Statistics, Grade, Weight, MessageType, KudosuAction,
    KudosuGiver, KudosuPost, EventType, EventAchivement, EventUser,
    EventBeatmap, BeatmapsetApproval, EventBeatmapset, KudosuVote,
    BeatmapsetEventType, UserRelationType, UserLevel, UserGradeCounts,
    GithubUser, ChangelogSearch, ForumTopicType, ForumPostBody, ForumTopicSort,
    ChannelType, ReviewsConfig, NewsSearch, Nomination, RankHighest, RoomType,
    RoomCategory, MatchEventType, ScoringType, TeamType)
from ossapi.utils import Datetime, Model, BaseModel, Field

T = TypeVar("T")
S = TypeVar("S")

"""
a type hint of ``Optional[Any]`` or ``Any`` means that I don't know what type it
is, not that the api actually lets any type be returned there.
"""

# =================
# Documented Models
# =================

# the weird location of the cursor class and `CursorT` definition is to remove
# the need for forward type annotations, which breaks typing_utils when they
# try to evaluate the forwardref (as the `Cursor` class is not in scope at that
# moment). We would be able to fix this by manually passing forward refs to the
# lib instead, but I don't want to have to keep track of which forward refs need
# passing and which don't, or which classes I need to import in various files
# (it's not as simple as just sticking a `global()` call in and calling it a
# day). So I'm just going to ban forward refs in the codebase for now, until we
# want to drop typing_utils (and thus support for python 3.8 and lower).
# It's also possible I'm missing an obvious fix for this, but I suspect this is
# a limitation of older python versions.

# Cursors are an interesting case. As I understand it, they don't have a
# predefined set of attributes across all endpoints, but instead differ per
# endpoint. I don't want to have dozens of different cursor classes (although
# that would perhaps be the proper way to go about this), so just allow
# any attribute.
# This is essentially a reimplementation of SimpleNamespace to deal with
# BaseModels being passed the data as a single dict (`_data`) instead of as
# **kwargs, plus some other weird stuff we're doing like handling cursor
# objects being passed as data
# We want cursors to also be instantiatable manually (eg `Cursor(page=199)`),
# so make `_data` optional and also allow arbitrary `kwargs`.

class Cursor(BaseModel):
    def __init__(self, _data=None, **kwargs):
        super().__init__()
        # allow Cursor to be instantiated with another cursor as a no-op
        if isinstance(_data, Cursor):
            _data = _data.__dict__
        _data = _data or kwargs
        self.__dict__.update(_data)

    def __repr__(self):
        keys = sorted(self.__dict__)
        items = (f"{k}={self.__dict__[k]!r}" for k in keys)
        return f"{type(self).__name__}({', '.join(items)})"

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

# if there are no more results, a null cursor is returned instead.
# So always let the cursor be nullable to catch this. It's the user's
# responsibility to check for a null cursor to see if there are any more
# results.
CursorT = Optional[Cursor]

class UserCompact(Model):
    """
    https://osu.ppy.sh/docs/index.html#usercompact
    """
    # required fields
    # ---------------
    avatar_url: str
    country_code: str
    default_group: str
    id: int
    is_active: bool
    is_bot: bool
    is_deleted: bool
    is_online: bool
    is_supporter: bool
    last_visit: Optional[Datetime]
    pm_friends_only: bool
    profile_colour: Optional[str]
    username: str

    # optional fields
    # ---------------
    account_history: Optional[List[UserAccountHistory]]
    active_tournament_banner: Optional[ProfileBanner]
    badges: Optional[List[UserBadge]]
    beatmap_playcounts_count: Optional[int]
    blocks: Optional[UserRelation]
    country: Optional[Country]
    cover: Optional[Cover]
    favourite_beatmapset_count: Optional[int]
    # undocumented
    follow_user_mapping: Optional[List[int]]
    follower_count: Optional[int]
    friends: Optional[List[UserRelation]]
    graveyard_beatmapset_count: Optional[int]
    groups: Optional[List[UserGroup]]
    # undocumented
    guest_beatmapset_count: Optional[int]
    is_admin: Optional[bool]
    is_bng: Optional[bool]
    is_full_bn: Optional[bool]
    is_gmt: Optional[bool]
    is_limited_bn: Optional[bool]
    is_moderator: Optional[bool]
    is_nat: Optional[bool]
    is_restricted: Optional[bool]
    is_silenced: Optional[bool]
    loved_beatmapset_count: Optional[int]
    # undocumented
    mapping_follower_count: Optional[int]
    monthly_playcounts: Optional[List[UserMonthlyPlaycount]]
    page: Optional[UserPage]
    previous_usernames: Optional[List[str]]
    # deprecated, replaced by ranked_beatmapset_count
    ranked_and_approved_beatmapset_count: Optional[int]
    ranked_beatmapset_count: Optional[int]
    replays_watched_counts: Optional[List[UserReplaysWatchedCount]]
    scores_best_count: Optional[int]
    scores_first_count: Optional[int]
    scores_recent_count: Optional[int]
    statistics: Optional[UserStatistics]
    statistics_rulesets: Optional[UserStatisticsRulesets]
    support_level: Optional[int]
    # deprecated, replaced by pending_beatmapset_count
    unranked_beatmapset_count: Optional[int]
    pending_beatmapset_count: Optional[int]
    unread_pm_count: Optional[int]
    user_achievements: Optional[List[UserAchievement]]
    user_preferences: Optional[UserProfileCustomization]
    rank_history: Optional[RankHistory]
    # deprecated, replaced by rank_history
    rankHistory: Optional[RankHistory]

    def expand(self) -> User:
        return self._fk_user(self.id)

class User(UserCompact):
    comments_count: int
    cover_url: str
    discord: Optional[str]
    has_supported: bool
    interests: Optional[str]
    join_date: Datetime
    kudosu: Kudosu
    location: Optional[str]
    max_blocks: int
    max_friends: int
    occupation: Optional[str]
    playmode: str
    playstyle: Optional[PlayStyles]
    post_count: int
    profile_order: List[ProfilePage]
    title: Optional[str]
    title_url: Optional[str]
    twitter: Optional[str]
    website: Optional[str]
    scores_pinned_count: int
    nominated_beatmapset_count: int
    rank_highest: Optional[RankHighest]

    def expand(self) -> User:
        # we're already expanded, no need to waste an api call
        return self


class BeatmapCompact(Model):
    # required fields
    # ---------------
    difficulty_rating: float
    id: int
    mode: GameMode
    status: RankStatus
    total_length: int
    version: str
    user_id: int
    beatmapset_id: int

    # optional fields
    # ---------------
    _beatmapset: Optional[BeatmapsetCompact] = Field(name="beatmapset")
    checksum: Optional[str]
    failtimes: Optional[Failtimes]
    max_combo: Optional[int]

    def expand(self) -> Beatmap:
        return self._fk_beatmap(self.id)

    def user(self) -> User:
        return self._fk_user(self.user_id)

    def beatmapset(self) -> Union[Beatmapset, BeatmapsetCompact]:
        return self._fk_beatmapset(self.beatmapset_id,
            existing=self._beatmapset)

class Beatmap(BeatmapCompact):
    total_length: int
    version: str
    accuracy: float
    ar: float
    bpm: Optional[float]
    convert: bool
    count_circles: int
    count_sliders: int
    count_spinners: int
    cs: float
    deleted_at: Optional[Datetime]
    drain: float
    hit_length: int
    is_scoreable: bool
    last_updated: Datetime
    mode_int: int
    passcount: int
    playcount: int
    ranked: RankStatus
    url: str
    # user associated with this difficulty (ie diff mapper / owner).
    # Returned as `user` in the api, but that conflicts with our fk method for
    # beatmapset owner.
    # This is optional as a workaround until
    # https://github.com/ppy/osu-web/issues/9784 is resolved.
    owner: Optional[UserCompact] = Field(name="user")

    # overridden fields
    # -----------------
    _beatmapset: Optional[Beatmapset] = Field(name="beatmapset")

    def expand(self) -> Beatmap:
        return self

    def beatmapset(self) -> Beatmapset:
        return self._fk_beatmapset(self.beatmapset_id,
            existing=self._beatmapset)


class BeatmapsetCompact(Model):
    """
    https://osu.ppy.sh/docs/index.html#beatmapsetcompact
    """
    # required fields
    # ---------------
    artist: str
    artist_unicode: str
    covers: Covers
    creator: str
    favourite_count: int
    id: int
    play_count: int
    preview_url: str
    source: str
    status: RankStatus
    title: str
    title_unicode: str
    user_id: int
    video: bool
    nsfw: bool
    offset: int
    spotlight: bool
    # documented as being in `Beatmapset` only, but returned by
    # `api.beatmapset_events` which uses a `BeatmapsetCompact`.
    hype: Optional[Hype]

    # optional fields
    # ---------------
    beatmaps: Optional[List[Beatmap]]
    converts: Optional[Any]
    current_user_attributes: Optional[Any]
    description: Optional[Any]
    discussions: Optional[Any]
    events: Optional[Any]
    genre: Optional[Any]
    has_favourited: Optional[bool]
    language: Optional[Any]
    nominations: Optional[Any]
    ratings: Optional[Any]
    recent_favourites: Optional[Any]
    related_users: Optional[Any]
    _user: Optional[UserCompact] = Field(name="user")
    # undocumented
    track_id: Optional[int]

    def expand(self) -> Beatmapset:
        return self._fk_beatmapset(self.id)

    def user(self) -> Union[UserCompact, User]:
        return self._fk_user(self.user_id, existing=self._user)

class Beatmapset(BeatmapsetCompact):
    availability: Availability
    bpm: float
    can_be_hyped: bool
    discussion_enabled: bool
    discussion_locked: bool
    is_scoreable: bool
    last_updated: Datetime
    legacy_thread_url: Optional[str]
    nominations_summary: Nominations
    ranked: RankStatus
    ranked_date: Optional[Datetime]
    storyboard: bool
    submitted_date: Optional[Datetime]
    tags: str
    current_nominations: Optional[List[Nomination]]
    deleted_at: Optional[Datetime]
    pack_tags: List[str]

    def expand(self) -> Beatmapset:
        return self

# undocumented, but defined here to avoid a forward reference in Score.
class ScoreMatchInfo(Model):
    slot: int
    team: str
    pass_: bool = Field(name="pass")

class Score(Model):
    """
    https://osu.ppy.sh/docs/index.html#score
    """
    # can be null for match scores, eg the scores
    # in https://osu.ppy.sh/community/matches/97947404
    id: Optional[int]
    best_id: Optional[int]
    user_id: int
    accuracy: float
    mods: Mod
    score: int
    max_combo: int
    perfect: bool
    statistics: Statistics
    pp: Optional[float]
    rank: Grade
    created_at: Datetime
    mode: GameMode
    mode_int: int
    replay: bool
    passed: bool
    current_user_attributes: Any

    beatmap: Optional[Beatmap]
    beatmapset: Optional[BeatmapsetCompact]
    rank_country: Optional[int]
    rank_global: Optional[int]
    weight: Optional[Weight]
    _user: Optional[UserCompact] = Field(name="user")
    match: Optional[ScoreMatchInfo]
    type: str

    @classmethod
    def preprocess_data(cls, data):
        # scores from matches (api.match) return perfect as an int instead of a
        # bool (same as api v1). Convert to a bool here.
        if isinstance(data["perfect"], int):
            data["perfect"] = bool(data["perfect"])
        return data

    def user(self) -> Union[UserCompact, User]:
        return self._fk_user(self.user_id, existing=self._user)

    def download(self):
        return self._api.download_score(self.mode, self.id)

class BeatmapUserScore(Model):
    position: int
    score: Score

class BeatmapUserScores(Model):
    scores: List[Score]

class BeatmapScores(Model):
    scores: List[Score]
    userScore: Optional[BeatmapUserScore]


class CommentableMeta(Model):
    # title is the only attribute returned for deleted commentables.
    id: Optional[int]
    title: str
    type: Optional[str]
    url: Optional[str]
    owner_id: Optional[int]
    owner_title: Optional[str]
    current_user_attributes: Optional[CommentableMetaCurrentUserAttributes]

class CommentableMetaCurrentUserAttributes(Model):
    can_new_comment_reason: Optional[str]

class Comment(Model):
    # null for deleted commentables, eg on /comments/3.
    commentable_id: Optional[int]
    # null for deleted commentables, eg on /comments/3.
    commentable_type: Optional[str]
    created_at: Datetime
    deleted_at: Optional[Datetime]
    edited_at: Optional[Datetime]
    edited_by_id: Optional[int]
    id: int
    legacy_name: Optional[str]
    message: Optional[str]
    message_html: Optional[str]
    parent_id: Optional[int]
    pinned: bool
    replies_count: int
    updated_at: Datetime
    # null for some commentables, eg on /comments/3.
    user_id: Optional[int]
    votes_count: int

    def user(self) -> User:
        return self._fk_user(self.user_id)

    def edited_by(self) -> Optional[User]:
        return self._fk_user(self.edited_by_id)

class CommentBundle(Model):
    commentable_meta: List[CommentableMeta]
    comments: List[Comment]
    has_more: bool
    has_more_id: Optional[int]
    included_comments: List[Comment]
    pinned_comments: Optional[List[Comment]]
    sort: str
    top_level_count: Optional[int]
    total: Optional[int]
    user_follow: bool
    user_votes: List[int]
    users: List[UserCompact]
    # undocumented
    cursor: CursorT

class ForumPost(Model):
    created_at: Datetime
    deleted_at: Optional[Datetime]
    edited_at: Optional[Datetime]
    edited_by_id: Optional[int]
    forum_id: int
    id: int
    topic_id: int
    user_id: int
    body: ForumPostBody

    def user(self) -> User:
        return self._fk_user(self.user_id)

    def edited_by(self) -> Optional[User]:
        return self._fk_user(self.edited_by_id)

class ForumTopic(Model):
    created_at: Datetime
    deleted_at: Optional[Datetime]
    first_post_id: int
    forum_id: int
    id: int
    is_locked: bool
    last_post_id: int
    post_count: int
    title: str
    type: ForumTopicType
    updated_at: Datetime
    user_id: int
    poll: Any

    def user(self) -> User:
        return self._fk_user(self.user_id)

class ForumTopicAndPosts(Model):
    cursor: CursorT
    search: ForumTopicSearch
    posts: List[ForumPost]
    topic: ForumTopic
    cursor_string: Optional[str]

class CreateForumTopicResponse(Model):
    post: ForumPost
    topic: ForumTopic

class ForumTopicSearch(Model):
    sort: Optional[ForumTopicSort]
    limit: Optional[int]
    start: Optional[int]
    end: Optional[int]

class SearchResult(Generic[T], Model):
    data: List[T]
    total: int

class WikiPage(Model):
    layout: str
    locale: str
    markdown: str
    path: str
    subtitle: Optional[str]
    tags: List[str]
    title: str
    available_locales: List[str]

class Search(Model):
    users: Optional[SearchResult[UserCompact]] = Field(name="user")
    wiki_pages: Optional[SearchResult[WikiPage]] = Field(name="wiki_page")

class Spotlight(Model):
    end_date: Datetime
    id: int
    mode_specific: bool
    participant_count: Optional[int]
    name: str
    start_date: Datetime
    type: str

class Spotlights(Model):
    spotlights: List[Spotlight]

# return-value wrapper for https://osu.ppy.sh/docs/index.html#get-users.
class Users(Model):
    users: List[UserCompact]

# return-value wrapper for https://osu.ppy.sh/docs/index.html#get-beatmaps.
class Beatmaps(Model):
    beatmaps: List[Beatmap]

class Rankings(Model):
    beatmapsets: Optional[List[Beatmapset]]
    cursor: CursorT
    ranking: List[UserStatistics]
    spotlight: Optional[Spotlight]
    total: int

class BeatmapsetDiscussionPost(Model):
    id: int
    beatmapset_discussion_id: int
    user_id: int
    last_editor_id: Optional[int]
    deleted_by_id: Optional[int]
    system: bool
    message: str
    created_at: Datetime
    updated_at: Datetime
    deleted_at: Optional[Datetime]

    def user(self) -> user:
        return self._fk_user(self.user_id)

    def last_editor(self) -> Optional[User]:
        return self._fk_user(self.last_editor_id)

    def deleted_by(self) -> Optional[User]:
        return self._fk_user(self.deleted_by_id)

class BeatmapsetDiscussion(Model):
    id: int
    beatmapset_id: int
    beatmap_id: Optional[int]
    user_id: int
    deleted_by_id: Optional[int]
    message_type: MessageType
    parent_id: Optional[int]
    # a point of time which is ``timestamp`` milliseconds into the map
    timestamp: Optional[int]
    resolved: bool
    can_be_resolved: bool
    can_grant_kudosu: bool
    created_at: Datetime
    # documented as non-optional, api.beatmapset_events() might give a null
    # response for this? but very rarely. need to find a repro case
    current_user_attributes: Any
    updated_at: Datetime
    deleted_at: Optional[Datetime]
    # similarly as for current_user_attributes, in the past this has been null
    # but can't find a repro case
    last_post_at: Datetime
    kudosu_denied: bool
    starting_post: Optional[BeatmapsetDiscussionPost]
    posts: Optional[List[BeatmapsetDiscussionPost]]
    _beatmap: Optional[BeatmapCompact] = Field(name="beatmap")
    _beatmapset: Optional[BeatmapsetCompact] = Field(name="beatmapset")

    def user(self) -> User:
        return self._fk_user(self.user_id)

    def deleted_by(self) -> Optional[User]:
        return self._fk_user(self.deleted_by_id)

    def beatmapset(self) -> Union[Beatmapset, BeatmapsetCompact]:
        return self._fk_beatmapset(self.beatmapset_id,
            existing=self._beatmapset)

    def beatmap(self) -> Union[Optional[Beatmap], BeatmapCompact]:
        return self._fk_beatmap(self.beatmap_id, existing=self._beatmap)

class BeatmapsetDiscussionVote(Model):
    id: int
    score: int
    user_id: int
    beatmapset_discussion_id: int
    created_at: Datetime
    updated_at: Datetime
    cursor_string: Optional[str]

    def user(self):
        return self._fk_user(self.user_id)

class KudosuHistory(Model):
    id: int
    action: KudosuAction
    amount: int
    # TODO enumify this. Described as "Object type which the exchange happened
    # on (forum_post, etc)." in https://osu.ppy.sh/docs/index.html#kudosuhistory
    model: str
    created_at: Datetime
    giver: Optional[KudosuGiver]
    post: KudosuPost
    # see https://github.com/ppy/osu-web/issues/7549
    details: Any

class BeatmapPlaycount(Model):
    beatmap_id: int
    _beatmap: Optional[BeatmapCompact] = Field(name="beatmap")
    beatmapset: Optional[BeatmapsetCompact]
    count: int

    def beatmap(self) -> Union[Beatmap, BeatmapCompact]:
        return self._fk_beatmap(self.beatmap_id, existing=self._beatmap)


# we use this class to determine which event dataclass to instantiate and
# return, based on the value of the ``type`` parameter.
class _Event(Model):
    @classmethod
    def override_class(cls, data):
        mapping = {
            EventType.ACHIEVEMENT: AchievementEvent,
            EventType.BEATMAP_PLAYCOUNT: BeatmapPlaycountEvent,
            EventType.BEATMAPSET_APPROVE: BeatmapsetApproveEvent,
            EventType.BEATMAPSET_DELETE: BeatmapsetDeleteEvent,
            EventType.BEATMAPSET_REVIVE: BeatmapsetReviveEvent,
            EventType.BEATMAPSET_UPDATE: BeatmapsetUpdateEvent,
            EventType.BEATMAPSET_UPLOAD: BeatmapsetUploadEvent,
            EventType.RANK: RankEvent,
            EventType.RANK_LOST: RankLostEvent,
            EventType.USER_SUPPORT_FIRST: UserSupportFirstEvent,
            EventType.USER_SUPPORT_AGAIN: UserSupportAgainEvent,
            EventType.USER_SUPPORT_GIFT: UserSupportGiftEvent,
            EventType.USERNAME_CHANGE: UsernameChangeEvent
        }
        type_ = EventType(data["type"])
        return mapping[type_]

class Event(Model):
    created_at: Datetime
    createdAt: Datetime
    id: int
    type: EventType

class AchievementEvent(Event):
    achievement: EventAchivement
    user: EventUser

class BeatmapPlaycountEvent(Event):
    beatmap: EventBeatmap
    count: int

class BeatmapsetApproveEvent(Event):
    approval: BeatmapsetApproval
    beatmapset: EventBeatmapset
    user: EventUser

class BeatmapsetDeleteEvent(Event):
    beatmapset: EventBeatmapset

class BeatmapsetReviveEvent(Event):
    beatmapset: EventBeatmapset
    user: EventUser

class BeatmapsetUpdateEvent(Event):
    beatmapset: EventBeatmapset
    user: EventUser

class BeatmapsetUploadEvent(Event):
    beatmapset: EventBeatmapset
    user: EventUser

class RankEvent(Event):
    scoreRank: str
    rank: int
    mode: GameMode
    beatmap: EventBeatmap
    user: EventUser

class RankLostEvent(Event):
    mode: GameMode
    beatmap: EventBeatmap
    user: EventUser

class UserSupportFirstEvent(Event):
    user: EventUser

class UserSupportAgainEvent(Event):
    user: EventUser

class UserSupportGiftEvent(Event):
    beatmap: EventBeatmap

class UsernameChangeEvent(Event):
    user: EventUser

class Build(Model):
    created_at: Datetime
    display_version: str
    id: int
    update_stream: Optional[UpdateStream]
    users: int
    version: Optional[str]
    changelog_entries: Optional[List[ChangelogEntry]]
    versions: Optional[Versions]

class Versions(Model):
    next: Optional[Build]
    previous: Optional[Build]

class UpdateStream(Model):
    display_name: Optional[str]
    id: int
    is_featured: bool
    name: str
    latest_build: Optional[Build]
    user_count: Optional[int]

class ChangelogEntry(Model):
    category: str
    created_at: Optional[Datetime]
    github_pull_request_id: Optional[int]
    github_url: Optional[str]
    id: Optional[int]
    major: bool
    message: Optional[str]
    message_html: Optional[str]
    repository: Optional[str]
    title: Optional[str]
    type: str
    url: Optional[str]
    github_user: GithubUser

class ChangelogListing(Model):
    builds: List[Build]
    search: ChangelogSearch
    streams: List[UpdateStream]

class MultiplayerScores(Model):
    cursor_string: str
    params: str
    scores: List[MultiplayerScore]
    total: Optional[int]
    user_score: Optional[MultiplayerScore]

class MultiplayerScore(Model):
    id: int
    user_id: int
    room_id: int
    playlist_item_id: int
    beatmap_id: int
    rank: int
    total_score: int
    max_combo: int
    mods: List[Mod]
    statistics: Statistics
    passed: bool
    position: Optional[int]
    scores_around: Optional[MultiplayerScoresAround]
    user: User

    def beatmap(self):
        return self._fk_beatmap(self.beatmap_id)

class MultiplayerScoresAround(Model):
    higher: List[MultiplayerScore]
    lower: List[MultiplayerScore]

class NewsListing(Model):
    cursor: CursorT
    cursor_string: str
    news_posts: List[NewsPost]
    news_sidebar: NewsSidebar
    search: NewsSearch

class NewsPost(Model):
    author: str
    edit_url: str
    first_image: Optional[str]
    id: int
    published_at: Datetime
    slug: str
    title: str
    updated_at: Datetime
    content: Optional[str]
    navigation: Optional[NewsNavigation]
    preview: Optional[str]

class NewsNavigation(Model):
    newer: Optional[NewsPost]
    older: Optional[NewsPost]

class NewsSidebar(Model):
    current_year: int
    news_posts: List[NewsPost]
    years: List[int]

class SeasonalBackgrounds(Model):
    ends_at: Datetime
    backgrounds: List[SeasonalBackground]

class SeasonalBackground(Model):
    url: str
    user: UserCompact

class DifficultyAttributes(Model):
    attributes: BeatmapDifficultyAttributes

class BeatmapDifficultyAttributes(Model):
    max_combo: int
    star_rating: float

    # osu attributes
    aim_difficulty: Optional[float]
    approach_rate: Optional[float]
    flashlight_difficulty: Optional[float]
    overall_difficulty: Optional[float]
    slider_factor: Optional[float]
    speed_difficulty: Optional[float]
    speed_note_count: Optional[float]

    # taiko attributes
    stamina_difficulty: Optional[float]
    rhythm_difficulty: Optional[float]
    colour_difficulty: Optional[float]
    approach_raty: Optional[float]
    great_hit_windoy: Optional[float]

    # ctb attributes
    approach_rate: Optional[float]

    # mania attributes
    great_hit_window: Optional[float]
    score_multiplier: Optional[float]



# ================
# Parameter Models
# ================

# models which aren't used for serialization, but passed to OssapiV2 methods.

@dataclass
class ForumPoll:
    options: List[str]
    title: str

    # default values taken from https://osu.ppy.sh/docs/index.html#create-topic
    hide_results: bool = False
    length_days: int = 0
    max_options: int = 1
    vote_change: bool = False



# ===================
# Undocumented Models
# ===================

class BeatmapsetSearchResult(Model):
    beatmapsets: List[Beatmapset]
    cursor: CursorT
    recommended_difficulty: Optional[float]
    error: Optional[str]
    total: int
    search: Any
    cursor_string: Optional[str]

class BeatmapsetDiscussions(Model):
    beatmaps: List[Beatmap]
    cursor: CursorT
    discussions: List[BeatmapsetDiscussion]
    included_discussions: List[BeatmapsetDiscussion]
    reviews_config: ReviewsConfig
    users: List[UserCompact]
    cursor_string: Optional[str]
    beatmapsets: List[Beatmapset]

class BeatmapsetDiscussionReview(Model):
    # https://github.com/ppy/osu-web/blob/master/app/Libraries/BeatmapsetDis
    # cussionReview.php
    max_blocks: int

class BeatmapsetDiscussionPosts(Model):
    beatmapsets: List[BeatmapsetCompact]
    discussions: List[BeatmapsetDiscussion]
    cursor: CursorT
    posts: List[BeatmapsetDiscussionPost]
    users: List[UserCompact]
    cursor_string: Optional[str]

class BeatmapsetDiscussionVotes(Model):
    cursor: CursorT
    discussions: List[BeatmapsetDiscussion]
    votes: List[BeatmapsetDiscussionVote]
    users: List[UserCompact]
    cursor_string: Optional[str]

class BeatmapsetEventComment(Model):
    beatmap_discussion_id: int
    beatmap_discussion_post_id: int

class BeatmapsetEventCommentNoPost(Model):
    beatmap_discussion_id: int
    beatmap_discussion_post_id: None

class BeatmapsetEventCommentNone(Model):
    beatmap_discussion_id: None
    beatmap_discussion_post_id: None


class BeatmapsetEventCommentChange(Generic[S], BeatmapsetEventCommentNone):
    old: S
    new: S

class BeatmapsetEventCommentLovedRemoval(BeatmapsetEventCommentNone):
    reason: str

class BeatmapsetEventCommentKudosuChange(BeatmapsetEventCommentNoPost):
    new_vote: KudosuVote
    votes: List[KudosuVote]

class BeatmapsetEventCommentKudosuRecalculate(BeatmapsetEventCommentNoPost):
    new_vote: Optional[KudosuVote]

class BeatmapsetEventCommentOwnerChange(BeatmapsetEventCommentNone):
    beatmap_id: int
    beatmap_version: str
    new_user_id: int
    new_user_username: str

class BeatmapsetEventCommentNominate(Model):
    # for some reason this comment type doesn't have the normal
    # beatmap_discussion_id and beatmap_discussion_post_id attributes (they're
    # not even null, just missing).
    modes: List[GameMode]

class BeatmapsetEventCommentWithNominators(BeatmapsetEventCommentNoPost):
    nominator_ids: Optional[List[int]]

class BeatmapsetEventCommentWithSourceUser(BeatmapsetEventCommentNoPost):
    source_user_id: int
    source_user_username: str

class BeatmapsetEvent(Model):
    # https://github.com/ppy/osu-web/blob/master/app/Models/BeatmapsetEvent.php
    #
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/BeatmapsetEv
    # entTransformer.php

    id: int
    type: BeatmapsetEventType
    comment: str
    created_at: Datetime

    user_id: Optional[int]
    beatmapset: Optional[BeatmapsetCompact]
    discussion: Optional[BeatmapsetDiscussion]

    def override_types(self):
        mapping = {
            BeatmapsetEventType.BEATMAP_OWNER_CHANGE: BeatmapsetEventCommentOwnerChange,
            BeatmapsetEventType.DISCUSSION_DELETE: BeatmapsetEventCommentNoPost,
            # `api.beatmapset_events(types=[BeatmapsetEventType.DISCUSSION_LOCK])`
            # doesn't seem to be recognized, just returns all events. Was this
            # type discontinued?
            # BeatmapsetEventType.DISCUSSION_LOCK: BeatmapsetEventComment,
            BeatmapsetEventType.DISCUSSION_POST_DELETE: BeatmapsetEventComment,
            BeatmapsetEventType.DISCUSSION_POST_RESTORE: BeatmapsetEventComment,
            BeatmapsetEventType.DISCUSSION_RESTORE: BeatmapsetEventCommentNoPost,
            # same here
            # BeatmapsetEventType.DISCUSSION_UNLOCK: BeatmapsetEventComment,
            BeatmapsetEventType.DISQUALIFY: BeatmapsetEventCommentWithNominators,
            # same here
            # BeatmapsetEventType.DISQUALIFY_LEGACY: BeatmapsetEventComment
            BeatmapsetEventType.GENRE_EDIT: BeatmapsetEventCommentChange[str],
            BeatmapsetEventType.ISSUE_REOPEN: BeatmapsetEventComment,
            BeatmapsetEventType.ISSUE_RESOLVE: BeatmapsetEventComment,
            BeatmapsetEventType.KUDOSU_ALLOW: BeatmapsetEventCommentNoPost,
            BeatmapsetEventType.KUDOSU_DENY: BeatmapsetEventCommentNoPost,
            BeatmapsetEventType.KUDOSU_GAIN: BeatmapsetEventCommentKudosuChange,
            BeatmapsetEventType.KUDOSU_LOST: BeatmapsetEventCommentKudosuChange,
            BeatmapsetEventType.KUDOSU_RECALCULATE: BeatmapsetEventCommentKudosuRecalculate,
            BeatmapsetEventType.LANGUAGE_EDIT: BeatmapsetEventCommentChange[str],
            BeatmapsetEventType.LOVE: type(None),
            BeatmapsetEventType.NOMINATE: BeatmapsetEventCommentNominate,
            # same here
            # BeatmapsetEventType.NOMINATE_MODES: BeatmapsetEventComment,
            BeatmapsetEventType.NOMINATION_RESET: BeatmapsetEventCommentWithNominators,
            BeatmapsetEventType.NOMINATION_RESET_RECEIVED: BeatmapsetEventCommentWithSourceUser,
            BeatmapsetEventType.QUALIFY: type(None),
            BeatmapsetEventType.RANK: type(None),
            BeatmapsetEventType.REMOVE_FROM_LOVED: BeatmapsetEventCommentLovedRemoval,
            BeatmapsetEventType.NSFW_TOGGLE: BeatmapsetEventCommentChange[bool],
        }
        type_ = BeatmapsetEventType(self.type)
        return {"comment": mapping[type_]}

    def user(self) -> Optional[User]:
        return self._fk_user(self.user_id)

class ChatChannel(Model):
    channel_id: int
    description: Optional[str]
    icon: Optional[str]
    # documented as non-optional (to see that it can be null, pm tillerino)
    moderated: Optional[bool]
    name: str
    type: ChannelType
    uuid: Optional[str]

    # optional fields
    # ---------------
    first_message_id: Optional[int]
    last_message_id: Optional[int]
    last_read_id: Optional[int]
    recent_messages: Optional[List[ChatMessage]]
    users: Optional[List[int]]

class ChatMessage(Model):
    channel_id: int
    content: str
    is_action: bool
    message_id: int
    sender: UserCompact
    sender_id: int
    timestamp: Datetime
    # TODO enumify, example value: "plain"
    type: str

class CreatePMResponse(Model):
    message: ChatMessage
    new_channel_id: int

    # undocumented
    channel: ChatChannel

    # documented but not present in response
    presence: Optional[List[ChatChannel]]

class ModdingHistoryEventsBundle(Model):
    # https://github.com/ppy/osu-web/blob/master/app/Libraries/ModdingHistor
    # yEventsBundle.php#L84
    events: List[BeatmapsetEvent]
    reviewsConfig: BeatmapsetDiscussionReview
    users: List[UserCompact]

class UserRelation(Model):
    # undocumented (and not a class on osu-web)
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserRelatio
    # nTransformer.php#L16
    target_id: int
    relation_type: UserRelationType
    mutual: bool

    # optional fields
    # ---------------
    target: Optional[UserCompact]

    def target(self) -> Union[User, UserCompact]:
        return self._fk_user(self.target_id, existing=self.target)


class UserStatistics(Model):
    level: UserLevel
    pp: float
    ranked_score: int
    hit_accuracy: float
    play_count: int
    play_time: int
    total_score: int
    total_hits: int
    maximum_combo: int
    replays_watched_by_others: int
    is_ranked: bool
    grade_counts: UserGradeCounts
    country_rank: Optional[int]
    global_rank: Optional[int]
    rank: Optional[Any]
    user: Optional[UserCompact]
    variants: Optional[Any]
    global_rank_exp: Optional[float]
    pp_exp: float
    count_100: int
    count_300: int
    count_50: int
    count_miss: int

class UserStatisticsRulesets(Model):
    # undocumented
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserStatisti
    # csRulesetsTransformer.php
    osu: Optional[UserStatistics]
    taiko: Optional[UserStatistics]
    fruits: Optional[UserStatistics]
    mania: Optional[UserStatistics]

class RoomPlaylistItemMod(Model):
    acronym: str
    settings: Dict[str, Any]

class RoomPlaylistItem(Model):
    id: int
    room_id: int
    beatmap_id: int
    ruleset_id: int
    allowed_mods: List[RoomPlaylistItemMod]
    required_mods: List[RoomPlaylistItemMod]
    expired: bool
    owner_id: int
    # null for playlist items which haven't finished yet, I think
    playlist_order: Optional[int]
    # null for playlist items which haven't finished yet, I think
    played_at: Optional[Datetime]
    beatmap: BeatmapCompact

class Room(Model):
    id: int
    name: str
    category: RoomCategory
    type: RoomType
    user_id: int
    starts_at: Datetime
    ends_at: Datetime
    max_attempts: Optional[int]
    participant_count: int
    channel_id: int
    active: bool
    has_password: bool
    queue_mode: str
    auto_skip: bool
    host: UserCompact
    playlist: List[RoomPlaylistItem]
    recent_participants: List[UserCompact]

class RoomLeaderboardScore(Model):
    accuracy: float
    attempts: int
    completed: int
    pp: float
    room_id: int
    total_score: int
    user_id: int
    user: UserCompact

class RoomLeaderboardUserScore(RoomLeaderboardScore):
    position: int

class RoomLeaderboard(Model):
    leaderboard: List[RoomLeaderboardScore]
    user_score: RoomLeaderboardUserScore

class Match(Model):
    id: int
    start_time: Datetime
    # null for matches which haven't finished yet, I think
    end_time: Optional[Datetime]
    name: str

class Matches(Model):
    matches: List[Match]
    cursor: CursorT
    params: Any
    cursor_string: str

class MatchGame(Model):
    id: int
    start_time: Datetime
    # null for in-progress matches.
    end_time: Optional[Datetime]
    mode: GameMode
    mode_int: int
    scoring_type: ScoringType
    team_type: TeamType
    mods: List[Mod]
    beatmap: BeatmapCompact
    beatmap_id: int
    scores: List[Score]

class MatchEventDetail(Model):
    type: MatchEventType
    # seems to only be used for MatchEventType.OTHER
    text: Optional[str]

class MatchEvent(Model):
    id: int
    detail: MatchEventDetail
    timestamp: Datetime
    # can be none for MatchEventType.OTHER
    user_id: Optional[int]
    game: Optional[MatchGame]

class MatchResponse(Model):
    match: Match
    events: List[MatchEvent]
    users: List[UserCompact]
    first_event_id: int
    latest_event_id: int
    current_game_id: Optional[int]
