# batch-paper-summary

Batch-read PDF academic papers and generate structured Chinese fast-reading summary reports for Obsidian.

## What It Does

1. **Extracts** text, tables, and embedded images from all PDFs in a directory
2. **Ranks** papers by relevance to your research direction
3. **Generates** a 7-section structured Chinese summary for each paper
4. **Outputs** markdown files to your Obsidian vault, with a master index and cross-paper synthesis

## Installation

```bash
# Clone to Claude Code skills directory
git clone https://github.com/<your-username>/batch-paper-summary.git "%USERPROFILE%\.claude\skills\batch-paper-summary"

# Install Python dependencies
pip install -r "%USERPROFILE%\.claude\skills\batch-paper-summary\scripts\requirements.txt"
```

## Quick Start

### Step 1: Extract PDFs

```bash
python scripts/extract_pdfs.py \
  --input "D:\your\pdf\folder" \
  --output "D:\your\pdf\folder\_extracted"
```

### Step 2: Generate Summaries

In Claude Code, say:
```
读一下 D:\your\pdf\folder 里的论文，输出到我的 Obsidian
```

The skill auto-triggers and follows the report template.

## Report Structure (7 Sections)

| # | Section | Description |
|---|---------|-------------|
| 1 | Executive Summary | Three-sentence core summary |
| 2 | Research Question | Specific scientific question |
| 3 | Methodology | Model architecture, input/output, data, validation |
| 4 | Key Findings & Contributions | Main conclusions and academic contribution |
| 5 | Relevance to My Research | High/Medium/Low + detailed alignment analysis |
| 6 | Innovations & Limitations | Main innovation + known limitations |
| 7 | Reading Recommendation | Should you deep-read? Which sections? |

## Output

```
<obsidian_vault>/
├── 00_总览索引.md           # Master index with relevance ranking (wikilinks to subdirs)
├── 99_总结与推荐.md         # Cross-paper synthesis & recommendations
├── 高相关/
│   ├── 01_<PaperName>.md    # Full 7-section report
│   └── ...
├── 中相关/
│   ├── 01_<PaperName>.md    # Full 7-section report
│   └── ...
└── 低相关/
    ├── 01_<PaperName>.md    # Condensed 4-section report
    └── ...
```

## Dependencies

- Python 3.9+
- [pdfplumber](https://github.com/jsvine/pdfplumber) — text + table extraction
- [PyMuPDF](https://github.com/pymupdf/PyMuPDF) — image extraction

## License

MIT
