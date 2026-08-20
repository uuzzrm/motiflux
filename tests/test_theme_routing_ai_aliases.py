from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "motiflux" / "tools"))

from engine.catalog import load_catalog  # noqa: E402


class ThemeRoutingAiAliasTests(unittest.TestCase):
    def test_chinese_ai_aliases_route_to_ai_field(self) -> None:
        catalog = load_catalog()
        for query in ("人工智能 logo 动画", "生成式 AI logo", "AI 科技 logo", "AI technology logo", "人工智能技术 logo"):
            selection = catalog.route(query)["theme_selection"]
            self.assertEqual(selection["primary_id"], "ai-field", query)

    def test_education_and_low_motion_routes_remain_stable(self) -> None:
        catalog = load_catalog()
        self.assertEqual(catalog.route("教育 logo")['theme_selection']["primary_id"], "system-spatial")
        self.assertEqual(catalog.route("低动效 logo")['theme_selection']["primary_id"], "accessibility-first")

    def test_structured_chinese_routing_aliases_select_expected_themes(self) -> None:
        catalog = load_catalog()
        cases = {
            "金融": "fintech-trust",
            "银行": "fintech-trust",
            "支付": "fintech-trust",
            "金融科技": "fintech-trust",
            "可信": "fintech-trust",
            "稳健": "fintech-trust",
            "安全": "security-shield",
            "隐私": "security-shield",
            "认证": "security-shield",
            "防护": "security-shield",
            "盾牌": "security-shield",
            "合规": "security-shield",
            "电商": "commerce-energy",
            "零售": "commerce-energy",
            "购物": "commerce-energy",
            "消费": "commerce-energy",
            "促销": "commerce-energy",
            "汽车": "automotive-precision",
            "交通": "automotive-precision",
            "工业": "automotive-precision",
            "工程": "automotive-precision",
            "性能": "automotive-precision",
            "机械": "automotive-precision",
            "体育": "sports-impact",
            "健身": "sports-impact",
            "竞技": "sports-impact",
            "速度": "sports-impact",
            "冲击": "sports-impact",
            "电影": "cinematic-title",
            "片头": "cinematic-title",
            "预告": "cinematic-title",
            "叙事": "cinematic-title",
            "戏剧": "cinematic-title",
            "自然": "nature-flow",
            "有机": "nature-flow",
            "健康": "nature-flow",
            "环保": "nature-flow",
            "成长": "nature-flow",
            "游戏": "gaming-world",
            "电竞": "gaming-world",
            "奇幻": "gaming-world",
            "科幻": "gaming-world",
            "街机": "gaming-world",
        }
        for alias, expected_id in cases.items():
            with self.subTest(alias=alias):
                selection = catalog.route(f"{alias} logo")['theme_selection']
                self.assertEqual(selection["primary_id"], expected_id)
                self.assertIn(alias, selection["matched_aliases"])
                self.assertIn(alias, selection["matched_tags"])

    def test_route_exposes_structured_tags_and_legacy_match_field(self) -> None:
        selection = load_catalog().route("金融科技 logo")['theme_selection']
        self.assertIn("matched_aliases", selection)
        self.assertIn("金融科技", selection["matched_aliases"])
        self.assertIn("matched_tags", selection)
        self.assertIn("finance", selection["domain_tags"])
        self.assertIn("trust", selection["style_tags"])
        self.assertIn("progress", selection["motion_tags"])


if __name__ == "__main__":
    unittest.main()
