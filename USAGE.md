# Running the EpiBench-1.0 Benchmark

This guide explains how to run EpiBench-1.0 against LLM/agent backends and read
the resulting scores. For the benchmark specification (tasks, scoring rubric,
data sources), see [README.md](README.md).

## Requirements

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- An API key for at least one provider (or a local OpenAI-compatible server)

## Installation

```bash
# Install the package with all bundled providers
uv sync --extra all

# …or install only the provider(s) you need
uv sync --extra openai
uv sync --extra anthropic
uv sync --extra gemini

# Without uv (pip works too)
pip install -e ".[all]"
```

Verify the install:

```bash
epibench --version
epibench list-tasks
```

## Configuring providers

API keys are read from environment variables:

| Provider        | Environment variable          | Spec prefix  |
|-----------------|-------------------------------|--------------|
| OpenAI          | `OPENAI_API_KEY`              | `openai:`    |
| Anthropic       | `ANTHROPIC_API_KEY`           | `anthropic:` |
| Google Gemini   | `GEMINI_API_KEY` *(or `GOOGLE_API_KEY`)* | `gemini:` |
| OpenRouter      | `OPENROUTER_API_KEY`          | `openrouter:`|
| Ollama / vLLM / LM Studio | *(no key for local)* | `openai:<base_url>:` |

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=...
```

### Optional: PMID verification

Citation scoring verifies PMIDs against PubMed via NCBI E-utilities. For polite,
higher-rate usage, set:

```bash
export NCBI_EMAIL=you@example.com
export NCBI_API_KEY=...     # optional, raises rate limit
```

To disable all network calls during scoring (e.g. for offline runs), set
`EPIBENCH_NETWORK_SCORING=0`. Unverifiable PMIDs are then treated as
"unknown" rather than fabricated.

## Model spec syntax

A model is selected with a `provider:model` spec string:

| Spec                                                | Meaning                          |
|-----------------------------------------------------|----------------------------------|
| `openai:gpt-4o`                                     | OpenAI hosted model              |
| `anthropic:claude-sonnet-4-5`                       | Anthropic Claude                 |
| `gemini:gemini-2.0-flash`                           | Google Gemini                    |
| `openrouter:anthropic/claude-3.5-sonnet`            | Any OpenRouter model             |
| `openai:http://localhost:11434/v1:llama3`           | Ollama (or any OpenAI-compatible endpoint) |
| `dummy:demo`                                        | Offline echo backend (no API key needed — handy for testing the pipeline) |

For a non-default OpenAI base URL (`OPENAI_BASE_URL`), you can also export it
and use the short `openai:<model>` form.

## Running tasks

### Run the full benchmark

```bash
epibench run --model openai:gpt-4o --tasks all
```

### Run a subset of tasks

```bash
# Specific task ids
epibench run --model anthropic:claude-sonnet-4-5 --tasks T01,T03,T16

# By difficulty level
epibench run --model gemini:gemini-2.0-flash --tasks bronze,silver

# Mixed (deduped, order-preserving)
epibench run --model openai:gpt-4o --tasks T01;gold
```

Levels: `bronze`, `silver`, `gold`, `platinum`.

### Compare models

Each run is appended to a cumulative leaderboard:

```bash
epibench compare
```

### List tasks

```bash
epibench list-tasks                 # all 21
epibench list-tasks --level gold    # filtered
```

## Output layout

Runs are written under `results/` (gitignored by default):

```
results/
├── leaderboard.json
├── leaderboard.csv
└── runs/<timestamp>_<model>/
    ├── run.json          # manifest: model, totals, tier, per-task summary
    ├── summary.csv       # one row per task
    └── tasks/
        ├── T01.json      # prompt, full response, latency, tokens,
        ├── T02.json      #   category scores, penalties, human-review flags
        └── ...
```

Override the output directory with `--results-dir` or `EPIBENCH_RESULTS_DIR`.

## Reading a score

Each per-task JSON records the full scoring breakdown:

- `score.final` — the task's final score after weights and penalties (0..max_points)
- `score.raw_positive` — weighted positive score before penalties
- `score.category_scores` — the five weighted categories (data retrieval 35%,
  methodology 30%, interpretation 20%, visualization 10%, citations 5%); a
  `null` entry means that category requires human review
- `score.penalties` — applied critical-error deductions (e.g.
  `fabricated_citation: -10`); see README §5.2
- `score.privacy_violation` — `true` means automatic task failure
- `score.needs_human_review` — `true` means a human reviewer must grade part of
  the task (interpretation, methodology rigor, report structure, visualization
  integrity — see README §6)
- `auto.extracted_pmids` / `auto.verified_pmids` — citations found and verified

The `run.json` manifest aggregates per-task results into a total score and an
overall tier (S / A / B / C / D / F, or `Disqualified` on any privacy
violation).

## Reference answers

Automated scoring requires reference answers in `data/reference_answers/T##.json`
(one file per task; schema in
[`data/reference_answers/SCHEMA.md`](data/reference_answers/SCHEMA.md)). Tasks
without a reference file are scored `0` and flagged `needs_human_review` — they
are still run and their full model output is captured for later grading.

To enable auto-scoring for a task, add a `T##.json` such as:

```json
{
  "task_id": "T03",
  "expected_values": {"incidence_rate": 123.4},
  "expected_sources": ["SINAN"],
  "minimum_required_pmids": 0
}
```

## Example: a quick offline dry run

No API key is required for this — it exercises the whole pipeline end-to-end:

```bash
EPIBENCH_NETWORK_SCORING=0 epibench run --model dummy:demo --tasks bronze
epibench compare
```

## Scoring model (summary)

See [README.md §5](README.md#5-scoring-framework) for the full specification.

| Category                  | Weight | How it's graded                            |
|---------------------------|--------|--------------------------------------------|
| Data Retrieval & Quality  | 35%    | Source attribution + reference values      |
| Methodological Correctness| 30%    | Numerical accuracy tiers + method credit   |
| Interpretation & Insights | 20%    | Human review                               |
| Visualization             | 10%    | Human review                               |
| Citations & References    | 5%     | PMID verification against PubMed           |

Critical-error penalties (stackable, floored at 0, capped at task max):
fabricated citation −10, incorrect source −5, misleading visualization −5,
unit/scale error −3, **privacy violation −20 / automatic failure**.

Overall tier (percentage of 610 total points): S ≥90%, A 75–89%, B 60–74%,
C 40–59%, D 20–39%, F <20%.
