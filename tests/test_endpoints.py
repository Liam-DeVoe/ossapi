from datetime import datetime
from unittest import TestCase

from ossapi import (
    RankingType,
    BeatmapsetEventType,
    InsufficientScopeError,
    Mod,
    GameMode,
    ForumPoll,
    RoomSearchMode,
    EventsSort,
)

from tests import (
    TestCaseAuthorizationCode,
    TestCaseDevServer,
    UNIT_TEST_MESSAGE,
    api_v2 as api,
    api_v2_full as api_full,
    api_v2_old as api_old,
    api_v2_dev as api_dev,
)


class TestBeatmapsetDiscussionPosts(TestCase):
    def test_deserialize(self):
        api.beatmapset_discussion_posts()


class TestUserRecentActivity(TestCase):
    def test_deserialize(self):
        api.user_recent_activity(12092800)


class TestSpotlights(TestCase):
    def test_deserialize(self):
        api.spotlights()


class TestUserBeatmaps(TestCase):
    def test_deserialize(self):
        api.user_beatmaps(user_id=12092800, type="most_played")


class TestUserKudosu(TestCase):
    def test_deserialize(self):
        api.user_kudosu(user_id=3178418)


class TestBeatmapScores(TestCase):
    def test_deserialize(self):
        api.beatmap_scores(beatmap_id=1981090)


class TestBeatmap(TestCase):
    def test_deserialize(self):
        api.beatmap(beatmap_id=221777)

        # beatmap with a diff owner
        bm = api.beatmap(beatmap_id=1604098)
        # might need to be updated when
        # https://github.com/ppy/osu-web/issues/9784 is addressed.
        self.assertIsNone(bm.owner)


class TestBeatmapset(TestCase):
    def test_deserialize(self):
        api.beatmapset(beatmap_id=3207950)


class TestBeatmapsetEvents(TestCase):
    def test_deserialize(self):
        api.beatmapset_events()

    def test_all_types(self):
        # beatmapset_events is a really complicated endpoint in terms of return
        # types. We want to make sure both that we're not doing anything wrong,
        # and the osu! api isn't doing anything wrong by returning something
        # that doesn't match their documentation.
        for event_type in BeatmapsetEventType:
            api.beatmapset_events(types=[event_type])


class TestRanking(TestCase):
    def test_deserialize(self):
        api.ranking("osu", RankingType.PERFORMANCE, country="US")
        api.ranking("osu", type="country")
        api.ranking("osu", type="charts")

        api.ranking("mania", "performance")
        api.ranking("mania", "performance", variant="4k")
        api.ranking("mania", "performance", variant="7k")

        api.ranking("fruits", "performance")
        api.ranking("taiko", "performance")


class TestUserScores(TestCase):
    def test_deserialize(self):
        api.user_scores(12092800, "best")


class TestBeatmapUserScore(TestCase):
    def test_deserialize(self):
        api.beatmap_user_score(beatmap_id=221777, user_id=2757689, mode="osu")


class TestBeatmapUserScores(TestCase):
    def test_deserialize(self):
        api.beatmap_user_scores(beatmap_id=221777, user_id=2757689, mode="osu")


class TestSearch(TestCase):
    def test_deserialize(self):
        api.search(query="peppy")


class TestComment(TestCase):
    def test_deserialize(self):
        # normal comments
        api.comment(1)
        api.comment(1123123)

        # comment on a deleted object
        api.comment(3)


class TestSearchBeatmaps(TestCase):
    def test_deserialize(self):
        api.search_beatmapsets(query="the big black")


class TestUser(TestCase):
    def test_deserialize(self):
        api.user(12092800)
        # user with an account_history (tournament ban)
        api.user(9997093)

    def test_key(self):
        # make sure it automatically falls back to username if not specified
        api.user("tybug")
        api.user("tybug", key="username")

        self.assertRaises(Exception, lambda: api.user("tybug", key="id"))


class TestMe(TestCase):
    def test_insufficient_scope(self):
        # client credentials grant can't request `Scope.IDENTIFY` and so can't
        # access /me
        self.assertRaises(InsufficientScopeError, api.get_me)


class TestWikiPage(TestCase):
    def test_deserialize(self):
        api.wiki_page("en", "Welcome")


class TestChangelogBuild(TestCase):
    def test_deserialize(self):
        api.changelog_build("stable40", "20210520.2")


class TestChangelogListing(TestCase):
    def test_deserialize(self):
        api.changelog_listing()


class TestChangelogLookup(TestCase):
    def test_deserialize(self):
        api.changelog_build_lookup("lazer")


class TestForumTopic(TestCase):
    def test_deserialize(self):
        # normal topic
        # https://osu.ppy.sh/community/forums/topics/141240?n=1
        api.forum_topic(141240)
        # topic with a poll
        # https://osu.ppy.sh/community/forums/topics/1781998?n=1
        api.forum_topic(1781998)


class TestBeatmapsetDiscussionVotes(TestCase):
    def test_deserialize(self):
        api.beatmapset_discussion_votes().votes[0].score


class TestBeatmapsetDiscussions(TestCase):
    def test_deserialize(self):
        api.beatmapset_discussions()


class TestNewsListing(TestCase):
    def test_deserialize(self):
        api.news_listing(year=2021)


class TestNewsPost(TestCase):
    def test_deserialize(self):
        # querying the same post by id or slug should give the same result.
        post1 = api.news_post(1025, key="id")
        post2 = api.news_post("2021-10-04-halloween-fanart-contest", key="slug")

        self.assertEqual(post1.id, post2.id)
        self.assertEqual(post1, post2)


class TestSeasonalBackgrounds(TestCase):
    def test_deserialize(self):
        api.seasonal_backgrounds()


