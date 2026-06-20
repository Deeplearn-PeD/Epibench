# Epibench
A Public Benchmark for AI Agents in Public Health and Epidemiology


## Abstract
**Background:** The rapid deployment of large language models (LLMs) and autonomous AI agents in health-related domains has outpaced the development of rigorous, domain-specific evaluation frameworks. Existing medical benchmarks (MMLU-Medical, USMLE, MedMCQA) assess static knowledge recall and clinical reasoning on curated question sets but do not evaluate the ability to interact with live data infrastructure, perform multi-step analytical workflows, or produce evidence-based outputs grounded in real epidemiological data. **Objective:** EpiBench-1.0 is the first publicly available benchmark specifically designed to evaluate AI *agents* — as opposed to passive language models — on practical public health and epidemiology tasks. It introduces a four-dimensional evaluation framework spanning data discovery, descriptive epidemiology, advanced multi-source analytics, and end-to-end professional reporting. **Methods:** The benchmark comprises 21 tasks organized across four difficulty levels (Bronze, Silver, Gold, Platinum) that collectively assess 12 competency areas — from heterogeneous data retrieval across 10+ international health data systems (DATASUS, WHO, ECDC, Mosqlimate, Malaria Atlas Project, Pathoplexus, World Bank, Eurostat, PAHO, HealthData.gov) to descriptive and inferential epidemiology, geospatial analysis, genomic surveillance integration, scientific citation verification, and professional report generation. Tasks require agents to download real data, compute epidemiological metrics (incidence, mortality, case-fatality rates), generate publication-quality visualizations (choropleth maps, temporal series, demographic breakdowns), and produce structured reports with PubMed-verified references. The scoring framework employs a weighted competency model (Data Retrieval 35%, Methodological Correctness 30%, Interpretation 20%, Visualization 10%, Citations 5%), complemented by negative-score penalties for critical errors (fabricated citations, misleading visualizations, privacy violations) and a five-tier granular partial credit system that distinguishes numerical accuracy from methodological validity. **Results:** The maximum achievable score is 610 points across 21 tasks, with a seven-tier classification scale ranging from S-Tier (production-ready AI epidemiologist, ≥90%) to F-Tier (non-functional, <20%) and an automatic disqualification category for privacy violations. Human-expert evaluation components are defined alongside automatable grading pipelines for numerical accuracy, citation verification, and critical error detection. **Conclusions:** EpiBench-1.0 addresses a critical gap in AI evaluation by providing a transparent, reproducible, and publicly accessible benchmark that tests the full spectrum of capabilities required for AI-assisted epidemiological practice. It establishes baseline expectations for AI agents operating in public health contexts and provides a roadmap for iterative refinement in future releases (EpiBench-2.0 and 3.0). The benchmark is designed as an open-science initiative, with task specifications, scoring rubrics, and reference answers intended for community review and contribution.

**Keywords:** AI evaluation benchmark; artificial intelligence agents; public health surveillance; epidemiological methods; multi-source data integration; disease surveillance; automated grading; weighted scoring; DATASUS; WHO Global Health Observatory; Mosqlimate; genomic epidemiology; citation verification; data quality assessment; spatial analysis; temporal analysis; visualization standards; health informatics; open science; EpiBench

## Table of Contents

