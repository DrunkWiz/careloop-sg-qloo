"""Unit tests for QlooClient and FixtureQlooClient (100% offline, no API key required)."""
from __future__ import annotations

import unittest

from backend.taste.client import FixtureQlooClient, QlooClient, describe_qloo


class TestQlooClient(unittest.TestCase):
    def test_fixture_search_known_and_unknown_seeds(self):
        c = FixtureQlooClient()
        res = c.search("Teresa Teng")
        self.assertEqual(res["mode"], "fixture")
        self.assertEqual(res["results"][0]["entity_id"], "urn:entity:artist:qloo-teresa-teng")

        unknown = c.search("perlis laksa")
        self.assertEqual(unknown["mode"], "fixture")
        self.assertTrue(unknown["results"][0]["entity_id"].startswith("urn:entity:place:qloo-"))

    def test_fixture_insights_across_three_domains(self):
        c = FixtureQlooClient()
        places = c.insights("urn:entity:place", signal_tags=["kopi", "mahjong", "teresa teng"], region="central")
        artists = c.insights("urn:entity:artist", signal_tags=["p. ramlee", "kopi"], region="west")
        movies = c.insights("urn:entity:movie", signal_tags=["p. ramlee", "kopi"], region="west")

        self.assertGreater(len(places["results"]), 0)
        self.assertEqual(places["results"][0]["entity_id"], "urn:entity:place:qloo-tp-porridge")
        self.assertEqual(artists["results"][0]["entity_id"], "urn:entity:artist:qloo-p-ramlee")
        self.assertEqual(movies["results"][0]["entity_id"], "urn:entity:movie:qloo-bujang-lapok")

    def test_qloo_client_caches_and_falls_back_when_no_key(self):
        c = QlooClient(api_key="")
        self.assertFalse(c.is_live)
        r1 = c.search("kopi")
        r2 = c.search("kopi")
        self.assertIs(r1, r2)  # served from in-memory cache
        self.assertEqual(r1["mode"], "fixture")

    def test_qloo_client_degrades_cleanly_on_network_error(self):
        c = QlooClient(api_key="dummy-key", base_url="http://127.0.0.1:1", timeout=0.05)
        self.assertTrue(c.is_live)
        s = c.search("Teresa Teng")
        self.assertEqual(s["mode"], "fixture")
        ins = c.insights("urn:entity:place", signal_tags=["kopi"], region="central")
        self.assertEqual(ins["mode"], "fixture")
        self.assertGreater(len(ins["results"]), 0)

    def test_describe_qloo_reports_metadata(self):
        meta = describe_qloo()
        self.assertEqual(meta["provider"], "Qloo Taste AI")
        self.assertIn("/v2/insights", meta["endpoints"])
        self.assertEqual(len(meta["domains"]), 3)


if __name__ == "__main__":
    unittest.main()
