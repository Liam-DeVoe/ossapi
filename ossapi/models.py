# opt-in to forward type annotations
# https://docs.python.org/3.7/whatsnew/3.7.html#pep-563-postponed-evaluation-
# of-annotations
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar, Union

from ossapi.enums import (
    Availability,
    BeatmapOwner,
    BeatmapPackUserCompletionData,
    BeatmapsetApproval,
    BeatmapsetEventType,
    BeatmapTag,
    ChangelogSearch,
    ChannelType,
    Country,
    Cover,
    Covers,
    EventAchievement,
    EventBeatmap,
    EventBeatmapset,
    EventType,
    EventUser,
    Failtimes,
    ForumPollText,
    ForumPollTitle,
    ForumPostBody,
    ForumTopicSort,
    ForumTopicType,
    GameMode,
    GithubUser,
    Grade,
    Hype,
    Kudosu,
    KudosuAction,
    KudosuGiver,
    KudosuPost,
    KudosuVote,
    MatchEventType,
    MessageType,
    NewsSearch,
    Nomination,
    Nominations,
    PlayStyles,
    ProfileBanner,
    ProfilePage,
    RankHighest,
    RankHistory,
    RankStatus,
    ReviewsConfig,
    RoomCategory,
    RoomDifficultyRange,
    RoomPlaylistItemStats,
    RoomType,
    ScoringType,
    Statistics,
    Team,
    TeamType,
    UserAccountHistory,
    UserAchievement,
    UserBadge,
    UserGlobalRank,
    UserGradeCounts,
    UserGroup,
    UserLevel,
    UserMonthlyPlaycount,
    UserPage,
    UserProfileCustomization,
    UserRelationType,
    UserReplaysWatchedCount,
    Variant,
    Weight,
)
from ossapi.mod import Mod
from ossapi.utils import BaseModel, Datetime, Field, Model

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
CursorStringT = Optional[str]


class UserCompact(Model):
    """
    https://osu.ppy.sh/docs/index.html#usercompact
    """

    # required fields
    # ---------------
    avatar_url: str
    country_code: str
    id: int
    is_active: bool
    is_bot: bool
    is_deleted: bool
    is_online: bool
    is_supporter: bool
    last_visit: Datetime | None
    pm_friends_only: bool
    profile_colour: str | None
    username: str

    # optional fields
    # ---------------
    account_history: list[UserAccountHistory] | None
    active_tournament_banner: ProfileBanner | None
    active_tournament_banners: list[ProfileBanner] | None
    badges: list[UserBadge] | None
    beatmap_playcounts_count: int | None
    blocks: UserRelation | None
    country: Country | None
    cover: Cover | None
    default_group: str | None
    favourite_beatmapset_count: int | None
    follow_user_mapping: list[int] | None
    follower_count: int | None
    friends: list[UserRelation] | None
    graveyard_beatmapset_count: int | None
    groups: list[UserGroup] | None
    guest_beatmapset_count: int | None
    is_restricted: bool | None
    is_silenced: bool | None
    loved_beatmapset_count: int | None
    # undocumented
    global_rank: UserGlobalRank | None
    mapping_follower_count: int | None
    monthly_playcounts: list[UserMonthlyPlaycount] | None
    page: UserPage | None
    pending_beatmapset_count: int | None
    previous_usernames: list[str] | None
    # deprecated, replaced by rank_history
    rankHistory: RankHistory | None
    rank_history: RankHistory | None
    # deprecated, replaced by ranked_beatmapset_count
    ranked_and_approved_beatmapset_count: int | None
    ranked_beatmapset_count: int | None
    replays_watched_counts: list[UserReplaysWatchedCount] | None
    scores_best_count: int | None
    scores_first_count: int | None
    scores_recent_count: int | None
    statistics: UserStatistics | None
    statistics_rulesets: UserStatisticsRulesets | None
    support_level: int | None
    # deprecated, replaced by pending_beatmapset_count
    unranked_beatmapset_count: int | None
    unread_pm_count: int | None
    user_achievements: list[UserAchievement] | None
    user_preferences: UserProfileCustomization | None
    session_verified: bool | None
    team: Team | None

    def expand(self) -> User:
        return self._fk_user(self.id)


