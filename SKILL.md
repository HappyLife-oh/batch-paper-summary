---
name: batch-paper-summary
description: "Batch read PDF academic papers and generate structured Chinese fast-reading summary reports. 7-section report template (Executive Summary, Research Question, Methodology, Key Findings, Relevance Assessment, Innovations & Limitations, Reading Recommendation). Outputs to Obsidian vault. Triggers: 批量阅读文献, 论文摘要, 快速阅读报告, batch paper summary, paper digest, 文献总结."
metadata:
  version: "1.0.0"
  last_updated: "2026-05-06"
  status: active
  task_type: batch
  related_skills:
    - academic-paper-reviewer
    - deep-research
---

# Batch Paper Summary — 批量文献快速阅读报告生成器

Batch-read PDF academic papers and generate structured Chinese fast-reading summary reports, output to Obsidian vault.

## Workflow

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

For each paper, read `full_text.txt` (focusing on title, abstract, keywords, section headings). Rank all papers by relevance to the user's research direction (default: 旋压工艺 + ML 预测工艺参数).

Present a relevance-ordered table to the user. Ask: "全部处理 or 仅处理高相关度论文?"

### Phase 3: Deep Read & Generate Report

Read papers in relevance order. For high-relevance papers: read full extracted text + review key tables/images. For medium/low: read abstract + methodology + conclusions.

Generate one `.md` file per paper using the 7-section template below. Output to the user's Obsidian vault (default: `D:\Obsidian\file_storage\Abaqus\文献阅读整理\神经算子\`).

### Phase 4: Master Index & Cross-Paper Synthesis

Generate two final files:
- **`00_总览索引.md`** — Summary table of all papers, sorted by relevance, with one-line takeaways
- **`99_总结与推荐.md`** — Cross-paper analysis: common themes, methodological trends, gaps, and prioritized reading recommendations

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

```
<Obsidian目标目录>/
├── 00_总览索引.md            # Master index: relevance-ranked table + one-line takeaways
├── 01_<论文简称1>.md         # Individual paper summary
├── 02_<论文简称2>.md
├── ...
└── 99_总结与推荐.md           # Cross-paper synthesis & reading recommendations
```

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
