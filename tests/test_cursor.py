from unittest import TestCase

from ossapi import RankingType, Cursor

from tests import api_v2 as api


class TestCursor(TestCase):
    def test_nullable_cursor(self):
        cursor = Cursor(page=199)
        r = api.ranking("osu", RankingType.SCORE, cursor=cursor)
        self.assertIsNotNone(r.cursor)

        # 200 is the last page of results so we expect a null cursor in response
        cursor = Cursor(page=200)
        r = api.ranking("osu", RankingType.SCORE, cursor=cursor)
        self.assertIsNone(r.cursor)