class User(UserCompact):
    comments_count: int
    cover_url: str
    discord: str | None
    has_supported: bool
    interests: str | None
    join_date: Datetime
    kudosu: Kudosu
    location: str | None
    max_blocks: int
    max_friends: int
    occupation: str | None
    playmode: str
    playstyle: PlayStyles | None
    post_count: int
    profile_order: list[ProfilePage]
    profile_hue: int | None
    daily_challenge_user_stats: DailyChallengeUserStats
    title: str | None
    title_url: str | None
    twitter: str | None
    website: str | None
    scores_pinned_count: int
    nominated_beatmapset_count: int
    rank_highest: RankHighest | None
    current_season_stats: SeasonStatistics | None

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
    _beatmapset: Field(name="beatmapset", type=BeatmapsetCompact | None)
    checksum: str | None
    failtimes: Failtimes | None
    max_combo: int | None

    def expand(self) -> Beatmap:
        return self._fk_beatmap(self.id)

    def user(self) -> User:
        return self._fk_user(self.user_id)

    def beatmapset(self) -> Beatmapset | BeatmapsetCompact:
        return self._fk_beatmapset(self.beatmapset_id, existing=self._beatmapset)


class Beatmap(BeatmapCompact):
    total_length: int
    version: str
    accuracy: float
    ar: float
    bpm: float | None
    current_user_tag_ids: list[int]
    # this might be non-optional? should test with client credentials grant.
    current_user_playcount: int | None
    top_tag_ids: list[int]
    convert: bool
    count_circles: int
    count_sliders: int
    count_spinners: int
    cs: float
    deleted_at: Datetime | None
    drain: float
    hit_length: int
    is_scoreable: bool
    last_updated: Datetime
    mode_int: int
    rating: float
    passcount: int
    playcount: int
    ranked: RankStatus
    url: str
    # user associated with this difficulty (ie diff mapper / owner).
    # Returned as `user` in the api, but that conflicts with our fk method for
    # beatmapset owner.
    # This is optional as a workaround until
    # https://github.com/ppy/osu-web/issues/9784 is resolved.
    owner: Field(name="user", type=UserCompact | None)
    # TODO does the new addition of this owners attribute deprecate the owner
    # attribute?
    owners: list[BeatmapOwner] | None

    # overridden fields
    # -----------------
    _beatmapset: Field(name="beatmapset", type=Beatmapset | None)

    def expand(self) -> Beatmap:
        return self

    def beatmapset(self) -> Beatmapset:
        return self._fk_beatmapset(self.beatmapset_id, existing=self._beatmapset)


class BeatmapsetCompact(Model):
    """
    https://osu.ppy.sh/docs/index.html#beatmapsetcompact
    """

    # required fields
    # ---------------
    anime_cover: bool
    artist: str
    artist_unicode: str
    covers: Covers
    current_user_playcount: int
    creator: str
    favourite_count: int
    id: int
    nsfw: bool
    offset: int
    play_count: int
    preview_url: str
    source: str
    status: RankStatus
    spotlight: bool
    title: str
    title_unicode: str
    user_id: int
    video: bool
    # documented as being in `Beatmapset` only, but returned by
    # `api.beatmapset_events` which uses a `BeatmapsetCompact`.
    hype: Hype | None

    # optional fields
    # ---------------
    beatmaps: list[Beatmap] | None
    converts: Any | None
    current_nominations: list[Nomination] | None
    current_user_attributes: Any | None
    description: Any | None
    discussions: Any | None
    events: Any | None
    genre: Any | None
    genre_id: int | None
    has_favourited: bool | None
    language: Any | None
    language_id: int | None
    nominations: Any | None
    pack_tags: list[str] | None
    ratings: Any | None
    recent_favourites: Any | None
    related_users: Any | None
    track_id: int | None
    _user: Field(name="user", type=UserCompact | None)

    def expand(self) -> Beatmapset:
        return self._fk_beatmapset(self.id)

    def user(self) -> UserCompact | User:
        return self._fk_user(self.user_id, existing=self._user)


class Beatmapset(BeatmapsetCompact):
    availability: Availability
    bpm: float
    can_be_hyped: bool
    deleted_at: Datetime | None
    discussion_enabled: bool
    discussion_locked: bool
    is_scoreable: bool
    last_updated: Datetime
    legacy_thread_url: str | None
    nominations_summary: Nominations
    ranked: RankStatus
    ranked_date: Datetime | None
    rating: float
    storyboard: bool
    submitted_date: Datetime | None
    tags: str
    related_tags: list[BeatmapTag]
    version_count: int

    def expand(self) -> Beatmapset:
        return self


# undocumented, but defined here to avoid a forward reference in Score.
class ScoreMatchInfo(Model):
    slot: int
    team: str
    pass_: Field(name="pass", type=bool)


