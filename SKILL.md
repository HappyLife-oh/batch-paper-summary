---
name: batch-paper-summary
description: "Batch read PDF academic papers and generate structured Chinese fast-reading summary reports. Includes literature search (Semantic Scholar API), batch PDF extraction, relevance ranking, and 7-section report template (Executive Summary, Research Question, Methodology, Key Findings, Relevance Assessment, Innovations & Limitations, Reading Recommendation). Outputs to Obsidian vault. Triggers: 批量阅读文献, 论文摘要, 快速阅读报告, batch paper summary, paper digest, 文献总结, 文献检索, paper search, 关键词搜索."
metadata:
  version: "1.3.0"
  last_updated: "2026-05-07"
  status: active
  task_type: batch
  related_skills:
    - academic-paper-reviewer
    - deep-research
---

# Batch Paper Summary — 批量文献快速阅读报告生成器

Batch-read PDF academic papers and generate structured Chinese fast-reading summary reports, output to Obsidian vault.

## Workflow

### Phase 0: Literature Search (Optional)

Search for papers by keyword using the Semantic Scholar API:

```bash
python scripts/search_papers.py \
  --query "neural operator mechanical engineering" \
  --top-journals \
  --min-citations 5 \
  --limit 20 \
  --output papers_search_results.md
```

The script returns: title, authors, year, abstract, arXiv ID, DOI, URL, citation count. Results can be saved as a Markdown table for easy browsing.

**Then**: Use the returned DOI/arXiv links to download PDFs, and feed them into Phase 1.

### Phase 1: Preprocessing (User executes once)

Run `scripts/extract_pdfs.py` to extract text, tables, and images from all PDFs in a directory:

```bash
python scripts/extract_pdfs.py --input "D:\Edge\ScienceDirect_articles_06May2026_02-15-34.764" --output "D:\Edge\ScienceDirect_articles_06May2026_02-15-34.764\_extracted"
```

The script creates:
```
_extracted/
├── PaperName1/
│   ├── full_text.txt          # Complete extracted text
│   ├── tables/                # Tables as CSV/JSON
│   │   ├── table_01.csv
│   │   └── table_02.json
│   └── images/                # Embedded images as PNG
│       ├── figure_01.png
│       └── figure_02.png
├── PaperName2/
│   └── ...
└── _extraction_log.json       # Per-file extraction status
```

### Phase 2: Quick Scan & Relevance Ranking

Process all papers **sequentially** in a single pass. For each paper, read `full_text.txt` (focusing on title, abstract, keywords, section headings). Rank all papers into three relevance tiers against the user's research direction (default: 旋压工艺 + ML 预测工艺参数).

**Why sequential:** Relevance ranking requires cross-paper comparison — you cannot reliably assign 高/中/低 without having seen all papers. Splitting across agents would produce inconsistent rankings because each agent only sees a subset.

Present a relevance-ordered table to the user. Ask: "全部处理 or 仅处理高相关度论文?"

**After user confirms**, organize papers into three lists for Phase 3:
- `papers_高`: list of high-relevance papers with their `full_text.txt` paths
- `papers_中`: list of medium-relevance papers with their `full_text.txt` paths
- `papers_低`: list of low-relevance papers with their `full_text.txt` paths

### Phase 3: Deep Read & Generate Reports (Parallel)

Phase 3 uses **parallel agents** — one agent per paper batch. Papers within each relevance category are completely independent at this stage (no shared state, no cross-paper dependencies). This eliminates the context-bloat problem of sequential processing and reduces wall-clock time from ~2 hours to ~15-25 minutes for 100 papers.

#### Step 3.1: Split Papers into Batches

Split each category into optimally-sized batches:

| Relevance | Report Type | Papers per Agent |
|-----------|------------|-------------------|
| 高相关 | Full 7-section (deep read) | 5-8 papers |
| 中相关 | Full 7-section (deep read) | 8-12 papers |
| 低相关 | Condensed 4-section (light read) | 12-20 papers |

