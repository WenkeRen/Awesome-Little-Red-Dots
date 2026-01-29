# AI Bot for LRD Paper Ranking

Automated system for ranking Little Red Dot (LRD) research papers by relevance using AI backends (Volcengine ARK or Google Gemini). This system evaluates papers based on domain-specific criteria to help curate the most relevant literature for NotebookLM and other research tools.

## Overview

This AI-powered ranking system addresses a critical challenge: the LRD bibliography has grown to 176+ papers, exceeding NotebookLM's 300-source limit. The solution uses intelligent scoring to identify the most essential papers for focused study.

### Key Features

- **Dual Backend Support**: Choose between Volcengine ARK (Kimi models) or Google Gemini
- **Domain-Aware Scoring**: Uses LRD-specific criteria (observational techniques, physical properties, scientific impact)
- **Text-Based Analysis**: Evaluates title, abstract, and existing tags - no PDF uploads required
- **Robust Error Handling**: Retry logic with exponential backoff for API reliability
- **Comprehensive Reports**: JSON output with scores, justifications, and key factors
- **Non-Destructive**: Does not modify BibTeX files - results are separate reports

## Quick Start

### 1. Install Dependencies

```bash
# From repository root
poetry install

# Or manually
pip install volcenginesdkarkruntime pybtex python-dotenv tqdm
```

### 2. Configure API Key

**For Volcengine ARK (Recommended Default):**

```bash
cp AIBot/.env.example .env
# Edit .env and add your ARK_API_KEY
```

Get your key from: https://ark.cn-beijing.volces.com/

**For Google Gemini (Alternative):**

```bash
# Edit .env and add your GEMINI_API_KEY
```

Get your API key from: https://makersuite.google.com/app/apikey

### 3. Test on Small Sample

**Using Volcengine (default):**
```bash
cd AIBot
python paper_ranker.py --backend volcengine --test-mode --limit 10
```

**Using Gemini:**
```bash
python paper_ranker.py --backend gemini --test-mode --limit 10
```

This will:
- Process only the first 10 papers
- Show ranking results and top papers
- Generate `AIBot/ranking_report.json`

## Choosing the AI Backend

### Volcengine ARK API (Default)

**Model**: `kimi-k2-thinking-251104`

**Advantages**:
- Enhanced reasoning capabilities with "thinking" models
- Often faster response times
- Cost-effective pricing

**Setup**:
```bash
export ARK_API_KEY="your-key-here"
python paper_ranker.py --backend volcengine --full
```

### Google Gemini (Alternative)

**Model**: `gemini-2.5-flash`

**Advantages**:
- Mature, well-documented API
- Multiple model options (flash, pro)
- Good multilingual support

**Setup**:
```bash
export GEMINI_API_KEY="your-key-here"
python paper_ranker.py --backend gemini --full
```

### Switching Between Backends

Simply add the `--backend` flag:

```bash
# Use Volcengine (default)
python paper_ranker.py --backend volcengine --full

# Use Gemini
python paper_ranker.py --backend gemini --full
```
- Take approximately 20-30 seconds

### 4. Full Ranking Run

```bash
python paper_ranker.py --full
```

This will:
- Process all 176 papers in `library/aslrd.bib`
- Take approximately 5-10 minutes (2-3 seconds per paper)
- Generate complete ranking report

## Files and Structure

```
AIBot/
├── README.md                    # This file
├── .env.example                # API key template
├── lrd_ranking_criteria.json   # Scoring rubric (read by agent)
├── gemini_client.py            # Google AI API wrapper
├── paper_ranker.py             # Main ranking script
└── ranking_report.json         # Output report (after running)
```

## Usage

### Basic Usage