class _LegacyScore(Model):
    # can be null for match scores, eg the scores
    # in https://osu.ppy.sh/community/matches/97947404
    id: int | None
    best_id: int | None
    user_id: int
    accuracy: float
    mods: Mod
    score: int
    max_combo: int
    perfect: bool
    statistics: Statistics
    pp: float | None
    rank: Grade
    created_at: Datetime
    mode: GameMode
    mode_int: int
    replay: bool
    passed: bool
    current_user_attributes: Any
    beatmap: Beatmap | None
    beatmapset: BeatmapsetCompact | None
    rank_country: int | None
    rank_global: int | None
    weight: Weight | None
    _user: Field(name="user", type=UserCompact | None)
    match: ScoreMatchInfo | None
    type: str


class Score(Model):
    """
    https://osu.ppy.sh/docs/index.html#score with x-api-version >= 20220705
    """

    id: int | None
    best_id: int | None
    user_id: int
    accuracy: float
    max_combo: int
    statistics: Statistics
    pp: float | None
    rank: Grade

    passed: bool
    current_user_attributes: Any
    classic_total_score: int
    processed: bool
    replay: bool
    maximum_statistics: Statistics
    mods: list[NonLegacyMod]
    ruleset_id: int
    started_at: Datetime | None
    ended_at: Datetime
    ranked: bool
    preserve: bool
    beatmap_id: int
    build_id: int | None
    has_replay: bool
    is_perfect_combo: bool
    total_score: int
    total_score_without_mods: int | None

    legacy_perfect: bool
    legacy_score_id: int | None
    legacy_total_score: int

    beatmap: Beatmap | None
    beatmapset: BeatmapsetCompact | None
    rank_country: int | None
    rank_global: int | None
    weight: Weight | None
    _user: Field(name="user", type=UserCompact | None)
    match: ScoreMatchInfo | None
    type: str

    @staticmethod
    def override_attributes(data, api):
        if api.api_version < 20220705:
            return _LegacyScore
        # there are rare cases where a legacy score is returned even when using a
        # modern api version. Legacy matches is the only exception I'm aware of currently.
        #
        # check a few attributes to be reasonably certain that we are in this case,
        # and then switch to _LegacyScore.
        if "mode" in data and "created_at" in data and "legacy_perfect" not in data:
            return _LegacyScore

    @staticmethod
    def preprocess_data(data, api):
        # scores from matches (api.match) return perfect as an int instead of a
        # bool (same as api v1). Convert to a bool here.
        if "perfect" in data and isinstance(data["perfect"], int):
            data["perfect"] = bool(data["perfect"])
        return data

    def user(self) -> UserCompact | User:
        return self._fk_user(self.user_id, existing=self._user)

    def download(self):
        if hasattr(self, "mode"):
            # _LegacyScore
            return self._api.download_score_mode(self.mode, self.id)

        return self._api.download_score(self.id)


class BeatmapUserScore(Model):
    position: int
    score: Score


class BeatmapUserScores(Model):
    scores: list[Score]


class BeatmapScores(Model):
    scores: list[Score]
    score_count: int
    user_score: Field(name="userScore", type=BeatmapUserScore | None)


class CommentableMeta(Model):
    # title is the only attribute returned for deleted commentables.
    id: int | None
    title: str
    type: str | None
    url: str | None
    owner_id: int | None
    owner_title: str | None
    locked: bool | None
    current_user_attributes: CommentableMetaCurrentUserAttributes | None


class CommentableMetaCurrentUserAttributes(Model):
    can_new_comment_reason: str | None


class Comment(Model):
    # null for deleted commentables, eg on /comments/3.
    commentable_id: int | None
    # null for deleted commentables, eg on /comments/3.
    commentable_type: str | None
    created_at: Datetime
    deleted_at: Datetime | None
    edited_at: Datetime | None
    edited_by_id: int | None
    id: int
    legacy_name: str | None
    message: str | None
    message_html: str | None
    parent_id: int | None
    pinned: bool
    replies_count: int
    updated_at: Datetime
    # null for some commentables, eg on /comments/3.
    user_id: int | None
    votes_count: int

    def user(self) -> User:
        return self._fk_user(self.user_id)

    def edited_by(self) -> User | None:
        return self._fk_user(self.edited_by_id)


class CommentBundle(Model):
    commentable_meta: list[CommentableMeta]
    comments: list[Comment]
    cursor: CursorT
    has_more: bool
    has_more_id: int | None
    included_comments: list[Comment]
    pinned_comments: list[Comment] | None
    # TODO this should be type CommentSort
    sort: str
    top_level_count: int | None
    total: int | None
    user_follow: bool
    user_votes: list[int]
    users: list[UserCompact]


