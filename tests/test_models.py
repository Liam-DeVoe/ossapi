from unittest import TestCase

from ossapi import (User, BeatmapsetCompact, UserCompact, GameMode,
    BeatmapCompact)

from tests import api_v2 as api


class TestMethodTypeConversion(TestCase):
    def test_beatmap_as_parameter(self):
        # make sure we can pass the full model in place of an id
        beatmap = api.beatmap(221777)
        self.assertEqual(api.beatmap_scores(beatmap),
            api.beatmap_scores(beatmap.id))

    def test_room_as_parameter(self):
        room1 = api.room(257524)
        room2 = api.room(room1)
        self.assertEqual(room1, room2)

class TestExpandableModels(TestCase):
    def test_expand_user(self):
        user = api.search(query="tybug2").users.data[0]
        # `statistics` is only available on User models, so make sure it's not
        # present before expanding and is present afterwards
        self.assertIsNone(user.statistics)

        user = user.expand()
        self.assertIsNotNone(user.statistics)

        # make sure expanding the user again returns the identical user
        user_new = user.expand()
        self.assertIs(user_new, user)

    def test_expand_beatmapset(self):
        beatmapset = api.beatmapset_discussion_posts().beatmapsets[0]
        self.assertIsNone(beatmapset.description)

        beatmapset = beatmapset.expand()
        self.assertIsNotNone(beatmapset.description)

        beatmapset_new = beatmapset.expand()
        self.assertIs(beatmapset_new, beatmapset)

    # TODO add test_expand_beatmap when I find a good endpoint that returns
    # BeatmapCompacts and not full Beatmaps.

class TestFollowingForeignKeys(TestCase):
    def test_beatmap_fks(self):
        beatmap = api.beatmap(221777)

        user = beatmap.user()
        self.assertIsInstance(user, User)
        self.assertEqual(user.id, 1047883)

        beatmapset = beatmap.beatmapset()
        self.assertIsInstance(beatmapset, BeatmapsetCompact)
        self.assertEqual(beatmapset.id, 79498)
        self.assertEqual(beatmapset.user_id, 1047883)

    def test_beatmapset_fks(self):
        beatmapset = api.beatmapset(beatmap_id=3207950)

        user = beatmapset.user()
        self.assertIsInstance(user, UserCompact)
        self.assertEqual(user.id, 4693052)

    def test_score_fks(self):
        score = api.score(GameMode.OSU, 3685255338)

        user = score.user()
        self.assertIsInstance(user, UserCompact)
        self.assertEqual(user.id, 12092800)

    def test_comment_fks(self):
        comment = api.comment(1533934).comments[0]

        user = comment.user()
        self.assertIsInstance(user, User)
        self.assertEqual(user.id, 12092800)

        edited_by = comment.edited_by()
        self.assertIsNone(edited_by)

    def test_forum_post_fks(self):
        post = api.forum_topic(141240).posts[0]

        user = post.user()
        self.assertIsInstance(user, User)
        self.assertEqual(user.id, 2)

        edited_by = post.edited_by()
        self.assertIsNone(edited_by)

    def test_forum_topic_fks(self):
        topic = api.forum_topic(141240).topic

        user = topic.user()
        self.assertIsInstance(user, User)
        self.assertEqual(user.id, 2)

    def test_beatmapset_discussion_post_fks(self):
        # https://osu.ppy.sh/beatmapsets/1576285/discussion#/2641058
        bmset_disc_post = api.beatmapset_discussion_posts(2641058).posts[0]

        user = bmset_disc_post.user()
        self.assertIsInstance(user, User)
        self.assertEqual(user.id, 6050530)

        last_editor = bmset_disc_post.last_editor()
        self.assertIsInstance(last_editor, User)
        self.assertEqual(last_editor.id, 6050530)

        deleted_by = bmset_disc_post.deleted_by()
        self.assertIsNone(deleted_by)

    def test_beatmap_playcount_fks(self):
        most_played = api.user_beatmaps(user_id=12092800, type="most_played")
        bm_playcount = most_played[0]

        beatmap = bm_playcount.beatmap()
        self.assertIsInstance(beatmap, BeatmapCompact)
        self.assertEqual(beatmap.id, 1626537)