```bash
# Test mode (10 papers)
python paper_ranker.py --test-mode --limit 10

# Full processing (all papers)
python paper_ranker.py --full

# Custom BibTeX file
python paper_ranker.py --bib-file path/to/biblio.bib

# Custom output path
python paper_ranker.py --output results/my_ranking.json

# Show top 20 papers instead of 10
python paper_ranker.py --show-top 20
```

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--bib-file` | Path to BibTeX file | `library/aslrd.bib` |
| `--output` | Output JSON report path | `AIBot/ranking_report.json` |
| `--criteria` | Path to ranking criteria JSON | `AIBot/lrd_ranking_criteria.json` |
| `--limit N` | Process only first N papers | All papers |
| `--test-mode` | Enable test mode (shows summary) | False |
| `--show-top N` | Number of top papers to display | 10 |
| `--model` | Gemini model to use | `gemini-2.0-flash-exp` |

## Scoring System

### Score Categories

Papers are evaluated across 5 weighted categories:

1. **Core LRD Focus** (40%): How directly the paper studies LRDs
2. **Observational Techniques** (20%): Quality and relevance of data used
3. **Physical Properties** (15%): Depth of analysis on LRD properties
4. **Scientific Impact** (15%): Novelty and advancement of understanding
5. **Methodological Rigor** (10%): Sample size and analytical quality

### Score Interpretation

| Score Range | Label | NotebookLM Action |
|-------------|-------|-------------------|
| **9-10** | Central / Seminal | Must include (top priority) |
| **7-8** | High Relevance | High priority for inclusion |
| **4-6** | Moderate Relevance | Include if space permits |
| **0-3** | Peripheral / Low | Exclude from NotebookLM |

### Key Evaluation Criteria

**Indicators of High Relevance:**
- Direct JWST NIRSpec spectroscopy
- Large, well-defined LRD samples (N > 50)
- Black hole mass and Eddington ratio measurements
- Resolves key debates (AGN vs starburst nature)
- Multi-wavelength analysis (X-ray, radio, ALMA)
- Published in high-impact journals

**Indicators of Low Relevance:**
- Only mentions LRDs in literature review
- No original LRD data or analysis
- Focuses on different galaxy types
- Redshift mismatch (z < 2 vs LRD's z > 4)

## Output Format

The `ranking_report.json` contains:

```json
{
  "generated_at": "2025-01-29T...",
  "total_papers": 176,
  "successfully_scored": 175,
  "papers": [
    {
      "bibtex_key": "2025MNRAS.539.2910P",
      "title": "...",
      "abstract": "...",
      "year": "2025",
      "existing_tags": "jwst, spectroscopy, black hole mass",
      "relevance_score": 8.5,
      "justification": "Direct observational study...",
      "key_factors": [
        "JWST NIRSpec data",
        "Large sample size",
        "BH mass measurements"
      ],
      "category_scores": {
        "core_lrd_focus": {"score": 9.0, "reasoning": "..."},
        "observational_techniques": {"score": 9.5, "reasoning": "..."},
        ...
      },
      "notebooklm_recommendation": "High priority for NotebookLM"
    }
  ],
  "statistics": {
    "average_score": 6.7,
    "median_score": 7.2,
    "high_relevance_count": 45,
    "moderate_relevance_count": 89,
    "low_relevance_count": 41
  }
}
```

## Using the Ranking Report

### Select Papers for NotebookLM

```python
import json

# Load report
with open('AIBot/ranking_report.json', 'r') as f:
    report = json.load(f)

# Get top 300 papers for NotebookLM
top_papers = [p for p in report['papers'] if p['relevance_score'] >= 7.0][:300]

# Extract BibTeX keys for filtering
bibtex_keys = [p['bibtex_key'] for p in top_papers]
print(f"Selected {len(bibtex_keys)} papers for NotebookLM")
```

### Generate Top Papers List

```bash
# Show top 50 papers
python paper_ranker.py --full --show-top 50
```

### Filter by Score

```python
# High relevance papers (score >= 7)
high_relevance = [p for p in report['papers'] if p['relevance_score'] >= 7]