class Forum(Model):
    id: int
    name: str
    description: str
    subforums: list[Forum] | None


class Forums(Model):
    forums: list[Forum]


class ForumTopics(Model):
    forum: Forum
    topics: list[ForumTopic]
    pinned_topics: list[ForumTopic]


class ForumPost(Model):
    created_at: Datetime
    deleted_at: Datetime | None
    edited_at: Datetime | None
    edited_by_id: int | None
    forum_id: int
    id: int
    topic_id: int
    user_id: int
    body: ForumPostBody

    def user(self) -> User:
        return self._fk_user(self.user_id)

    def edited_by(self) -> User | None:
        return self._fk_user(self.edited_by_id)


class ForumTopic(Model):
    created_at: Datetime
    deleted_at: Datetime | None
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
    views: int
    poll: ForumPollModel | None

    def user(self) -> User:
        return self._fk_user(self.user_id)


class ForumPollModel(Model):
    allow_vote_change: bool
    ended_at: Datetime | None
    hide_incomplete_results: bool
    last_vote_at: Datetime | None
    max_votes: int
    options: list[ForumPollOption]
    started_at: Datetime
    title: ForumPollTitle
    total_vote_count: int


class ForumPollOption(Model):
    id: int
    text: ForumPollText
    vote_count: int | None


class ForumTopicAndPosts(Model):
    cursor: CursorT
    search: ForumTopicSearch
    posts: list[ForumPost]
    topic: ForumTopic
    cursor_string: CursorStringT


class CreateForumTopicResponse(Model):
    post: ForumPost
    topic: ForumTopic


class ForumTopicSearch(Model):
    sort: ForumTopicSort | None
    limit: int | None
    start: int | None
    end: int | None


class SearchResult(Generic[T], Model):
    data: list[T]
    total: int


class WikiPage(Model):
    layout: str
    locale: str
    markdown: str
    path: str
    subtitle: str | None
    tags: list[str]
    title: str
    available_locales: list[str]


class Search(Model):
    users: Field(name="user", type=SearchResult[UserCompact] | None)
    wiki_pages: Field(name="wiki_page", type=SearchResult[WikiPage] | None)


class Spotlight(Model):
    end_date: Datetime
    id: int
    mode_specific: bool
    participant_count: int | None
    name: str
    start_date: Datetime
    type: str


class Spotlights(Model):
    spotlights: list[Spotlight]


class SeasonDivision(Model):
    colour_tier: str
    id: int
    image_url: str
    name: str
    threshold: float


class Season(Model):
    start_date: Datetime
    end_date: Datetime | None
    name: str
    room_count: int


class SeasonStatistics(Model):
    division: SeasonDivision
    season: Season
    rank: int
    total_score: float


# return-value wrapper for https://osu.ppy.sh/docs/index.html#get-users.
class Users(Model):
    users: list[UserCompact]


# return-value wrapper for https://osu.ppy.sh/docs/index.html#get-beatmaps.
class Beatmaps(Model):
    beatmaps: list[Beatmap]


class BeatmapPacks(Model):
    cursor: CursorT
    cursor_string: CursorStringT
    beatmap_packs: list[BeatmapPack]


class Rankings(Model):
    beatmapsets: list[Beatmapset] | None
    cursor: CursorT
    cursor_string: str | None
    ranking: list[UserStatistics] | list[CountryStatistics]
    spotlight: Spotlight | None
    total: int | None


class BeatmapsetDiscussionPost(Model):
    id: int
    beatmapset_discussion_id: int
    user_id: int
    last_editor_id: int | None
    deleted_by_id: int | None
    system: bool
    message: str
    created_at: Datetime
    updated_at: Datetime
    deleted_at: Datetime | None

    def user(self) -> User:
        return self._fk_user(self.user_id)

    def last_editor(self) -> User | None:
        return self._fk_user(self.last_editor_id)

    def deleted_by(self) -> User | None:
        return self._fk_user(self.deleted_by_id)


