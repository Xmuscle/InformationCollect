# Architecture

## 项目总览

Intel Briefing 是一个情报聚合引擎，从 12+ 数据源抓取科技/金融信息，经 Gemini 翻译摘要后生成中文日报。

## 技术栈

- **运行时**: Python 3.11+
- **包管理**: uv + hatchling
- **并发**: ThreadPoolExecutor (stdlib)
- **HTTP**: httpx (异步能力备用), requests
- **解析**: BeautifulSoup4, lxml, feedparser
- **AI**: Google Gemini (翻译/摘要), xAI Grok (Twitter 舆情)

## 数据流

```
cli.py (入口)
  │
  ├─→ intel_collector.py (并发调度)
  │     │
  │     ├─ Batch 1 (并行): 各传感器独立采集
  │     │   ├─ Tier 1: fetch_news.py → HN, GitHub, 36Kr, V2EX, WallStreetCN
  │     │   └─ Tier 2: sensors/* → PH, ArXiv, HF, HN Blogs, TC, MIT-TR
  │     │
  │     └─ Batch 2 (依赖 Batch 1): Grok/X 调用
  │         └─ x_grok_sensor.py → 基于 Batch 1 结果生成 Twitter 分析
  │
  └─→ report_generator.py (渲染)
        └─ 输出 Markdown 日报 → reports/daily_briefings/
```

## 模块职责

### 入口层

| 文件 | 职责 |
|:--|:--|
| `cli.py` | CLI 解析, 串联采集→生成→保存 |

### 核心层 (`src/`)

| 文件 | 职责 |
|:--|:--|
| `config.py` | `IntelConfig` 单例, 优先级: env > .env > defaults |
| `intel_collector.py` | ThreadPoolExecutor 并发调度, 分批执行, 运行时预算报告 |
| `report_generator.py` | Markdown 渲染, 防幻觉标记, 板块组装 |

### 数据采集层

| 路径 | 职责 |
|:--|:--|
| `src/external/fetch_news.py` | Tier 1 聚合器: 5 个源共用一个模块 |
| `src/sensors/*.py` | Tier 2 传感器: 每源一个独立模块 |

### 工具层 (`src/utils/`)

| 文件 | 职责 |
|:--|:--|
| `gemini_translator.py` | Gemini API 调用, 中文翻译 + 摘要生成 |
| `jina_reader.py` | 网页全文提取, DDG 搜索 fallback |
| `verifier.py` | HTTP HEAD 链接有效性验证 |
| `generate_summaries.py` | PWA 前端预烘焙摘要 |

## 设计原则

### 优雅降级

每个传感器 import 失败或 API key 缺失时，标记 `*_AVAILABLE = False` 并跳过，不中断整体流程。

### 防幻觉

当 Product Hunt API 不可用时 fallback 到 Grok 推断。Grok 生成的 URL 是猜测的 slug：
- 报告中标记 `⚠️ 链接未验证 (AI 推断)`
- 不渲染为可点击 markdown 链接
- 提供 Google 搜索链接供人工核实

### 并发分批

```
Batch 1: [HN, GitHub, 36Kr, PH, ArXiv, ...] → 并行
Batch 2: [Grok/X sensor] → 等 Batch 1 完成后执行 (依赖其结果)
```

## 配置

所有配置通过 `IntelConfig` 单例管理：

| 变量 | 默认值 | 说明 |
|:--|:--|:--|
| `GEMINI_MODEL` | `gemini-2.0-flash` | 翻译/摘要模型 |
| `XAI_MODEL` | `x-ai/grok-4-fast` | Grok 模型 |
| `FETCH_TIMEOUT` | `15` | 网络超时 (秒) |
| `LIMIT_PER_SOURCE` | `10` | 每源抓取上限 |
| `CONTENT_TRUNCATE_LIMIT` | `3000` | 内容截断字数 |

## 输出

报告保存至 `reports/daily_briefings/Morning_Report_YYYY-MM-DD.md`，包含 7 大板块：

1. 技术趋势 (HN + GitHub)
2. 资本动向 (36Kr + WallStreetCN)
3. 学术前沿 (ArXiv + HF Papers)
4. 产品精选 (Product Hunt)
5. 社区热议 (V2EX)
6. 社交舆情 (X/Twitter via Grok)
7. 深度洞察 (HN Blogs + TechCrunch + MIT-TR)
