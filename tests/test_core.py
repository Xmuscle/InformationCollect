"""
Intel Briefing - 基础测试
测试核心模块的基本功能，不依赖外部 API。
"""
import sys
import os
import pytest


class TestConfig:
    """测试配置模块。"""

    def test_config_imports(self):
        from src.config import cfg, DEEPSEEK_API_URL, JINA_READER_URL
        assert DEEPSEEK_API_URL.startswith("https://")
        assert JINA_READER_URL.startswith("https://")
        assert cfg.fetch_timeout > 0

    def test_config_has_all_keys(self):
        from src.config import cfg
        # Verify all critical fields exist
        assert hasattr(cfg, 'deepseek_api_url')
        assert hasattr(cfg, 'xai_base_url')
        assert hasattr(cfg, 'jina_reader_url')
        assert hasattr(cfg, 'llm_rate_limit_delay')


class TestDedup:
    """测试去重逻辑。"""

    def test_dedup_removes_duplicates(self):
        from src.intel_collector import _dedup_items
        items = [
            {"title": "Hello World", "url": "a"},
            {"title": "hello world", "url": "b"},
            {"title": "Different", "url": "c"},
        ]
        result = _dedup_items(items)
        assert len(result) == 2

    def test_dedup_keeps_empty_titles(self):
        from src.intel_collector import _dedup_items
        items = [
            {"title": "", "url": "a"},
            {"title": "", "url": "b"},
        ]
        result = _dedup_items(items)
        assert len(result) == 2

    def test_dedup_empty_list(self):
        from src.intel_collector import _dedup_items
        assert _dedup_items([]) == []

    def test_extract_agent_research_candidates_matches_title_and_summary(self):
        from src.intel_collector import _extract_agent_research_candidates
        items = [
            {"title": "Agentic Memory for LLM Systems", "summary": "", "url": "a"},
            {"title": "Plain RAG Paper", "summary": "Uses multi-agent coordination for retrieval", "url": "b"},
            {"title": "Unrelated Vision Paper", "summary": "", "url": "c"},
        ]
        result = _extract_agent_research_candidates(items)
        assert len(result) == 2
        assert result[0]["source"] == "ArXiv Agent (fallback)"
        assert all(item["category"] == "ArXiv Agent" for item in result)


class TestReportGenerator:
    """测试报告生成。"""

    def test_generate_empty_report(self):
        from src.report_generator import generate_report
        intel = {
            "tech_trends": [],
            "capital_flow": [],
            "product_gems": [],
            "community": [],
            "research": [],
            "social": [],
            "xhs_directives": [],
            "insights": [],
        }
        report = generate_report(intel, "2026-01-01")
        assert "全球情报日报" in report
        assert "2026-01-01" in report
        assert "暂无数据" in report

    def test_generate_report_with_data(self):
        from src.report_generator import generate_report
        intel = {
            "tech_trends": [
                {"title": "Test Project", "url": "https://example.com", "heat": "100", "time": "1h", "category": "HN"}
            ],
            "capital_flow": [],
            "product_gems": [],
            "community": [
                {"title": "V2EX Topic", "url": "https://v2ex.com/t/1", "heat": "50 replies"}
            ],
            "research": [],
            "social": [],
            "xhs_directives": [],
            "insights": [],
        }
        report = generate_report(intel, "2026-01-01")
        assert "Test Project" in report
        assert "V2EX Topic" in report
        assert "https://example.com" in report

    def test_generate_report_with_multiple_social_reports(self):
        from src.report_generator import generate_report
        intel = {
            "tech_trends": [],
            "capital_flow": [],
            "product_gems": [],
            "community": [],
            "research": [],
            "agent_research": [],
            "social": [
                {"source": "X (via Grok) - AI/LLM/Startups", "content": "General social report", "type": "markdown_report"},
                {"source": "X (via Grok) - AI Agents", "content": "Agent social report", "type": "markdown_report"},
            ],
            "xhs_directives": [],
            "insights": [],
        }
        report = generate_report(intel, "2026-01-01")
        assert "X (via Grok) - AI/LLM/Startups" in report
        assert "X (via Grok) - AI Agents" in report
        assert "Agent social report" in report

    def test_generate_report_product_gems_include_chinese_intro(self, monkeypatch):
        import src.report_generator as report_generator
        monkeypatch.setattr(report_generator, "expand_product_tagline", lambda name, tagline: "中文简介")
        intel = {
            "tech_trends": [],
            "capital_flow": [],
            "product_gems": [
                {"title": "Demo Product", "url": "https://example.com", "heat": "10 votes", "tagline": "AI note taker", "topics": []}
            ],
            "community": [],
            "research": [],
            "agent_research": [],
            "social": [],
            "xhs_directives": [],
            "insights": [],
        }
        report = report_generator.generate_report(intel, "2026-01-01")
        assert "AI note taker" in report
        assert "中文简介" in report


class TestFetchNewsHelpers:
    """测试 fetch_news 辅助函数。"""

    def test_filter_items_no_keyword(self):
        from src.external.fetch_news import filter_items
        items = [{"title": "Hello"}, {"title": "World"}]
        assert filter_items(items) == items

    def test_filter_items_with_keyword(self):
        from src.external.fetch_news import filter_items
        items = [
            {"title": "Python is great"},
            {"title": "Java is fine"},
            {"title": "Rust rocks"},
        ]
        result = filter_items(items, "Python")
        assert len(result) == 1
        assert result[0]["title"] == "Python is great"

    def test_validate_url(self):
        from src.external.fetch_news import _validate_url
        assert _validate_url("https://example.com") is True
        assert _validate_url("http://example.com") is True
        assert _validate_url("ftp://example.com") is False
        assert _validate_url("") is False
        assert _validate_url(None) is False


class TestVerifier:
    """测试链接验证器。"""

    def test_invalid_url_format(self):
        from src.utils.verifier import verify_link
        assert verify_link("") is False
        assert verify_link("not-a-url") is False
        assert verify_link("ftp://example.com") is False


class TestGrokReportValidation:
    """测试 Grok 报告验证。"""

    def test_validate_no_links(self):
        from src.intel_collector import validate_grok_report
        content = "This is a report with no links."
        assert validate_grok_report(content) == content

    def test_validate_with_skip_domains(self):
        from src.intel_collector import validate_grok_report
        content = "Check [this](https://twitter.com/user) and [that](https://x.com/post)"
        result = validate_grok_report(content)
        # Should not modify links from skip domains
        assert "⚠️" not in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