class BeatmapsetDiscussion(Model):
    id: int
    beatmapset_id: int
    beatmap_id: int | None
    user_id: int
    deleted_by_id: int | None
    message_type: MessageType
    parent_id: int | None
    # a point of time which is ``timestamp`` milliseconds into the map
    timestamp: int | None
    resolved: bool
    can_be_resolved: bool
    can_grant_kudosu: bool
    created_at: Datetime
    current_user_attributes: Any
    updated_at: Datetime
    deleted_at: Datetime | None
    # marked as required in the docs, but null in
    #   api.beatmapset_events(beatmapset_id=1112418)
    # due to this post
    # https://osu.ppy.sh/beatmapsets/1112418/discussion/-/generalAll#/1633002
    last_post_at: Datetime | None
    kudosu_denied: bool
    starting_post: BeatmapsetDiscussionPost | None
    posts: list[BeatmapsetDiscussionPost] | None
    _beatmap: Field(name="beatmap", type=BeatmapCompact | None)
    _beatmapset: Field(name="beatmapset", type=BeatmapsetCompact | None)

    def user(self) -> User:
        return self._fk_user(self.user_id)

    def deleted_by(self) -> User | None:
        return self._fk_user(self.deleted_by_id)

    def beatmapset(self) -> Beatmapset | BeatmapsetCompact:
        return self._fk_beatmapset(self.beatmapset_id, existing=self._beatmapset)

    def beatmap(self) -> Beatmap | None | BeatmapCompact:
        return self._fk_beatmap(self.beatmap_id, existing=self._beatmap)


class BeatmapsetDiscussionVote(Model):
    id: int
    score: int
    user_id: int
    beatmapset_discussion_id: int
    created_at: Datetime
    updated_at: Datetime
    # TODO is this field ever actually returned? not documented and can't find
    # a repro case.
    cursor_string: CursorStringT

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
    giver: KudosuGiver | None
    post: KudosuPost
    # see https://github.com/ppy/osu-web/issues/7549
    details: Any


class BeatmapPlaycount(Model):
    beatmap_id: int
    _beatmap: Field(name="beatmap", type=BeatmapCompact | None)
    beatmapset: BeatmapsetCompact | None
    count: int

    def beatmap(self) -> Beatmap | BeatmapCompact:
        return self._fk_beatmap(self.beatmap_id, existing=self._beatmap)


# we use this class to determine which event dataclass to instantiate and
# return, based on the value of the ``type`` parameter.
class _Event(Model):
    @staticmethod
    def override_attributes(data, api):
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
            EventType.USERNAME_CHANGE: UsernameChangeEvent,
        }
        type_ = EventType(data["type"])
        return mapping[type_]


class Event(Model):
    created_at: Datetime
    createdAt: Datetime
    id: int
    type: EventType


class AchievementEvent(Event):
    achievement: EventAchievement
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
    user: EventUser


class UsernameChangeEvent(Event):
    user: EventUser


class Build(Model):
    created_at: Datetime
    display_version: str
    id: int
    update_stream: UpdateStream | None
    users: int
    version: str | None
    changelog_entries: list[ChangelogEntry] | None
    versions: Versions | None
    youtube_id: str | None


class Versions(Model):
    next: Build | None
    previous: Build | None


class UpdateStream(Model):
    display_name: str | None
    id: int
    is_featured: bool
    name: str
    latest_build: Build | None
    user_count: int | None


class ChangelogEntry(Model):
    category: str
    created_at: Datetime | None
    github_pull_request_id: int | None
    github_url: str | None
    id: int | None
    major: bool
    message: str | None
    message_html: str | None
    repository: str | None
    title: str | None
    type: str
    url: str | None
    github_user: GithubUser


class ChangelogListing(Model):
    builds: list[Build]
    search: ChangelogSearch
    streams: list[UpdateStream]


class MultiplayerScores(Model):
    cursor: CursorT
    cursor_string: CursorStringT
    params: Any
    scores: list[MultiplayerScore]
    total: int | None
    user_score: MultiplayerScore | None


class MultiplayerScore(Model):
    id: int
    user_id: int
    room_id: int
    playlist_item_id: int
    beatmap_id: int
    rank: Grade
    total_score: int
    max_combo: int
    mods: list[Mod]
    statistics: Statistics
    passed: bool
    position: int | None
    scores_around: MultiplayerScoresAround | None
    user: User
    solo_score_id: int
    classic_total_score: int
    preserve: bool
    processed: bool
    ranked: bool
    maximum_statistics: Statistics
    total_score_without_mods: int
    best_id: int | None
    type: str
    accuracy: float
    build_id: int
    ended_at: Datetime
    is_perfect_combo: bool
    replay: bool
    pp: float | None
    started_at: Datetime
    ruleset_id: int
    current_user_attributes: Any
    has_replay: bool
    legacy_perfect: bool
    legacy_score_id: int | None
    legacy_total_score: int

    def beatmap(self):
        return self._fk_beatmap(self.beatmap_id)