**Batching rules:**
- High-relevance papers generate larger per-paper context (full text + tables + images), so smaller batches.
- Low-relevance papers read only abstract/methodology/conclusions, so larger batches are safe.
- If a category has fewer papers than the max batch size, use a single agent.
- If a category splits into multiple batches, track numbering offsets: batch1 starts at 01, batch2 starts at batch1_size+1, etc.

**Example for 100 papers (20 high, 35 medium, 45 low):**
- 高相关: 3 agents (7+7+6 papers)
- 中相关: 4 agents (9+9+9+8 papers)
- 低相关: 3 agents (15+15+15 papers)
- Total: 10 agents running in parallel

#### Step 3.2: Construct Agent Prompts

For EACH batch, construct a **self-contained** agent prompt using the template below. Paste everything the agent needs directly — subagents cannot read SKILL.md or access your session history.

**Agent prompt template:**

```
You are generating structured Chinese fast-reading summary reports for academic papers.

## Your Assigned Papers

You are responsible for the following {N} papers in the **{relevance_category}** category.
Generate one `.md` report for each paper.

### Paper List:
{for each paper:}
- **Paper {index}**: {paper_title}
  - Full text at: `{full_text_path}`
  - Tables at: `{tables_dir}` (if exists)
  - Images at: `{images_dir}` (if exists)

## Reading Depth

{for 高/中:}
Read the FULL `full_text.txt` for each paper. Review key tables and images where available.

{for 低:}
Read ONLY: title, abstract, keywords, methodology section, and conclusions from `full_text.txt`. Do NOT read the full text.

## Report Template

{for 高/中 — paste the full 7-section template from the "Report Template" section:}
---
tags: [文献阅读, 神经算子, <领域标签>]
aliases: [<论文简称>, <英文关键词>]
created: <YYYY-MM-DD>
relevance: <高/中/低>
---

# <论文标题（中译）>

> <英文原标题>
> **期刊**: <期刊名>, <年份> | **作者**: <第一作者> et al.
> **相关度**: <高/中/低>

## 1. 论文核心概要 (Executive Summary)

用三句话总结这篇论文的核心目标、方法和主要发现。

## 2. 研究问题与目标 (Research Question)

这篇论文试图回答的具体科学问题是什么？

## 3. 关键方法与技术 (Methodology)

- **模型架构**: <DeepONet / PINN / FNO / ... >
- **模型输入**: <输入特征>
- **模型输出**: <输出目标>
- **关键技术创新**: <方法上的核心创新点>
- **数据来源**: <训练/测试数据来源>
- **验证方式**: <如何验证模型效果？>

## 4. 主要结论与贡献 (Key Findings & Contributions)

论文得出了哪些重要结论？其学术贡献是什么？

## 5. 与我研究的相关性评估 (Relevance to My Research)

- **总体相关度**: 高 / 中 / 低
- **详细分析**:
  - **高度相关的方面**: <与旋压工艺、ML预测工艺参数的具体关联>
  - **关系不大的方面**: <哪些内容与我的研究方向距离较远>

## 6. 创新点与局限性 (Innovations & Limitations)

- **最主要创新点**:
- **研究局限 / 未来改进方向**:

## 7. 精读建议 (Recommendation)

- **是否推荐精读**: 是 / 否
- **理由**:
- **重点关注章节**: <如果推荐精读，具体关注哪些部分？>

{for 低 — paste a condensed 4-section template:}
---
tags: [文献阅读, 神经算子, <领域标签>]
aliases: [<论文简称>, <英文关键词>]
created: <YYYY-MM-DD>
relevance: 低
---

# <论文标题（中译）>

> <英文原标题>
> **期刊**: <期刊名>, <年份> | **作者**: <第一作者> et al.
> **相关度**: 低

## 1. 论文核心概要 (Executive Summary)

用三句话总结这篇论文的核心目标、方法和主要发现。

## 2. 主要结论与贡献 (Key Findings & Contributions)

论文得出了哪些重要结论？其学术贡献是什么？

## 3. 与我研究的相关性评估 (Relevance to My Research)

- **总体相关度**: 低
- **详细分析**: <简要说明为何相关性低，以及是否有可借鉴的个别方法或思路>

## 4. 精读建议 (Recommendation)

- **是否推荐精读**: 否
- **理由**: <简要说明>
```