class TestBeatmapAttributes(TestCase):
    def test_deserialize(self):
        api.beatmap_attributes(221777, ruleset="osu")
        api.beatmap_attributes(221777, mods=Mod.HDDT)
        api.beatmap_attributes(221777, mods="HR")
        api.beatmap_attributes(221777, ruleset_id=0)


class TestUsers(TestCase):
    def test_deserialize(self):
        api.users([12092800])


class TestBeatmaps(TestCase):
    def test_deserialize(self):
        api.beatmaps([221777])


class TestScore(TestCase):
    def test_deserialize(self):
        for api_ in [api, api_old]:
            # downloadable
            api_.score(429915881)
            # downloadable, my score
            api_.score(1262758549)
            # not downloadable, my score
            api_.score(1312718771)

            # other gamemodes
            api_.score(1874611010)  # taiko
            api_.score(2238254261)  # mania
            api_.score(1958862712)  # catch


class TestScoreMode(TestCase):
    def test_deserialize(self):
        # downloadable
        api.score_mode(GameMode.OSU, 2243145877)
        # downloadable, my score
        api.score_mode(GameMode.OSU, 3685255338)
        # not downloadable, my score
        api.score_mode(GameMode.OSU, 3772000814)

        # other gamemodes
        api.score_mode(GameMode.TAIKO, 176904666)
        api.score_mode(GameMode.MANIA, 524674142)
        api.score_mode(GameMode.CATCH, 211167987)


class TestFriends(TestCase):
    def test_access_denied(self):
        self.assertRaises(InsufficientScopeError, api.friends)


class TestRoom(TestCase):
    def test_deserialize(self):
        # https://osu.ppy.sh/multiplayer/rooms/257524
        api.room(257524)


class TestMatches(TestCase):
    def test_deserialize(self):
        api.matches()


class TestMatch(TestCase):
    def test_deserialize(self):
        for api_ in [api, api_old]:
            # https://osu.ppy.sh/community/matches/97947404, tournament match
            api_.match(97947404)
            # https://osu.ppy.sh/community/matches/103721175, deleted beatmap
            api_.match(103721175)


class TestComments(TestCase):
    def test_deserialize(self):
        api.comments()


class TestEvents(TestCase):
    def test_deserialize(self):
        events = api.events()
        api.events(cursor_string=events.cursor_string)
        api.events(sort=EventsSort.NEW)


class TestBeatmapPacks(TestCase):
    def test_deserialize(self):
        api.beatmap_packs()
        api.beatmap_packs("artist")


class TestBeatmapPack(TestCase):
    def test_deserialize(self):
        api.beatmap_pack("S100")
        api.beatmap_pack("A1")


# ======================
# api_full test cases
# ======================


class TestCreateNewPM(TestCaseAuthorizationCode):
    def test_deserialize(self):
        # test_account https://osu.ppy.sh/users/14212521
        api_full.send_pm(14212521, UNIT_TEST_MESSAGE)


class TestMeAuth(TestCaseAuthorizationCode):
    def test_deserialize(self):
        api_full.get_me()


class TestFriendsAuth(TestCaseAuthorizationCode):
    def test_deserialize(self):
        api_full.friends()


class TestRoomLeaderboard(TestCaseAuthorizationCode):
    def test_deserialize(self):
        # https://osu.ppy.sh/multiplayer/rooms/232594
        api_full.room_leaderboard(232594)


class TestRooms(TestCaseAuthorizationCode):
    def test_deserialize(self):
        api_full.rooms()
        api_full.rooms(mode=RoomSearchMode.OWNED)


class TestDownloadScore(TestCaseAuthorizationCode):
    def test_deserialize(self):
        api_full.download_score(429915881)


class TestDownloadScoreMode(TestCaseAuthorizationCode):
    def test_deserialize(self):
        api_full.download_score_mode("osu", score_id=2243145877)


# ==================
# api_dev test cases
# ==================


class TestForum(TestCaseDevServer):
    def test_forum(self):
        # test creating both a topic and posting a reply in that topic.
        # be careful to post to one of the forums in
        # `double_post_allowed_forum_ids`, or else we'll be rejected for double
        # posting.
        # https://github.com/ppy/osu-web/blob/3d1586392102b05f2a3b264905c4dbb7b
        # 2d430a2/config/osu.php#L107.

        # create and edit a topic
        response = api_dev.forum_create_topic(85, UNIT_TEST_MESSAGE, UNIT_TEST_MESSAGE)
        topic_id = response.topic.id
        api_dev.forum_edit_topic(
            topic_id, f"This title was last updated at {datetime.now()}"
        )

        # unfortunately, 85 (help and technical support) is not one of the
        # whitelisted double posting allowed forums, so we can't create a reply
        # right after our post.
        # We could switch to another forum which does allow double posting
        # (off-topic), but then we can only make as many topics as we have
        # playcount, requiring me to constantly play on my dev account to make
        # the tests work. I'll take less test coverage over that.
        # Can uncomment if peppy ever grants my dev account a playcount bypass
        # in the future.

        ## create and edit a post under that topic
        # response = api_dev.forum_reply(topic_id, UNIT_TEST_MESSAGE)
        # post_id = response.id
        # api_dev.forum_edit_post(post_id,
        #     f"This comment was last edited at {datetime.now()}")

    def test_poll(self):
        poll = ForumPoll(
            options=["Option 1", "Option 2"],
            title="Test Poll",
            length_days=0,
            vote_change=True,
            max_options=1,
        )
        api_dev.forum_create_topic(
            title=f"{UNIT_TEST_MESSAGE}",
            body=f"{UNIT_TEST_MESSAGE} ({datetime.now()})",
            forum_id=85,
            poll=poll,
        )