class MultiplayerScoresAround(Model):
    higher: list[MultiplayerScore]
    lower: list[MultiplayerScore]


class NewsListing(Model):
    cursor: CursorT
    cursor_string: CursorStringT
    news_posts: list[NewsPost]
    news_sidebar: NewsSidebar
    search: NewsSearch


class NewsPost(Model):
    author: str
    edit_url: str
    first_image: str | None
    first_image_2x: Field(name="first_image@2x", type=str | None)
    id: int
    published_at: Datetime
    slug: str
    title: str
    updated_at: Datetime
    content: str | None
    navigation: NewsNavigation | None
    preview: str | None


class NewsNavigation(Model):
    newer: NewsPost | None
    older: NewsPost | None


class NewsSidebar(Model):
    current_year: int
    news_posts: list[NewsPost]
    years: list[int]


class SeasonalBackgrounds(Model):
    ends_at: Datetime
    backgrounds: list[SeasonalBackground]


class SeasonalBackground(Model):
    url: str
    user: UserCompact


class DifficultyAttributes(Model):
    attributes: BeatmapDifficultyAttributes


class BeatmapDifficultyAttributes(Model):
    max_combo: int
    star_rating: float

    # osu attributes
    aim_difficulty: float | None
    approach_rate: float | None
    flashlight_difficulty: float | None
    overall_difficulty: float | None
    slider_factor: float | None
    speed_difficulty: float | None
    speed_note_count: float | None
    aim_difficult_slider_count: float | None
    aim_difficult_strain_count: float | None
    speed_difficult_strain_count: float | None

    # taiko attributes
    stamina_difficulty: float | None
    rhythm_difficulty: float | None
    colour_difficulty: float | None
    approach_rate: float | None
    great_hit_window: float | None

    # ctb attributes
    approach_rate: float | None

    # mania attributes
    great_hit_window: float | None
    score_multiplier: float | None


class Events(Model):
    cursor: CursorT
    cursor_string: CursorStringT
    events: Field(type=list[_Event])


class BeatmapPack(Model):
    author: str
    date: Datetime
    name: str
    no_diff_reduction: bool
    # marked as nonnull on docs
    ruleset_id: int | None
    tag: str
    url: str

    # optional attributes
    beatmapsets: list[Beatmapset] | None
    user_completion_data: BeatmapPackUserCompletionData | None


class Scores(Model):
    cursor: CursorT
    cursor_string: CursorStringT
    scores: list[Score]


# ================
# Parameter Models
# ================

# models which aren't used for serialization, but passed to OssapiV2 methods.


@dataclass
class ForumPoll:
    options: list[str]
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
    beatmapsets: list[Beatmapset]
    cursor: CursorT
    recommended_difficulty: float | None
    error: str | None
    total: int
    search: Any
    cursor_string: str | None


class BeatmapsetDiscussions(Model):
    beatmaps: list[Beatmap]
    cursor: CursorT
    discussions: list[BeatmapsetDiscussion]
    included_discussions: list[BeatmapsetDiscussion]
    reviews_config: ReviewsConfig
    users: list[UserCompact]
    cursor_string: str | None
    beatmapsets: list[Beatmapset]


class BeatmapsetDiscussionReview(Model):
    # https://github.com/ppy/osu-web/blob/master/app/Libraries/BeatmapsetDis
    # cussionReview.php
    max_blocks: int


class BeatmapsetDiscussionPosts(Model):
    beatmapsets: list[BeatmapsetCompact]
    discussions: list[BeatmapsetDiscussion]
    cursor: CursorT
    posts: list[BeatmapsetDiscussionPost]
    users: list[UserCompact]
    cursor_string: str | None


class BeatmapsetDiscussionVotes(Model):
    cursor: CursorT
    discussions: list[BeatmapsetDiscussion]
    votes: list[BeatmapsetDiscussionVote]
    users: list[UserCompact]
    cursor_string: str | None


class BeatmapsetEventComment(Model):
    beatmap_discussion_id: int
    beatmap_discussion_post_id: int


class BeatmapsetEventCommentNoPost(Model):
    beatmap_discussion_id: int
    beatmap_discussion_post_id: int | None


class BeatmapsetEventCommentNone(Model):
    beatmap_discussion_id: int | None
    beatmap_discussion_post_id: int | None


class BeatmapsetEventCommentChange(Generic[S], BeatmapsetEventCommentNone):
    old: S
    new: S