1. [1. Introduction and Motivation](#1-introduction-and-motivation)
2. [2. Benchmark Design — Four-Dimensional Framework](#2-benchmark-design--four-dimensional-framework)
3. [3. Task Specifications — Full Detail](#3-task-specifications--full-detail)
4. [4. Task Specifications — Platinum Level](#4-task-specifications--platinum-level)
5. [5. Scoring Framework](#5-scoring-framework)
6. [6. Evaluation Protocol](#6-evaluation-protocol)
7. [7. Reference Answers and Automated Grading](#7-reference-answers-and-automated-grading)
8. [8. Required Data Sources and Infrastructure](#8-required-data-sources-and-infrastructure)
9. [9. Comparison with Existing Benchmarks](#9-comparison-with-existing-benchmarks)
10. [10. Leaderboard](#10-leaderboard)
11. [11. Future Directions](#11-future-directions)
12. [References](#references)

---

## 1. Introduction and Motivation

**Purpose:** EpiBench-1.0 is the first publicly available benchmark specifically designed to evaluate AI **agents** — not just large language models (LLMs) — on real-world public health and epidemiology tasks. Unlike general-purpose benchmarks (MMLU, HumanEval, GSM8K), which test static knowledge or coding ability in isolation, EpiBench-1.0 requires candidates to interact with live data infrastructure, perform multi-step analytical workflows, and produce evidence-based outputs.

**Why a New Benchmark?**

The current landscape of AI evaluation in health is dominated by benchmarks that test either:
- **Medical knowledge recall** (MMLU-Medical, MedMCQA, USMLE)
- **Clinical reasoning on static cases** (PubMedQA, Med-PaLM)
- **Biomedical question answering** (BioASQ)

None of these benchmarks evaluate the ability to:
1. **Discover and retrieve** heterogeneous data from multiple public health systems
2. **Compute epidemiological metrics** from real administrative databases
3. **Integrate data** across sources (e.g., climate + disease, domestic + international)
4. **Produce professional reports** with verified scientific citations
5. **Operate across jurisdictions** — from Brazilian municipalities to global comparisons

**Key Differentiator:** EpiBench-1.0 requires AI agents to interact with live data infrastructure (DATASUS/PySUS, WHO GHO, ECDC, Mosqlimate, Malaria Atlas Project, Pathoplexus, Eurostat, World Bank), perform multi-step analytical workflows, and produce evidence-based reports with PubMed-verified citations — capabilities no general-purpose LLM possesses.

**Target Audience:** AI researchers, epidemiologists, public health professionals, and model developers who need to evaluate and compare AI systems on practical public health tasks.


## 2. Benchmark Design — Four-Dimensional Framework

EpiBench-1.0 evaluates AI agents along four orthogonal dimensions:

### Dimension A: Evaluation Domains (4 Domains)

| ID | Domain | Description |
|---|---|---|
| **D1** | Data Discovery & Literacy | Finding and understanding heterogeneous public health data sources |
| **D2** | Descriptive Epidemiology | Computing incidence, mortality, case-fatality rates, temporal/spatial patterns |
| **D3** | Advanced Analytics & Integration | Multi-source correlation, climate-disease modeling, international comparisons |
| **D4** | Full Workflow & Communication | End-to-end from question to professional report with verified citations |

### Dimension B: Difficulty Levels (4 Levels)

| Level | Label | Description | Tasks |
|---|---|---|---|
| 🥉 **Bronze** | Data Literacy | Single-step data discovery, catalog navigation | T01–T02 |
| 🥈 **Silver** | Single-Source Analysis | Descriptive epidemiology with one data source | T03–T06 |
| 🪙 **Gold** | Multi-Source Integration | 2+ sources, correlation, cross-border analysis | T07–T15 |
| 💎 **Platinum** | Full Workflow Reports | Complete analytical workflow with publication-quality outputs | T16–T21 |

### Dimension C: Competency Matrix (12 Competencies)

| Code | Competency | Description |
|---|---|---|
| **A** | Heterogeneous Data Discovery | Navigate DATASUS, WHO, ECDC, Mosqlimate, MAP, Pathoplexus, WB, Eurostat |
| **B** | Descriptive Epidemiology | Compute incidence, prevalence, mortality, case-fatality, age-standardized rates |
| **C** | Temporal Analysis | Trends, seasonality, Mann-Kendall tests, moving averages, epidemic curves |
| **D** | Spatial Analysis | Choropleth maps, hotspot identification, raster visualization, spatial statistics |
| **E** | Demographic Stratification | Age/sex disaggregation, equity analysis, vulnerability identification |
| **F** | Multi-Dimensional Integration | Linking climate, demographic, and epidemiological data across databases |
| **G** | Surveillance & Outbreak Detection | Alert systems, epidemic parameters, threshold monitoring |
| **H** | Data Quality Assessment | Completeness, consistency, duplication detection, bias identification |
| **I** | Visualization & Visual Communication | Appropriate chart selection, choropleths, time series, composition charts |
| **J** | Scientific Literature & Evidence | PubMed search, abstract verification, Vancouver citation formatting |
| **K** | Professional Reporting | Structured reports with TOC, branding, embedded visualizations, executive summaries |
| **L** | Genomic Epidemiology | Pathogen genomic surveillance, sequence availability, serotype/lineage tracking |

### Dimension D: Task Summary Table

| Task | Name | Level | Domain | Competencies | Max Points |
|---|---|---|---|---|---|
| T01 | Multi-Source Data Discovery | Bronze | D1 | A | 10 |
| T02 | Global Health Data Finder | Bronze | D1 | A | 10 |
| T03 | National Dengue Temporal Series | Silver | D2 | B, C, I | 20 |
| T04 | Mortality Spatial Analysis | Silver | D2 | B, D, I | 20 |
| T05 | Age-Sex Demographic Analysis | Silver | D2 | B, E, I | 20 |
| T06 | Data Quality Assessment | Silver | D2 | H | 20 |
| T07 | Multi-State Dengue Comparison | Gold | D3 | A, B, C, D, F, I | 30 |
| T08 | Climate-Disease Correlation | Gold | D3 | A, C, F, I | 30 |
| T09 | Infant Mortality Intl. Comparison | Gold | D3 | A, B, F | 30 |
| T10 | Epidemic Parameter Estimation | Gold | D3 | A, C, G | 30 |
| T11 | European Respiratory Surveillance | Gold | D3 | A, B, C, I | 30 |
| T12 | Malaria Prevalence Mapping | Gold | D3 | A, D, F | 30 |
| T13 | Genomic Surveillance Dashboard | Gold | D3 | A, D, L | 30 |
| T14 | Vaccination Coverage Analysis | Gold | D3 | A, B, E, F | 30 |
| T15 | Hospital Capacity Analysis | Gold | D3 | A, B, D, I | 30 |
| T16 | Full Epi Report — Dengue | Platinum | D4 | A–L (all) | 40 |
| T17 | Full Epi Report — Maternal Health | Platinum | D4 | A–L (all) | 40 |
| T18 | Cross-National Health Systems Report | Platinum | D4 | A–L (all) | 40 |
| T19 | Global Health Inequality Report | Platinum | D4 | A–L (all) | 40 |
| T20 | Multi-Source Outbreak Investigation | Platinum | D4 | A–L (all) | 40 |
| T21 | Predictive Model Evaluation Report | Platinum | D4 | A–L (all) | 40 |
| | | | **Total** | | **610** |


## 3. Task Specifications — Full Detail

### BRONZE TASKS (10 points each)

---

**Task T01 — Multi-Source Data Discovery**

- **Competencies:** A
- **Input:** "What epidemiological datasets are available for Brazil covering dengue, mortality, and live births?"
- **Expected Output:** List of available datasets with source names (SINAN, SIM, SINASC), data formats, available years, and row counts.
- **Evaluation Criteria:** Catalog scanning, correct database identification (at least 3 DATASUS databases), accurate metadata.
- **Max Score:** 10

---

**Task T02 — Global Health Data Finder**

- **Competencies:** A
- **Input:** "What health indicators are available from WHO, World Bank, and Eurostat for life expectancy and infant mortality?"
- **Expected Output:** Indicator codes, descriptions, available countries, time coverage, and data sources for each.
- **Evaluation Criteria:** Multi-source discovery, correct indicator identification, coverage information.
- **Max Score:** 10

---

### SILVER TASKS (20 points each)

---

**Task T03 — National Dengue Temporal Series**

- **Competencies:** B, C, I
- **Input:** "Analyze the monthly dengue notification trend in Brazil for the most recent available year."
- **Expected Output:** Monthly case counts with trend line, identification of peak month, seasonal pattern description.
- **Evaluation Criteria:** Correct data retrieval from SINAN, appropriate temporal aggregation, peak identification, seasonality description.
- **Max Score:** 20

---

**Task T04 — Mortality Spatial Analysis**

- **Competencies:** B, D, I
- **Input:** "Map the spatial distribution of mortality in [given state] for [given year], highlighting municipalities with highest rates."
- **Expected Output:** Choropleth map of municipalities, identification of top-10 high-mortality municipalities, rate computation.
- **Evaluation Criteria:** SIM data retrieval, correct rate computation, proper spatial visualization.
- **Max Score:** 20

---

**Task T05 — Age-Sex Demographic Analysis**

- **Competencies:** B, E, I
- **Input:** "Analyze the age and sex distribution of dengue cases in [given state] for [given year]."
- **Expected Output:** Age-group and sex-stratified case counts with appropriate visualizations (bar charts, proportions).
- **Evaluation Criteria:** Correct stratification, complete age groups, accurate proportions, appropriate visualizations.
- **Max Score:** 20

---

**Task T06 — Data Quality Assessment**

- **Competencies:** H
- **Input:** "Assess the data quality of the SINAN dengue dataset for [given state/year], identifying completeness, consistency, and potential biases."
- **Expected Output:** Quality report with missingness analysis, field-level completeness rates, consistency checks, bias discussion.
- **Evaluation Criteria:** Comprehensive quality assessment, correct methodology, actionable findings.
- **Max Score:** 20

---

### GOLD TASKS (30 points each)

---

**Task T07 — Multi-State Dengue Comparison**

- **Competencies:** A, B, C, D, F, I
- **Input:** "Compare dengue epidemiological profiles across 3 specified Brazilian states over a 3-year period."
- **Expected Output:** Comparative analysis with temporal trends, spatial distribution, incidence rates, risk stratification.
- **Evaluation Criteria:** Multi-state comparison, multi-year temporal analysis, incidence rate computation, clear comparison.
- **Max Score:** 30

---

**Task T08 — Climate-Disease Correlation**

- **Competencies:** A, C, F, I
- **Input:** "Analyze the correlation between climate variables (temperature, precipitation, humidity) and dengue incidence in [given municipality] over the past 3 years."
- **Expected Output:** Correlation analysis, scatter plots, time-lagged analysis, interpretation of climate drivers.
- **Evaluation Criteria:** Mosqlimate climate data retrieval, correct temporal alignment, statistical correlation, meaningful interpretation.
- **Max Score:** 30

---

**Task T09 — Infant Mortality International Comparison**

- **Competencies:** A, B, F
- **Input:** "Compare infant mortality rates between Brazil, Argentina, Colombia, and Mexico using WHO and World Bank data."
- **Expected Output:** Comparative table/graph with IMR values, trend analysis, ranking, contextual interpretation.
- **Evaluation Criteria:** Multi-country data from international sources, correct indicators, proper comparison.
- **Max Score:** 30

---

**Task T10 — Epidemic Parameter Estimation**

- **Competencies:** A, C, G
- **Input:** "Estimate the epidemic parameters (R0, peak timing, epidemic duration) for dengue in [given state] using EpiScanner data."
- **Expected Output:** Parameter estimates with confidence intervals, comparison across municipalities, epidemic curve overlay.
- **Evaluation Criteria:** EpiScanner data retrieval, correct parameter interpretation, spatial comparison.
- **Max Score:** 30

---

**Task T11 — European Respiratory Surveillance**

- **Competencies:** A, B, C, I
- **Input:** "Analyze the weekly influenza and SARS-CoV-2 co-circulation patterns in [given European country] for the current respiratory season."
- **Expected Output:** Multi-pathogen temporal analysis with sentinel testing data, variant information, activity levels.
- **Evaluation Criteria:** ECDC data retrieval, multi-pathogen analysis, temporal patterns, variant tracking.
- **Max Score:** 30

---

**Task T12 — Malaria Prevalence Mapping**

- **Competencies:** A, D, F
- **Input:** "Map malaria parasite rate surveys in [given African or Amazon country] and visualize prevalence patterns."
- **Expected Output:** Survey point map, prevalence ranges, species distribution (Pf/Pv), geographic gaps in data.
- **Evaluation Criteria:** Malaria Atlas Project data retrieval, correct parasite rate interpretation, appropriate spatial visualization.
- **Max Score:** 30

---

**Task T13 — Genomic Surveillance Dashboard**

- **Competencies:** A, D, L
- **Input:** "Analyze the availability and distribution of dengue genomic sequences in Brazil by serotype and state."
- **Expected Output:** Sequence count analysis by DENV-1/2/3/4, geographic distribution, temporal trends, data gaps.
- **Evaluation Criteria:** Pathoplexus data retrieval, serotype breakdown, geographic analysis, gap identification.
- **Max Score:** 30

---

**Task T14 — Vaccination Coverage Analysis**

- **Competencies:** A, B, E, F
- **Input:** "Analyze vaccination coverage for DTP3 and MCV1 across PAHO countries and identify disparities."
- **Expected Output:** Coverage table by country, trend analysis, identification of below-threshold countries, equity assessment.
- **Evaluation Criteria:** PAHO immunization data retrieval, correct vaccine codes, cross-country comparison, disparity identification.
- **Max Score:** 30

---

**Task T15 — Hospital Capacity Analysis**

- **Competencies:** A, B, D, I
- **Input:** "Analyze US hospital capacity utilization and COVID-19 burden across 5 specified states."
- **Expected Output:** Comparative analysis of bed occupancy, COVID-19 metrics, state-level differences, temporal trends.
- **Evaluation Criteria:** HealthData.gov retrieval, multi-state comparison, capacity metrics, temporal patterns.
- **Max Score:** 30


## 4. Task Specifications — Platinum Level

### PLATINUM TASKS (40 points each)

---

**Task T16 — Full Epidemiological Report: Dengue**

- **Competencies:** ALL (A through L)
- **Input:** "Produce a comprehensive epidemiological report on dengue in [given state] for [given year], including: temporal analysis, spatial distribution, demographic profile, data quality assessment, comparison with national average, and at least 3 PubMed-verified citations."
- **Expected Output:** Professional PDF report with table of contents, executive summary, 5+ sections, embedded visualizations (map, temporal chart, demographic chart, quality assessment), verified references, and structured findings.
- **Evaluation Criteria:** SINAN data retrieval, multi-dimensional analysis, professional formatting, citation verification, completeness of all required sections.
- **Max Score:** 40

---

**Task T17 — Full Epidemiological Report: Maternal Health**

- **Competencies:** ALL (A through L)
- **Input:** "Produce a comprehensive report on maternal health indicators in Brazil using SINASC (live births) and SIM (mortality) data, including: maternal mortality ratio trends, age distribution of mothers, birth outcomes, geographic disparities, and international comparison."
- **Expected Output:** Professional report integrating SINASC + SIM data, international comparison via WHO/WB, 4+ visualizations, verified citations.
- **Evaluation Criteria:** Multi-database integration (SINASC + SIM), correct maternal mortality ratio computation, international benchmarking, report quality.
- **Max Score:** 40

---

**Task T18 — Cross-National Health Systems Report**

- **Competencies:** ALL (A through L)
- **Input:** "Compare health system performance across 5 European countries using Eurostat data, including: healthcare expenditure, hospital beds, physician density, life expectancy, and self-perceived health status."
- **Expected Output:** Professional report with cross-national comparison, trend analysis, ranking tables, policy implications, verified citations.
- **Evaluation Criteria:** Eurostat multi-indicator retrieval, correct expenditure unit normalization, meaningful comparisons, report quality.
- **Max Score:** 40

---

**Task T19 — Global Health Inequality Report**

- **Competencies:** ALL (A through L)
- **Input:** "Produce a report comparing health indicators (life expectancy, infant mortality, healthcare expenditure) across WHO regions or PAHO subregions, analyzing inequalities and trends."
- **Expected Output:** Professional report with international comparisons from WHO/WB/Eurostat, trend analysis, inequality metrics, regional patterns, verified citations.
- **Evaluation Criteria:** Multi-source international data, multiple indicators, inequality quantification, regional analysis, report quality.
- **Max Score:** 40

---

**Task T20 — Multi-Source Outbreak Investigation**

- **Competencies:** ALL (A through L)
- **Input:** "Investigate a hypothetical or real disease outbreak using all available data sources: case notification data, genomic sequences, climate data, hospital capacity, and international surveillance reports. Produce a comprehensive investigation report."
- **Expected Output:** Full investigation integrating 5+ data sources, epidemiological curve, genomic context, environmental assessment, health system capacity assessment, international context, verified citations.
- **Evaluation Criteria:** 5+ data source integration, coherent narrative, proper investigation methodology, multi-jurisdictional awareness, publication quality.
- **Max Score:** 40

---

**Task T21 — Predictive Model Evaluation Report**

- **Competencies:** ALL (A through L)
- **Input:** "Evaluate available prediction models for [given disease] in Brazil from the Mosqlimate model registry. Compare model types, spatial/temporal resolution, and prediction records. Assess forecast accuracy where scores are available."
- **Expected Output:** Model comparison report with registry analysis, model type classification, resolution comparison, performance assessment, recommendations.
- **Evaluation Criteria:** Mosqlimate registry navigation, model metadata extraction, proper comparison methodology, actionable recommendations.
- **Max Score:** 40


## 5. Scoring Framework

### 5.1 Weighted Competency Scoring

The original framework treated all competencies equally, assigning uniform credit across data retrieval, computation, visualization, interpretation, and citation. In practice, competencies differ substantially in their impact on analytical validity. The principle of **"garbage in, garbage out"** means that data retrieval accuracy is foundational — errors propagating from incorrect data cannot be compensated by excellence in visualization or reporting.

EpiBench-1.0 adopts a **weighted scoring system** that reflects real-world epidemiological priorities:

| Competency Category | Weight | Rationale |
|---|---|---|
| **Data Retrieval & Quality** | **35%** | Foundational: correct source identification, accurate data extraction, and quality assessment are prerequisites for all downstream analysis. Errors here propagate irreversibly. |
| **Methodological Correctness** | **30%** | Core analytical integrity: appropriate use of epidemiological metrics, correct statistical methods, proper rate computation, and sound temporal/spatial analysis. |
| **Interpretation & Insights** | **20%** | Added analytical value: epidemiological soundness of conclusions, contextual interpretation, identification of patterns, and actionable insights beyond basic description. |
| **Visualization & Communication** | **10%** | Presentation quality: appropriate chart types, axis labels, color palettes, and professional formatting that accurately represents the underlying data. |
| **Citations & References** | **5%** | Scientific credibility: valid PubMed PMIDs, correct Vancouver formatting, abstract verification. Weighted lower because errors are detectable and correctable post-hoc. |

**Weighted Per-Task Score Formula:**

```
Score_task = Σ (category_score × category_weight) + penalty_adjustments
```

Where `category_score` ranges from 0 to 100% for each of the five categories above, and `penalty_adjustments` are applied as described in §5.2.

#### Mapping Competencies to Weight Categories

The 12 competencies (A–L) are mapped to the five weighted categories:

| Weight Category | Mapped Competencies |
|---|---|
| Data Retrieval & Quality (35%) | A (Data Discovery), H (Data Quality Assessment) |
| Methodological Correctness (30%) | B (Descriptive Epi), C (Temporal Analysis), D (Spatial Analysis), E (Demographics), F (Integration), G (Surveillance), L (Genomic Epi) |
| Interpretation & Insights (20%) | B (interpretive component), F (integrative insights), G (surveillance interpretation) |
| Visualization & Communication (10%) | I (Visualization), K (Professional Reporting) |
| Citations & References (5%) | J (Scientific Literature & Evidence) |

> **Note:** Some competencies (e.g., B, F, G) contribute to multiple categories. For scoring purposes, each competency's contributions are apportioned proportionally based on the task context.

---

### 5.2 Negative Scoring for Critical Errors

Not all errors are equal. While minor inaccuracies in formatting or visualization aesthetics may be tolerated, certain errors undermine the **scientific integrity** or **ethical compliance** of the output and warrant explicit deductions. EpiBench-1.0 introduces **negative scoring penalties** applied to the final task score:

| Critical Error Category | Penalty | Description | Examples |
|---|---|---|---|
| 🔴 **Fabricated Citations** | **−10 points** | Invented or hallucinated references that do not exist in PubMed or any bibliographic database. | Non-existent PMIDs, fabricated DOIs, hallucinated author names or journal titles. |
| 🟠 **Incorrect Data Source Attribution** | **−5 points** | Misidentifying the origin of data used in the analysis. | Claiming WHO data came from DATASUS; attributing SINAN notifications to SIVEP; mislabeling Mosqlimate data as official Ministry of Health data. |
| 🟠 **Misleading Visualizations** | **−5 points** | Charts or maps that distort the underlying data in ways that could lead to incorrect conclusions. | Truncated y-axis that exaggerates trends; inappropriate color scales (sequential for divergent data); inverted axes; cherry-picked time windows that misrepresent seasonality. |
| ⚫ **Privacy Violations** | **−20 points or Automatic Failure** | Exposure of individual-level data, potential re-identification, or disclosure of personally identifiable information (PII). | Displaying patient names, CPF numbers, individual geocoordinates; publishing case-level data without aggregation; enabling re-identification through cross-referencing. |
| 🟡 **Unit/Scale Errors** | **−3 points** | Incorrect units, wrong denominators, or scale mismatches. | Reporting mortality per 1,000 instead of per 100,000; using population from a different year; confusing incidence with prevalence. |

**Penalty Rules:**

1. **Penalties stack:** Multiple critical errors incur cumulative deductions (e.g., a fabricated citation + misleading visualization = −15 points).
2. **Floor at zero:** No task score can fall below 0 points, regardless of penalty accumulation.
3. **Privacy violation override:** Regardless of positive scoring, any confirmed privacy violation results in **automatic task failure** (score = 0) and a flag for the entire benchmark evaluation.
4. **Penalty cap per task:** Total negative deductions are capped at the task's maximum score to prevent scenarios where penalties exceed possible positive contributions.

**Impact Example (Gold Task, max 30 points):**

| Scenario | Positive Score | Penalties | Final Score |
|---|---|---|---|
| Strong analysis, no errors | 26/30 | 0 | **26** |
| Good analysis + 1 fabricated citation | 26/30 | −10 | **16** |
| Good analysis + misleading visualization | 26/30 | −5 | **21** |
| Good analysis + fabricated citation + wrong source | 26/30 | −15 | **11** |
| Good analysis + privacy violation | 26/30 | −20 → **automatic failure** | **0** |

---

### 5.3 Partial Credit Granularity

The original ±5% binary tolerance for numerical results was too coarse, failing to distinguish between a nearly perfect computation and a barely acceptable one. EpiBench-1.0 introduces a **five-tier partial credit scale** for numerical accuracy, plus separate recognition for methodological correctness independent of the final result:

#### Numerical Accuracy Tiers

| Tier | Deviation from Reference | Credit Awarded | Interpretation |
|---|---|---|---|
| 🏆 **Exact Match** | 0% | **100%** | Numerically identical to the reference answer. |
| 🥇 **Within 1%** | ≤ 1.0% | **95%** | Rounding or minor precision difference; analytically equivalent. |
| 🥈 **Within 5%** | ≤ 5.0% | **80%** | Acceptable tolerance for epidemiological metrics. May reflect different denominator choices or minor data version differences. |
| 🥉 **Within 10%** | ≤ 10.0% | **60%** | Below ideal but within a reasonable range; likely reflects a methodological discrepancy or data filtering difference worth investigating. |
| ⚠️ **Beyond 10%** | > 10.0% | **0%** | Result is not considered valid; full credit is lost for this metric. |

#### Methodological Credit (Independent of Numerical Accuracy)

Recognizing that correct methodology is valuable even when the final result diverges (due to data versioning, source differences, or computational edge cases), a separate **methodological credit** is awarded:

| Scenario | Methodological Credit | Rationale |
|---|---|---|
| **Correct method, correct result** | 100% | Ideal: method and result both validated. |
| **Correct method, wrong result** | **40%** | The analytical approach was sound but something went wrong in execution (data issue, rounding error, edge case). This partial credit incentivizes methodological rigor even when outcomes diverge. |
| **Wrong method, right result** | **20%** | The correct answer was obtained by coincidence (e.g., using the wrong denominator that happens to produce a similar number). Minimal credit because the approach is not reproducible or generalizable. |
| **Wrong method, wrong result** | 0% | No credit; both approach and outcome are invalid. |

#### Combined Scoring Example

For a Gold task metric worth 10 points in the "Methodological Correctness" category:

| Scenario | Numerical Credit | Methodological Credit | Combined (10 pt) |
|---|---|---|---|
| Exact match, correct method | 100% × 95%* | 100% | **10.0** |
| Within 5%, correct method | 80% | 100% | **8.0** |
| Beyond 10%, correct method | 0% | 40% | **4.0** |
| Exact match, wrong method | 100% × 95%* | 20% | **1.9** |
| Beyond 10%, wrong method | 0% | 0% | **0.0** |

*\*Exact match receives the 100% numerical tier, multiplied by the methodological credit.*

#### Applicability by Task Level

| Task Level | Granular Scoring | Notes |
|---|---|---|
| **Bronze** | ✓ Numerical tiers only | No complex methods to evaluate; focus on data retrieval accuracy. |
| **Silver** | ✓ Numerical tiers + Methodological credit | Single-source analysis allows clear method-vs-result disambiguation. |
| **Gold** | ✓ Full granular scoring | Multi-step workflows warrant both numerical and methodological evaluation. |
| **Platinum** | ✓ Full granular scoring + Weighted categories + Penalties | Complete reports evaluated holistically across all scoring dimensions. |

---

### Per-Task Scoring Rubric (Revised)

| Score | Percentage | Description |
|---|---|---|
| **10/10** | 100% | Fully correct, comprehensive, all required elements present, professional quality, no penalties |
| **7–9/10** | 70–90% | Mostly correct with minor gaps or inaccuracies, no critical errors |
| **4–6/10** | 40–60% | Partially correct, significant gaps or methodological issues |
| **1–3/10** | 10–30% | Minimal correct elements, major failures in data or analysis |
| **0/10** | 0% | No correct elements, complete failure, or privacy violation |

*Note: Platinum tasks use a 0–40 scale (4× multiplier). Gold tasks use 0–30 (3×). Silver tasks use 0–20 (2×). Bronze tasks use 0–10 (1×). All scales are subject to negative penalties as defined in §5.2.*

### Total Score Computation

| Task Level | Tasks | Points Per Task | Subtotal |
|---|---|---|---|
| Bronze (T01–T02) | 2 | 10 | 20 |
| Silver (T03–T06) | 4 | 20 | 80 |
| Gold (T07–T15) | 9 | 30 | 270 |
| Platinum (T16–T21) | 6 | 40 | 240 |
| | **21 total** | | **610 max** |
| | | **Penalty reserve** | **−610 max** |
| | | **Effective range** | **0 to 610** |

### Overall Grading Scale (Revised)

The grading scale now accounts for the fact that penalties can reduce scores below what would be expected from positive scoring alone:

| Tier | Score Range | Classification |
|---|---|---|
| 🏆 **S-Tier** | 90%+ (549–610) | Production-ready AI epidemiologist |
| 🥇 **A-Tier** | 75–89% (458–548) | Advanced analytical assistant |
| 🥈 **B-Tier** | 60–74% (366–457) | Competent with supervision needed |
| 🥉 **C-Tier** | 40–59% (244–365) | Basic capability, significant gaps |
| ❌ **D-Tier** | 20–39% (122–243) | Below minimum viable capability |
| ❌ **F-Tier** | 0–19% (0–121) | Non-functional for epidemiological tasks |
| 🚫 **Disqualified** | Any privacy violation | Automatic benchmark failure regardless of positive score |

### Scoring Summary Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    EpiBench-1.0 Scoring Pipeline                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌────────────────────┐    ┌─────────────┐ │
│  │ Agent Output  │───▶│ Category Evaluation │───▶│ Weighted    │ │
│  │ (per task)    │    │ (5 categories)      │    │ Sum         │ │
│  └──────────────┘    └────────────────────┘    └──────┬──────┘ │
│                                                       │          │
│  ┌──────────────┐    ┌────────────────────┐    ┌──────▼──────┐ │
│  │ Error         │───▶│ Penalty Assessment │───▶│ Penalty     │ │
│  │ Detection     │    │ (§5.2 rules)       │    │ Deduction   │ │
│  └──────────────┘    └────────────────────┘    └──────┬──────┘ │
│                                                       │          │
│  ┌──────────────┐    ┌────────────────────┐    ┌──────▼──────┐ │
│  │ Numerical     │───▶│ Partial Credit     │───▶│ Granularity │ │
│  │ Comparison    │    │ Tiers (§5.3)       │    │ Adjustment  │ │
│  └──────────────┘    └────────────────────┘    └──────┬──────┘ │
│                                                       │          │
│                                               ┌──────▼──────┐ │
│                                               │ Final Score │ │
│                                               │ → Tier      │ │
│                                               └─────────────┘ │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```


## 6. Evaluation Protocol

### Automated Components (gradable by script)

- **Data retrieval accuracy:** Correct database/source identified (evaluated under Data Retrieval & Quality, 35%)
- **Metric computation:** Numerical results scored via partial credit tiers (§5.3)
- **Visualization generation:** Correct chart type, axis labels present (evaluated under Visualization & Communication, 10%)
- **Citation verification:** Valid PMIDs, correct formatting (evaluated under Citations & References, 5%)
- **Critical error detection:** Automated checks for fabricated PMIDs, privacy leaks, source mismatches (§5.2)

### Human-Expert Components (require reviewer)

- **Interpretation quality:** Epidemiological soundness of conclusions (evaluated under Interpretation & Insights, 20%)
- **Methodological rigor:** Appropriate statistical methods (evaluated under Methodological Correctness, 30%)
- **Report structure and clarity:** Professional formatting standards
- **Insight novelty:** Beyond basic description, adds analytical value
- **Misleading visualization assessment:** Human judgment for chart integrity (§5.2)

### Time Limits

| Task Level | Time Per Task | Total Time |
|---|---|---|
| Bronze | 5 minutes | 10 minutes |
| Silver | 15 minutes | 60 minutes |
| Gold | 30 minutes | 4.5 hours |
| Platinum | 60 minutes | 6 hours |
| | | **~8 hours total** |

### Partial Credit Rules (Revised — Aligned with §5.1 Weights)

| Category | Weight | Evaluation Focus |
|---|---|---|
| **Data Retrieval & Quality** | 35% | Correct source identified, data downloaded, quality assessed |
| **Methodological Correctness** | 30% | Metrics computed correctly, appropriate statistical methods, proper denominators |
| **Interpretation & Insights** | 20% | Meaningful epidemiological conclusions drawn, contextual awareness |
| **Visualization & Communication** | 10% | Appropriate charts generated, clear axis labels, professional presentation |
| **Citations & References** | 5% | Valid PubMed citations, verified abstracts, correct formatting |


## 7. Reference Answers and Automated Grading

Reference answers for all 21 tasks are maintained in a separate repository (to be published). For each task, the reference answer includes:

- **Exact data source and query** used
- **Expected numerical results** with granular tolerance tiers (§5.3)
- **Required visualization types** and minimum content requirements
- **Citation requirements** (PubMed PMIDs and verification status)
- **Structural requirements** for report-type tasks
- **Methodological specification** for method-vs-result disambiguation

### Automated Grading Pipeline (Revised)

```
Input Task → Execute Agent → Collect Output → Parse Results
                                                   ↓
                                          ┌─────────────────────┐
                                          │ Compare vs. Reference │
                                          └──────────┬──────────┘
                                                     ↓
                                          ┌─────────────────────┐
                                          │ 5-Category Scoring   │
                                          │ (§5.1 Weights)       │
                                          └──────────┬──────────┘
                                                     ↓
                                          ┌─────────────────────┐
                                          │ Numerical Tiers      │
                                          │ (§5.3 Granularity)   │
                                          └──────────┬──────────┘
                                                     ↓
                                          ┌─────────────────────┐
                                          │ Penalty Check        │
                                          │ (§5.2 Deductions)    │
                                          └──────────┬──────────┘
                                                     ↓
                                     Score = Σ (cat_score × w) − penalties
                                                     ↓
                                         Assign Tier Classification
```

### Validation Methodology

Reference answers are validated by:
1. Expert epidemiologist review
2. Cross-validation with published surveillance reports
3. Automated consistency checks against official data
4. Community review (planned open-source repository)
5. **Methodological specification** — each reference answer now includes an explicit methodological description so that correct-method/wrong-result scenarios can be properly scored (§5.3)


## 8. Required Data Sources and Infrastructure

The benchmark requires access to the following data infrastructure:

### Brazilian Data Systems (DATASUS via PySUS)

| System | Acronym | Data Type |
|---|---|---|
| Disease Notification | SINAN | Case-level disease reports |
| Mortality | SIM | Death certificates (DO)
| Live Births | SINASC | Birth certificates (DN)
| Hospital Admissions | SIH-SUS | AIH records |
| Outpatient Procedures | SIA-SUS | BPA/PA records |
| Immunization | PNI | Vaccine coverage |
| Health Establishments | CNES | Facility registry |
| Hospital Production | CIHA | Production data |

### International Data Sources

| Source | System | Data Type |
|---|---|---|
| WHO | Global Health Observatory (GHO) | Health indicators, 1000+ indicators |
| WHO | Disease Outbreak News (DON) | Real-time outbreak reports |
| ECDC | ERVISS / GitHub | European respiratory surveillance |
| Mosqlimate | Infodengue, Climate, EpiScanner, Contaovos | Brazilian epi-climate data |
| Malaria Atlas Project (MAP) | PR surveys, vectors, rasters | Global malaria data |
| Pathoplexus | Genomic sequences | Viral pathogen genomics |
| World Bank | Open Data API | Economic & health indicators |
| Eurostat | Health indicators | European health statistics |
| PAHO/WHO | WUENIC, epidemiological data | Americas immunization & disease |
| HealthData.gov | HHS Protect | US hospital capacity & COVID |

### Required Agent Capabilities

To attempt EpiBench-1.0, an AI agent must possess:

1. **Tool-use capability:** Ability to call APIs and database interfaces
2. **Code execution:** Python/DuckDB for data processing and statistical analysis
3. **Data cataloging:** Ability to scan and index parquet files and metadata
4. **Geospatial operations:** Choropleth mapping, raster visualization
5. **Report generation:** Structured markdown/HTML/PDF output
6. **Literature search:** PubMed API integration with abstract verification
7. **Privacy awareness:** Ability to aggregate data appropriately and avoid individual-level exposure


## 9. Comparison with Existing Benchmarks

| Benchmark | Domain | Data Interaction | Multi-Step Workflow | Visualization | Citations | Epidemiology |
|---|---|---|---|---|---|---|
| **MMLU-ProfMedical** | Medical knowledge | ❌ Static | ❌ | ❌ | ❌ | ❌ |
| **MedMCQA** | Medical MCQ | ❌ Static | ❌ | ❌ | ❌ | ❌ |
| **USMLE Step 1-3** | Clinical reasoning | ❌ Static | ❌ | ❌ | ❌ | ❌ |
| **PubMedQA** | Literature comprehension | ❌ Static | ❌ | ❌ | ❌ | ❌ |
| **BioASQ** | Biomedical QA | ❌ Static | ❌ | ❌ | ❌ | ❌ |
| **Med-PaLM Evaluation** | Clinical dialogue | ❌ Static | ❌ | ❌ | ❌ | ❌ |
| **EpiBench-1.0** | Public Health / Epi | ✅ Live APIs | ✅ 5–20 steps | ✅ Required | ✅ Verified | ✅ Core |

**EpiBench-1.0 uniquely requires:**
- Real-time interaction with 10+ public health data systems
- Multi-step analytical workflows spanning hours
- Generation of publication-quality visualizations
- PubMed-verified scientific citations
- Cross-jurisdictional data integration (local to global)
- **Weighted scoring with critical error penalties** (§5.1, §5.2)
- **Granular partial credit for methodological rigor** (§5.3)


## 10. Leaderboard

Results from local `epibench` runs (`epibench compare`) and the published EpidBot self-assessment.

### Local runs

| Rank | Model | Score | Max | % | Tier | Run ID |
|---|---|---:|---:|---:|---:|---:|
| 1 | anthropic:claude-sonnet-4-5 | 290.68 | 590 | 49.27 | C | 20260620T174858 |
| 2 | dummy:demo | 223.33 | 610 | 36.61 | D | 20260620T104639 |
| 3 | dummy:demo | 182.23 | 610 | 29.87 | D | 20260620T173049 |
| 4 | openai:gpt-4o | 125.13 | 270 | 46.34 | D | 20260620T174237 |
| 5 | openai:gpt-4o | 70.18 | 240 | 29.24 | F | 20260620T174346 |
| 6 | openai:gpt-4o | 46.75 | 80 | 58.43 | F | 20260620T174157 |

> **Note:** The *Max* column reflects the point total of the task subset that was run (610 = full benchmark). Several entries are partial runs. The complete local leaderboard is written to `results/leaderboard.csv` after each run.

### EpidBot self-assessment

| Version | Score | Max | % | Tier | Source |
|---|---:|---:|---:|---:|---|
| v3 — post tool-upgrade | 418 | 550 | 76.0 | A | [Zenodo DOI:10.5281/zenodo.20709172](https://doi.org/10.5281/zenodo.20709172) |
| Earlier version | 340 | 550 | 61.8 | B | Zenodo |

> **Note:** The Zenodo assessment uses a 550-point version of EpiBench-1.0; the current repository release scores out of **610** points.

## 11. Future Directions

### EpiBench-2.0 (Planned)

- **Causal inference tasks:** Directed acyclic graph (DAG) construction, counterfactual analysis
- **Outbreak simulation:** Response modeling, intervention scenario analysis
- **Real-time alert evaluation:** Automated detection of emerging threats

### EpiBench-3.0 (Planned)

- **Multi-country outbreak investigation:** Cross-border surveillance integration
- **Predictive model training:** End-to-end model development and evaluation
- **Natural language report writing:** Full scientific manuscript generation

### Community Contributions

- **Task proposals:** New epidemiological scenarios and domains
- **Reference answer validation:** Expert review of gold-standard answers
- **Additional data sources:** Integration of new national and international systems
- **Multi-language support:** Task specifications in Portuguese, Spanish, French

### Open Science Commitment

EpiBench-1.0 is designed as an open benchmark:
- **Task specifications:** Publicly available for any AI system
- **Scoring rubrics:** Transparent and reproducible (weighted categories, penalties, partial credit tiers)
- **Reference answers:** To be published in open repository
- **Community review:** Pull requests and discussions welcome


## References

1. Singhal K, Azizi S, Tu T, et al. Large language models encode clinical knowledge. *Nature*. 2023;620(7973):172-180. doi:10.1038/s41586-023-06191-x

2. Pal R, Khatri A, Sorensen T, et al. Towards generalist biomedical AI. *NEJM AI*. 2024;1(4):AIoa2300118. doi:10.1056/AIoa2300118

3. Galadima II, Mbacham WF, Clarkson C, et al. Artificial intelligence and malaria — a scoping review of current approaches and future prospects. *Malar J*. 2024;23(1):105. doi:10.1186/s12936-024-04817-0

4. Abdalla SM, Camargos MCS, da Silva FL, et al. Análise da completitude das variáveis epidemiológicas do Sistema de Informação sobre Mortalidade em idosos no Brasil. *Cad Saúde Pública*. 2023;39(3):e00237222. doi:10.1590/0102-311X037222

5. Puri A, Cozzi L, Ellis J, et al. Expert-level detection of pathologies from unannotated chest X-ray images via self-supervised learning. *Nat Biotechnol*. 2024;42:1356-1365. doi:10.1038/s41587-023-02037-4

---