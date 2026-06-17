# Reference Answers — Schema

EpiBench-1.0's reference answers are published separately. When a file
`T##.json` is present in this directory, the auto-scorer will use it to score
the corresponding task; otherwise the task is marked `needs_human_review`.

## File name

One file per task: `T01.json`, `T02.json`, …, `T21.json`.

## JSON schema

All fields are optional except `task_id`. The scorer only uses the parts that
are present.

```jsonc
{
  // Required. Must match the filename stem.
  "task_id": "T01",

  // §5.3 numerical metrics. The scorer extracts labeled numbers from the
  // model response (e.g. "Incidence rate: 123.4") and compares each against
  // the reference value using the README's deviation tiers.
  "expected_values": {
    "incidence_rate": 123.4,
    "case_fatality_rate": 0.05
  },

  // Known-good PMIDs for this task. Used to give credit for citing real
  // literature. (PMIDs cited by the model that are NOT in PubMed at all are
  // treated as fabricated and trigger the −10 penalty.)
  "expected_pmids": [36631231, 12345678],

  // Minimum number of distinct PMIDs the response must cite (e.g. 3 for the
  // Platinum report tasks). Citation credit = min(1, cited/required).
  "minimum_required_pmids": 3,

  // Canonical data-source names the response must reference (SINAN, SIM,
  // WHO, ...). Used for the data-retrieval category and the incorrect-source
  // (−5) penalty.
  "expected_sources": ["SINAN", "SIM", "SINASC"],

  // Free-text keywords describing the expected methodology. (Reserved for a
  // future LLM-as-judge pass; not used by the current deterministic scorer.)
  "methodology_keywords": ["age_standardization", "direct_method"],

  // Free-form notes for human reviewers.
  "notes": "Population denominators from IBGE 2022 census estimates."
}
```

## How scoring uses each field

| Field                  | Scored automatically? | Where in README |
|------------------------|-----------------------|-----------------|
| `expected_values`      | yes — numerical tiers | §5.3            |
| `expected_pmids`       | yes — PMID existence  | §6, §5.2        |
| `minimum_required_pmids` | yes — citation count | §5.1            |
| `expected_sources`     | yes — source attribution | §5.1, §5.2    |
| `methodology_keywords` | no — future LLM judge | §5.3            |
| `notes`                | no — reviewer only    | n/a             |

## Categories always deferred to human review

Per README §6, these are never auto-scored regardless of the reference file:

- **Interpretation & Insights** (20%)
- **Visualization & Communication** (10%) — chart type, axis labels, integrity
- **Methodological rigor** beyond numerical correctness (correct-method vs.
  correct-result disambiguation in §5.3)
- **Report structure & clarity** (Platinum tasks)