class BeatmapsetEventCommentLovedRemoval(BeatmapsetEventCommentNone):
    reason: str


class BeatmapsetEventCommentKudosuChange(BeatmapsetEventCommentNoPost):
    new_vote: KudosuVote
    votes: list[KudosuVote]


class BeatmapsetEventCommentKudosuRecalculate(BeatmapsetEventCommentNoPost):
    new_vote: KudosuVote | None


class BeatmapsetEventCommentOwnerChange(BeatmapsetEventCommentNone):
    beatmap_id: int
    beatmap_version: str
    new_user_id: int
    new_user_username: str
    new_users: list[int]


class BeatmapsetEventCommentNominate(Model):
    # for some reason this comment type doesn't have the normal
    # beatmap_discussion_id and beatmap_discussion_post_id attributes (they're
    # not even null, just missing).
    modes: list[GameMode]


class BeatmapsetEventCommentWithNominators(BeatmapsetEventCommentNoPost):
    beatmap_ids: list[int] | None
    nominator_ids: list[int] | None


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
    comment: Any
    created_at: Datetime

    user_id: int | None
    beatmapset: BeatmapsetCompact | None
    discussion: BeatmapsetDiscussion | None

    @staticmethod
    def override_attributes(data, api):
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
            # Some events have a comment that is *just a string*.
            #   api.beatmapset_events(beatmapset_id=724033)
            # I've only seen this for "type": "disqualify", but who knows where
            # else it could happen. I've preemptively marked NOMINATION_RESET as
            # taking a string also.
            BeatmapsetEventType.DISQUALIFY: Union[
                BeatmapsetEventCommentWithNominators, str
            ],
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
            BeatmapsetEventType.NOMINATION_RESET: Union[
                BeatmapsetEventCommentWithNominators, str
            ],
            BeatmapsetEventType.NOMINATION_RESET_RECEIVED: BeatmapsetEventCommentWithSourceUser,
            BeatmapsetEventType.QUALIFY: type(None),
            BeatmapsetEventType.RANK: type(None),
            BeatmapsetEventType.REMOVE_FROM_LOVED: BeatmapsetEventCommentLovedRemoval,
            BeatmapsetEventType.NSFW_TOGGLE: BeatmapsetEventCommentChange[bool],
        }
        type_ = BeatmapsetEventType(data["type"])
        # some events don't seem to have an associate comment, eg
        #   api.beatmapset_events(beatmapset_id=692322)
        # I don't know under what circumstances this does or does not happen, so
        # I am marking all comments as optional.
        return {"comment": Optional[mapping[type_]]}

    def user(self) -> User | None:
        return self._fk_user(self.user_id)


class ChatChannel(Model):
    channel_id: int
    description: str | None
    icon: str | None
    moderated: bool | None
    name: str
    type: ChannelType
    uuid: str | None
    message_length_limit: int

    # optional fields
    # ---------------
    last_message_id: int | None
    last_read_id: int | None
    recent_messages: list[ChatMessage] | None
    users: list[int] | None


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


class CountryStatistics(Model):
    code: str
    active_users: int
    play_count: int
    ranked_score: int
    performance: int
    country: Country


class CreatePMResponse(Model):
    message: ChatMessage
    new_channel_id: int

    # undocumented
    channel: ChatChannel

    # documented but not present in response
    presence: list[ChatChannel] | None


class ModdingHistoryEventsBundle(Model):
    # https://github.com/ppy/osu-web/blob/master/app/Libraries/ModdingHistor
    # yEventsBundle.php#L84
    events: list[BeatmapsetEvent]
    reviewsConfig: BeatmapsetDiscussionReview
    users: list[UserCompact]


class UserRelation(Model):
    # undocumented (and not a class on osu-web)
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserRelatio
    # nTransformer.php#L16
    target_id: int
    relation_type: UserRelationType
    mutual: bool

    # optional fields
    # ---------------
    target: UserCompact | None

    def target(self) -> User | UserCompact:
        return self._fk_user(self.target_id, existing=self.target)


class StatisticsVariant(Model):
    mode: GameMode
    variant: Variant
    country_rank: int | None
    global_rank: int | None
    pp: float


class UserStatistics(Model):
    count_100: int
    count_300: int
    count_50: int
    count_miss: int
    country_rank: int | None
    grade_counts: UserGradeCounts
    hit_accuracy: float
    accuracy: float
    is_ranked: bool
    level: UserLevel
    maximum_combo: int
    play_count: int
    play_time: int | None
    pp: float | None
    pp_exp: float
    global_rank: int | None
    global_rank_exp: float | None
    # deprecated, replaced by global_rank and country_rank
    rank: Any | None
    ranked_score: int
    rank_change_since_30_days: int | None
    replays_watched_by_others: int
    total_hits: int
    total_score: int
    user: UserCompact | None
    variants: list[StatisticsVariant] | None
    global_rank_percent: float | None