# Papers with specific techniques
jwst_spectroscopy = [
    p for p in report['papers']
    if 'JWST' in p['justification'] and 'spectroscopy' in str(p['key_factors']).lower()
]
```

## Troubleshooting

### Common Issues

**Error: `GEMINI_API_KEY not found`**
- Ensure `.env` file exists in repository root
- Check that `GEMINI_API_KEY=your_key` is set
- Verify the API key is valid

**Error: `Ranking criteria file not found`**
- Ensure `AIBot/lrd_ranking_criteria.json` exists
- Check file path if using custom `--criteria` argument

**Error: `BibTeX file not found`**
- Verify `library/aslrd.bib` exists
- Check path if using custom `--bib-file` argument

**Timeout or API errors:**
- Script automatically retries 3 times with exponential backoff
- Check internet connection
- Verify Google API quota (free tier: 15 requests/minute)
- If rate-limited, wait a few minutes and retry

**Low score results:**
- Review `lrd_ranking_criteria.json` and adjust if needed
- Check prompt template in criteria file
- Some papers may genuinely have low relevance

### Testing API Connection

```python
# Test the Gemini client directly
from AIBot.gemini_client import test_client
test_client()  # Uses sample paper
```

## Integration with Existing Workflow

### Current Pipeline

```
1. library/lrd_ads_request.py → Fetch new papers from ADS
2. library/paper_kwd.py → Add AI tags (Qwen-Max)
3. library/kick_off_papers.py → Update related references
```

### Adding Ranking (Optional)

```yaml
# .github/workflows/update_bibliography.yml
- name: Rank LRD Papers
  run: |
    cd AIBot
    python paper_ranker.py --full
  env:
    GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
```

## Performance and Costs

### Processing Speed

- **Per paper**: 2-3 seconds (including API latency)
- **10 papers**: ~20-30 seconds
- **176 papers**: ~5-10 minutes

### API Costs

- **Model**: `gemini-2.5-flash` (fast, cost-effective)
- **Estimated cost**: Free tier typically sufficient for 176 papers
- **Quota**: 15 requests/minute on free tier (script respects this)

### Resource Usage

- **Memory**: Minimal (text-only, no PDF uploads)
- **Network**: ~1-2 KB per paper (title + abstract + tags)
- **Storage**: ranking_report.json ~500 KB for 176 papers

## Customization

### Modifying Scoring Criteria

Edit `AIBot/lrd_ranking_criteria.json`:

```json
{
  "scoring_categories": [
    {
      "name": "Custom Category",
      "weight": 0.10,
      "description": "Your custom criteria",
      "evaluation_criteria": [...]
    }
  ]
}
```

### Changing Prompt Template

The prompt template is in `lrd_ranking_criteria.json` under `usage_instructions.prompt_template`. Modify to adjust AI behavior.

### Using Different Gemini Models

```bash
# Use latest stable model (default)
python paper_ranker.py --model gemini-2.5-flash

# Use more powerful model (slower, higher cost)
python paper_ranker.py --model gemini-2.5-pro
```

## Development

### Code Structure

- **`gemini_client.py`**: Low-level API wrapper
  - `GeminiRankingClient`: Main client class
  - Retry logic, JSON parsing, error handling
  - `test_client()`: Standalone test function

- **`paper_ranker.py`**: High-level ranking script
  - BibTeX parsing with pybtex
  - Batch processing with progress bars
  - Report generation and statistics
  - CLI interface with argparse

### Testing

```bash
# Unit test client
python -m AIBot.gemini_client

# Integration test (10 papers)
python AIBot/paper_ranker.py --test-mode --limit 10

# Full test
python AIBot/paper_ranker.py --full
```

## Future Enhancements

Potential improvements:

1. **Batch API calls**: Process multiple papers in parallel (respecting rate limits)
2. **Caching**: Store API responses to avoid re-scoring unchanged papers
3. **PDF analysis**: Option to upload PDFs for deeper content analysis
4. **Visualization**: Generate plots showing score distribution, trends
5. **Website integration**: Display scores on Jekyll website
6. **Auto-filtering**: Create `aslrd_top300.bib` automatically

## Related Tools

- **`library/paper_kwd.py`**: Adds AI tags using Qwen-Max API
- **`library/lrd_ads_request.py`**: Fetches papers from NASA ADS
- **NotebookLM**: https://notebooklm.google.com - Source-grounded AI research

## Citation

If you use this ranking system in your research, please cite the [Awesome-Little-Red-Dots repository](https://github.com/WenkeRen/Awesome-Little-Red-Dots).

## License

This project is part of Awesome-Little-Red-Dots and follows the same license.

## Contact

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Last Updated**: 2025-01-29
**Maintainer**: Awesome-Little-Red-Dots Project