## Output Instructions

For each paper, return the complete report content as a code block. Do NOT write files yourself — the main session handles file writing.

**Return format for each paper:**
```
FILENAME: {index:02d}_{paper_short_name}.md
PATH: {output_root}/{relevance_dir}/{index:02d}_{paper_short_name}.md
---CONTENT---
{full markdown report with frontmatter}
---END---
```

File numbering: Start at **{batch_start_index}** and increment for each paper.
(Example: if batch_start_index=1 → 01_xxx.md, 02_xxx.md, ...;
 if batch_start_index=8 → 08_xxx.md, 09_xxx.md, ...)

**MANDATORY rules:**
- Output language: Chinese (中文)
- Use the EXACT template structure provided above — do not skip or reorder sections
- Frontmatter MUST include: tags, aliases, created (today's date YYYY-MM-DD), relevance ({高/中/低})
- Use the FILENAME/PATH/CONTENT/END format exactly as shown for each paper
- Report back with: number of papers processed + list of filenames returned

## Research Context

Research focus (for relevance assessment in Section 5): {research_focus}

## Constraints

- Do NOT write files — return all report content in your response
- Do NOT generate 00_总览索引.md or 99_总结与推荐.md content (Phase 4 handles this)
- If a full_text.txt is unreadable or empty, skip that paper and note it in your final report
```

#### Step 3.3: Dispatch All Agents in Parallel

Use the `Agent` tool to dispatch one agent per batch. Dispatch ALL agents **simultaneously** — they are fully independent.

Key dispatch rules:
- Use `subagent_type: "general-purpose"` for all batches (structured summarization does not need Explore)
- Dispatch all agents in ONE message to ensure true parallelism
- Each agent prompt is the fully-constructed prompt from Step 3.2
- Do NOT wait for one batch before dispatching the next

#### Step 3.4: Collect Results & Write Files

Wait for ALL agents to return. Each agent returns report content directly (not files on disk).

**For each returned report**, extract the FILENAME, PATH, and CONTENT from the structured format. Write the content to disk:
```
Write(file_path=PATH, content=CONTENT)
```

**Verify each agent returned:**
- Number of papers processed
- List of filenames returned
- Any skipped or errored papers

If any agent reports errors or skipped papers, note them for Phase 4 (they will appear as "未完成" in the master index).

**Why this approach:** Subagents may lack file write permission. Returning content to the main session avoids permission issues while keeping report generation (the expensive 95%) fully parallel. File writing is serial but takes milliseconds per file.

**Proceed to Phase 4 ONLY after ALL agents have returned and all files are written.**

### Phase 4: Master Index & Cross-Paper Synthesis

**Precondition:** ALL Phase 3 agents have returned. Verify:
1. Every paper from the Phase 2 ranking list has a corresponding `.md` file in the expected relevance subdirectory
2. No agent is still running (all Agent dispatches have returned)

If any papers are missing (agent failure), note them as "未完成" in the index.

#### Step 4.1: Discover Generated Reports

Scan the output directory to discover all generated `.md` files:
```
<output_root>/
├── 高相关/01_xxx.md, 02_xxx.md, ...
├── 中相关/01_xxx.md, 02_xxx.md, ...
└── 低相关/01_xxx.md, 02_xxx.md, ...
```

For each `.md` file, read ONLY: frontmatter (`relevance`, `title`) and Section 1 (Executive Summary). This gives you all data needed for the master index without re-reading every full report.

#### Step 4.2: Generate Master Index

Generate **`00_总览索引.md`** at the root of the output directory:
- Summary table of all papers, sorted by relevance (高 → 中 → 低), with one-line takeaways from Section 1
- Use relative wikilinks: `[[高相关/01_xxx|Display Name]]`
- Include status column: "已完成" or "未完成" for any papers agents couldn't process

#### Step 4.3: Generate Cross-Paper Synthesis

Generate **`99_总结与推荐.md`** at the root of the output directory:
- Cross-paper analysis: common themes, methodological trends, gaps, and prioritized reading recommendations
- Draw from Section 1 and Section 5 of each report (read relevant sections, not full reports)
- Highlight the top 3-5 most relevant papers with detailed justification

This phase runs sequentially — it must integrate output from all Phase 3 agents.

---

## Trigger Conditions

### Trigger Keywords

**中文**: 批量阅读文献, 论文摘要, 快速阅读报告, 文献总结, 论文总结, 读论文, 生成文献报告, 文献阅读整理

**English**: batch paper summary, paper digest, batch read papers, generate paper summaries, literature fast read

### Does NOT Trigger

| Scenario | Use Instead |
|----------|-------------|
| Writing a new academic paper | `academic-paper` |
| Peer review / structured review | `academic-paper-reviewer` |
| Deep research / literature search | `deep-research` |

---

## Report Template (7 Sections)

Each paper summary MUST follow this exact structure. Output language: **Chinese**.

```markdown
---
tags: [文献阅读, 神经算子, <领域标签>]
aliases: [<论文简称>, <英文关键词>]
created: <YYYY-MM-DD>
relevance: <高/中/低>
---

# <论文标题（中译）>

> <英文原标题>
> **期刊**: <期刊名>, <年份> | **作者**: <第一作者> et al.
> **相关度**: <高/中/低>

## 1. 论文核心概要 (Executive Summary)

用三句话总结这篇论文的核心目标、方法和主要发现。

## 2. 研究问题与目标 (Research Question)

这篇论文试图回答的具体科学问题是什么？

## 3. 关键方法与技术 (Methodology)

- **模型架构**: <用了什么模型？DeepONet / PINN / FNO / ... >
- **模型输入**: <输入是什么？>
- **模型输出**: <输出是什么？>
- **关键技术创新**: <方法上的核心创新点>
- **数据来源**: <训练/测试数据从哪里来？>
- **验证方式**: <如何验证模型效果？>

## 4. 主要结论与贡献 (Key Findings & Contributions)

论文得出了哪些重要结论？其学术贡献是什么？

## 5. 与我研究的相关性评估 (Relevance to My Research)

- **总体相关度**: 高 / 中 / 低
- **详细分析**:
  - **高度相关的方面**: <与旋压工艺、ML预测工艺参数的具体关联>
  - **关系不大的方面**: <哪些内容与我的研究方向距离较远>

## 6. 创新点与局限性 (Innovations & Limitations)

- **最主要创新点**:
- **研究局限 / 未来改进方向**:

## 7. 精读建议 (Recommendation)

- **是否推荐精读**: 是 / 否
- **理由**:
- **重点关注章节**: <如果推荐精读，具体关注哪些部分？>
```

---

## Output Structure

Reports are organized by relevance level for clean hierarchy management:

```
<Obsidian目标目录>/
├── 00_总览索引.md                 # Master index: relevance-ranked table + one-line takeaways
├── 99_总结与推荐.md               # Cross-paper synthesis & reading recommendations
├── 高相关/
│   ├── 01_<论文简称1>.md          # Deep-read, full 7-section report
│   ├── 02_<论文简称2>.md
│   └── ...
├── 中相关/
│   ├── 01_<论文简称1>.md          # Deep-read, full 7-section report
│   ├── 02_<论文简称2>.md
│   └── ...
└── 低相关/
    ├── 01_<论文简称1>.md          # Light-read, condensed 4-section report
    ├── 02_<论文简称2>.md
    └── ...
```

**Rules**:
- High/Medium relevance papers get full 7-section reports; Low relevance get condensed 4-section reports
- Files within each subdirectory are numbered independently by processing order
- `00_总览索引.md` and `99_总结与推荐.md` sit at root level for quick access
- Wikilinks in `00_总览索引.md` use relative paths (e.g., `[[高相关/01_xxx]]`)

---

## Agent Dispatch Reference

### Why Parallel Agents for Phase 3

Phase 3 paper processing is **embarrassingly parallel** — each paper's report is generated independently with no shared state between papers. Sequential processing causes three problems:

1. **Context bloat**: Each paper's full text accumulates in the context window, slowing inference for later papers
2. **Linear wall-clock time**: 100 papers x ~1.2 min/paper ≈ 2 hours sequentially
3. **Error propagation**: A mistake on paper 5 creates confusion for paper 6+

Parallel agents solve all three: each agent starts with a clean context, runs concurrently, and errors are isolated.

### Batch Sizing Logic

Target: keep each agent's total context under 100K tokens for optimal inference speed.

| Factor | Estimate |
|--------|----------|
| Agent prompt + template | ~3K tokens |
| Full paper text (typical) | ~10K-20K tokens |
| Report output (per paper) | ~1K-2K tokens |
| Safe capacity at 100K | ~5-8 full papers |

**Formula:** `batch_size = min(category_paper_count, floor(80K / estimated_paper_tokens))`

For low-relevance (light read): estimated_paper_tokens is ~3K-5K (abstract+method+conclusion only), so batches of 12-20 are safe.

### Agent Tool Usage

Use the `Agent` tool to dispatch subagents. Each dispatch creates a fresh subagent with isolated context. The subagent CANNOT access your session history, the SKILL.md file, or other agents' work — this ensures clean separation.

```
// Example dispatch for 3 parallel batches
Agent(description="Batch: 高相关 papers 1-7", subagent_type="general-purpose", prompt=<constructed prompt>)
Agent(description="Batch: 中相关 papers 1-9", subagent_type="general-purpose", prompt=<constructed prompt>)
Agent(description="Batch: 低相关 papers 1-15", subagent_type="general-purpose", prompt=<constructed prompt>)
```

Dispatch all agents in ONE message to ensure true parallelism.

### Phase 2: Why NOT Parallel

Phase 2 ranking is inherently sequential. Relevance is relative — "high relevance" only means something in comparison to other papers. If you split papers across agents, each agent ranks within its own subset, and you cannot merge the rankings without the controller reading all papers again. The 5-10 minutes spent in Phase 2 is not the bottleneck (Phase 3 takes 24x longer).

### Agent File Write Permission

The Phase 3 prompt template defaults to **Option A:** agents return report content directly in their response, and the main session writes the `.md` files. This avoids subagent file-write permission issues entirely.

If you prefer agents to write files directly (requires auto-approved write permissions), change the Output Instructions in Step 3.2 from "return content" to "create a file at" and remove the "Do NOT write files" constraint.

### Error Handling

If a Phase 3 agent fails (timeout, error, incomplete output):
1. Note which papers were missed
2. In Phase 4, mark those papers as "未完成" in the master index
3. Optionally re-dispatch a single agent for just the missed papers
4. Do NOT re-run the entire batch

---

## Configuration

The following defaults can be overridden per session:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `pdf_directory` | User specifies | Directory containing PDF files |
| `output_directory` | `D:\Obsidian\file_storage\Abaqus\文献阅读整理\神经算子\` | Obsidian vault output path |
| `research_focus` | 旋压工艺 + ML 预测工艺参数 | Used for relevance assessment |
| `report_language` | Chinese (中文) | Output language |
| `relevance_threshold` | 高/中 → deep read; 低 → light read | Which papers get full treatment |