class UserStatisticsRulesets(Model):
    # undocumented
    # https://github.com/ppy/osu-web/blob/master/app/Transformers/UserStatisti
    # csRulesetsTransformer.php
    osu: UserStatistics | None
    taiko: UserStatistics | None
    fruits: UserStatistics | None
    mania: UserStatistics | None


class RoomPlaylistItemMod(Model):
    acronym: str
    settings: dict[str, Any]


class RoomPlaylistItem(Model):
    id: int
    room_id: int
    beatmap_id: int
    ruleset_id: int
    allowed_mods: list[RoomPlaylistItemMod]
    required_mods: list[RoomPlaylistItemMod]
    expired: bool
    owner_id: int
    # null for playlist items which haven't finished yet, I think
    playlist_order: int | None
    # null for playlist items which haven't finished yet, I think
    played_at: Datetime | None
    beatmap: BeatmapCompact
    created_at: Datetime | None
    freestyle: bool


class _Room1(Model):
    id: int
    name: str
    category: RoomCategory
    type: RoomType
    user_id: int
    starts_at: Datetime
    ends_at: Datetime | None
    max_attempts: int | None
    participant_count: int
    channel_id: int
    active: bool
    has_password: bool
    queue_mode: str
    auto_skip: bool
    host: UserCompact
    playlist: list[RoomPlaylistItem]
    recent_participants: list[UserCompact]


class Room(Model):
    id: int
    name: str
    category: RoomCategory
    type: RoomType
    user_id: int
    starts_at: Datetime
    ends_at: Datetime | None
    max_attempts: int | None
    participant_count: int
    channel_id: int
    active: bool
    has_password: bool
    queue_mode: str
    auto_skip: bool
    host: UserCompact
    playlist: list[RoomPlaylistItem]
    description: str | None
    status: str
    pinned: bool

    # new from _Room1
    playlist_item_stats: RoomPlaylistItemStats
    current_playlist_item: RoomPlaylistItem | None
    difficulty_range: RoomDifficultyRange
    recent_participants: list[UserCompact]

    @staticmethod
    def override_attributes(data, api):
        if api.api_version < 20220217:
            return _Room1


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
    leaderboard: list[RoomLeaderboardScore]
    user_score: RoomLeaderboardUserScore | None


class Match(Model):
    id: int
    start_time: Datetime
    # null for matches which haven't finished yet, I think
    end_time: Datetime | None
    name: str


class Matches(Model):
    matches: list[Match]
    cursor: CursorT
    params: Any
    cursor_string: CursorStringT


class MatchGame(Model):
    id: int
    start_time: Datetime
    # null for in-progress matches.
    end_time: Datetime | None
    mode: GameMode
    mode_int: int
    scoring_type: ScoringType
    team_type: TeamType
    mods: list[Mod]
    # null for deleted beatmaps,
    # e.g. https://osu.ppy.sh/community/matches/103721175.
    # TODO doesn't match docs
    beatmap: BeatmapCompact | None
    beatmap_id: int
    match_id: int
    scores: list[Score]


class MatchEventDetail(Model):
    type: MatchEventType
    # seems to only be used for MatchEventType.OTHER
    text: str | None


class MatchEvent(Model):
    id: int
    detail: MatchEventDetail
    timestamp: Datetime
    # can be none for MatchEventType.OTHER
    user_id: int | None
    game: MatchGame | None


class MatchResponse(Model):
    match: Match
    events: list[MatchEvent]
    users: list[UserCompact]
    first_event_id: int
    latest_event_id: int
    current_game_id: int | None


class DailyChallengeUserStats(Model):
    daily_streak_best: int
    daily_streak_current: int
    last_update: Datetime
    last_weekly_streak: Datetime
    playcount: int
    top_10p_placements: int
    top_50p_placements: int
    user_id: int
    weekly_streak_best: int
    weekly_streak_current: int


class NonLegacyMod(Model):
    acronym: str
    settings: Any


class Tag(Model):
    id: int
    name: str
    description: str
    ruleset_id: int | None


class Tags(Model):
    tags: list[Tag]


class BeatmapsPassed(Model):
    beatmaps_passed: list[BeatmapCompact]
