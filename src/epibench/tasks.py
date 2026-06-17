"""EpiBench-1.0 benchmark task specifications.

Encodes all 21 tasks from the EpiBench README (sections 3 and 4) as structured
data, plus the four-dimensional framework (domains, levels, competencies) from
section 2.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import ClassVar


class Level(StrEnum):
    BRONZE = "Bronze"
    SILVER = "Silver"
    GOLD = "Gold"
    PLATINUM = "Platinum"


class Domain(StrEnum):
    D1 = "D1"  # Data Discovery & Literacy
    D2 = "D2"  # Descriptive Epidemiology
    D3 = "D3"  # Advanced Analytics & Integration
    D4 = "D4"  # Full Workflow & Communication


class Competency(StrEnum):
    A = "A"  # Heterogeneous Data Discovery
    B = "B"  # Descriptive Epidemiology
    C = "C"  # Temporal Analysis
    D = "D"  # Spatial Analysis
    E = "E"  # Demographic Stratification
    F = "F"  # Multi-Dimensional Integration
    G = "G"  # Surveillance & Outbreak Detection
    H = "H"  # Data Quality Assessment
    I = "I"  # noqa: E741 (spec competency code)  # Visualization & Visual Communication
    J = "J"  # Scientific Literature & Evidence
    K = "K"  # Professional Reporting
    L = "L"  # Genomic Epidemiology


# Section 5.1 — weighted competency categories.
CATEGORY_WEIGHTS: dict[str, float] = {
    "data_retrieval": 0.35,
    "methodology": 0.30,
    "interpretation": 0.20,
    "visualization": 0.10,
    "citations": 0.05,
}

# Section 5.1 — which competencies feed which weight category.
COMPETENCY_TO_CATEGORY: dict[Competency, list[str]] = {
    Competency.A: ["data_retrieval"],
    Competency.H: ["data_retrieval"],
    Competency.B: ["methodology", "interpretation"],
    Competency.C: ["methodology"],
    Competency.D: ["methodology"],
    Competency.E: ["methodology"],
    Competency.F: ["methodology", "interpretation"],
    Competency.G: ["methodology", "interpretation"],
    Competency.L: ["methodology"],
    Competency.I: ["visualization"],
    Competency.K: ["visualization"],
    Competency.J: ["citations"],
}

# Section 6 — wall-clock time budget per task level (seconds).
LEVEL_TIME_BUDGETS: dict[Level, int] = {
    Level.BRONZE: 5 * 60,
    Level.SILVER: 15 * 60,
    Level.GOLD: 30 * 60,
    Level.PLATINUM: 60 * 60,
}

# Points per level, from the README task table.
LEVEL_MAX_POINTS: dict[Level, int] = {
    Level.BRONZE: 10,
    Level.SILVER: 20,
    Level.GOLD: 30,
    Level.PLATINUM: 40,
}

# Total benchmark points: 2x10 (Bronze) + 4x20 (Silver) + 9x30 (Gold) + 6x40
# (Platinum) = 610. The overall tier classification is percentage-based.
TOTAL_MAX_POINTS: int = 610


@dataclass(frozen=True)
class Task:
    id: str
    name: str
    level: Level
    domain: Domain
    competencies: tuple[Competency, ...]
    prompt: str
    expected_output: str
    evaluation_criteria: str
    max_points: int = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "max_points", LEVEL_MAX_POINTS[self.level])

    @property
    def time_budget_seconds(self) -> int:
        return LEVEL_TIME_BUDGETS[self.level]

    @property
    def weight_categories(self) -> set[str]:
        """Weighted categories this task touches, derived from its competencies."""
        cats: set[str] = set()
        for comp in self.competencies:
            cats.update(COMPETENCY_TO_CATEGORY.get(comp, ()))
        return cats


_TASKS: list[Task] = [
    Task(
        id="T01",
        name="Multi-Source Data Discovery",
        level=Level.BRONZE,
        domain=Domain.D1,
        competencies=(Competency.A,),
        prompt=(
            "What epidemiological datasets are available for Brazil covering dengue, "
            "mortality, and live births?"
        ),
        expected_output=(
            "List of available datasets with source names (SINAN, SIM, SINASC), data "
            "formats, available years, and row counts."
        ),
        evaluation_criteria=(
            "Catalog scanning, correct database identification (at least 3 DATASUS "
            "databases), accurate metadata."
        ),
    ),
    Task(
        id="T02",
        name="Global Health Data Finder",
        level=Level.BRONZE,
        domain=Domain.D1,
        competencies=(Competency.A,),
        prompt=(
            "What health indicators are available from WHO, World Bank, and Eurostat "
            "for life expectancy and infant mortality?"
        ),
        expected_output=(
            "Indicator codes, descriptions, available countries, time coverage, and "
            "data sources for each."
        ),
        evaluation_criteria=(
            "Multi-source discovery, correct indicator identification, coverage information."
        ),
    ),
    Task(
        id="T03",
        name="National Dengue Temporal Series",
        level=Level.SILVER,
        domain=Domain.D2,
        competencies=(Competency.B, Competency.C, Competency.I),
        prompt=(
            "Analyze the monthly dengue notification trend in Brazil for the most "
            "recent available year."
        ),
        expected_output=(
            "Monthly case counts with trend line, identification of peak month, "
            "seasonal pattern description."
        ),
        evaluation_criteria=(
            "Correct data retrieval from SINAN, appropriate temporal aggregation, "
            "peak identification, seasonality description."
        ),
    ),
    Task(
        id="T04",
        name="Mortality Spatial Analysis",
        level=Level.SILVER,
        domain=Domain.D2,
        competencies=(Competency.B, Competency.D, Competency.I),
        prompt=(
            "Map the spatial distribution of mortality in a given Brazilian state for "
            "a given year, highlighting municipalities with highest rates."
        ),
        expected_output=(
            "Choropleth map of municipalities, identification of top-10 high-mortality "
            "municipalities, rate computation."
        ),
        evaluation_criteria=(
            "SIM data retrieval, correct rate computation, proper spatial visualization."
        ),
    ),
    Task(
        id="T05",
        name="Age-Sex Demographic Analysis",
        level=Level.SILVER,
        domain=Domain.D2,
        competencies=(Competency.B, Competency.E, Competency.I),
        prompt=(
            "Analyze the age and sex distribution of dengue cases in a given Brazilian "
            "state for a given year."
        ),
        expected_output=(
            "Age-group and sex-stratified case counts with appropriate visualizations "
            "(bar charts, proportions)."
        ),
        evaluation_criteria=(
            "Correct stratification, complete age groups, accurate proportions, "
            "appropriate visualizations."
        ),
    ),
    Task(
        id="T06",
        name="Data Quality Assessment",
        level=Level.SILVER,
        domain=Domain.D2,
        competencies=(Competency.H,),
        prompt=(
            "Assess the data quality of the SINAN dengue dataset for a given state and "
            "year, identifying completeness, consistency, and potential biases."
        ),
        expected_output=(
            "Quality report with missingness analysis, field-level completeness rates, "
            "consistency checks, bias discussion."
        ),
        evaluation_criteria=(
            "Comprehensive quality assessment, correct methodology, actionable findings."
        ),
    ),
    Task(
        id="T07",
        name="Multi-State Dengue Comparison",
        level=Level.GOLD,
        domain=Domain.D3,
        competencies=(
            Competency.A, Competency.B, Competency.C,
            Competency.D, Competency.F, Competency.I,
        ),
        prompt=(
            "Compare dengue epidemiological profiles across 3 specified Brazilian states "
            "over a 3-year period."
        ),
        expected_output=(
            "Comparative analysis with temporal trends, spatial distribution, incidence "
            "rates, risk stratification."
        ),
        evaluation_criteria=(
            "Multi-state comparison, multi-year temporal analysis, incidence rate "
            "computation, clear comparison."
        ),
    ),
    Task(
        id="T08",
        name="Climate-Disease Correlation",
        level=Level.GOLD,
        domain=Domain.D3,
        competencies=(Competency.A, Competency.C, Competency.F, Competency.I),
        prompt=(
            "Analyze the correlation between climate variables (temperature, "
            "precipitation, humidity) and dengue incidence in a given municipality over "
            "the past 3 years."
        ),
        expected_output=(
            "Correlation analysis, scatter plots, time-lagged analysis, interpretation "
            "of climate drivers."
        ),
        evaluation_criteria=(
            "Mosqlimate climate data retrieval, correct temporal alignment, statistical "
            "correlation, meaningful interpretation."
        ),
    ),
    Task(
        id="T09",
        name="Infant Mortality International Comparison",
        level=Level.GOLD,
        domain=Domain.D3,
        competencies=(Competency.A, Competency.B, Competency.F),
        prompt=(
            "Compare infant mortality rates between Brazil, Argentina, Colombia, and "
            "Mexico using WHO and World Bank data."
        ),
        expected_output=(
            "Comparative table/graph with IMR values, trend analysis, ranking, "
            "contextual interpretation."
        ),
        evaluation_criteria=(
            "Multi-country data from international sources, correct indicators, proper "
            "comparison."
        ),
    ),
    Task(
        id="T10",
        name="Epidemic Parameter Estimation",
        level=Level.GOLD,
        domain=Domain.D3,
        competencies=(Competency.A, Competency.C, Competency.G),
        prompt=(
            "Estimate the epidemic parameters (R0, peak timing, epidemic duration) for "
            "dengue in a given state using EpiScanner data."
        ),
        expected_output=(
            "Parameter estimates with confidence intervals, comparison across "
            "municipalities, epidemic curve overlay."
        ),
        evaluation_criteria=(
            "EpiScanner data retrieval, correct parameter interpretation, spatial comparison."
        ),
    ),
    Task(
        id="T11",
        name="European Respiratory Surveillance",
        level=Level.GOLD,
        domain=Domain.D3,
        competencies=(Competency.A, Competency.B, Competency.C, Competency.I),
        prompt=(
            "Analyze the weekly influenza and SARS-CoV-2 co-circulation patterns in a "
            "given European country for the current respiratory season."
        ),
        expected_output=(
            "Multi-pathogen temporal analysis with sentinel testing data, variant "
            "information, activity levels."
        ),
        evaluation_criteria=(
            "ECDC data retrieval, multi-pathogen analysis, temporal patterns, variant tracking."
        ),
    ),
    Task(
        id="T12",
        name="Malaria Prevalence Mapping",
        level=Level.GOLD,
        domain=Domain.D3,
        competencies=(Competency.A, Competency.D, Competency.F),
        prompt=(
            "Map malaria parasite rate surveys in a given African or Amazon country and "
            "visualize prevalence patterns."
        ),
        expected_output=(
            "Survey point map, prevalence ranges, species distribution (Pf/Pv), "
            "geographic gaps in data."
        ),
        evaluation_criteria=(
            "Malaria Atlas Project data retrieval, correct parasite rate interpretation, "
            "appropriate spatial visualization."
        ),
    ),
    Task(
        id="T13",
        name="Genomic Surveillance Dashboard",
        level=Level.GOLD,
        domain=Domain.D3,
        competencies=(Competency.A, Competency.D, Competency.L),
        prompt=(
            "Analyze the availability and distribution of dengue genomic sequences in "
            "Brazil by serotype and state."
        ),
        expected_output=(
            "Sequence count analysis by DENV-1/2/3/4, geographic distribution, temporal "
            "trends, data gaps."
        ),
        evaluation_criteria=(
            "Pathoplexus data retrieval, serotype breakdown, geographic analysis, gap "
            "identification."
        ),
    ),
    Task(
        id="T14",
        name="Vaccination Coverage Analysis",
        level=Level.GOLD,
        domain=Domain.D3,
        competencies=(Competency.A, Competency.B, Competency.E, Competency.F),
        prompt=(
            "Analyze vaccination coverage for DTP3 and MCV1 across PAHO countries and "
            "identify disparities."
        ),
        expected_output=(
            "Coverage table by country, trend analysis, identification of below-threshold "
            "countries, equity assessment."
        ),
        evaluation_criteria=(
            "PAHO immunization data retrieval, correct vaccine codes, cross-country "
            "comparison, disparity identification."
        ),
    ),
    Task(
        id="T15",
        name="Hospital Capacity Analysis",
        level=Level.GOLD,
        domain=Domain.D3,
        competencies=(Competency.A, Competency.B, Competency.D, Competency.I),
        prompt=(
            "Analyze US hospital capacity utilization and COVID-19 burden across 5 "
            "specified states."
        ),
        expected_output=(
            "Comparative analysis of bed occupancy, COVID-19 metrics, state-level "
            "differences, temporal trends."
        ),
        evaluation_criteria=(
            "HealthData.gov retrieval, multi-state comparison, capacity metrics, temporal "
            "patterns."
        ),
    ),
    Task(
        id="T16",
        name="Full Epidemiological Report: Dengue",
        level=Level.PLATINUM,
        domain=Domain.D4,
        competencies=tuple(Competency),  # All A–L
        prompt=(
            "Produce a comprehensive epidemiological report on dengue in a given Brazilian "
            "state for a given year, including: temporal analysis, spatial distribution, "
            "demographic profile, data quality assessment, comparison with national average, "
            "and at least 3 PubMed-verified citations."
        ),
        expected_output=(
            "Professional PDF report with table of contents, executive summary, 5+ sections, "
            "embedded visualizations (map, temporal chart, demographic chart, quality "
            "assessment), verified references, and structured findings."
        ),
        evaluation_criteria=(
            "SINAN data retrieval, multi-dimensional analysis, professional formatting, "
            "citation verification, completeness of all required sections."
        ),
    ),
    Task(
        id="T17",
        name="Full Epidemiological Report: Maternal Health",
        level=Level.PLATINUM,
        domain=Domain.D4,
        competencies=tuple(Competency),
        prompt=(
            "Produce a comprehensive report on maternal health indicators in Brazil using "
            "SINASC (live births) and SIM (mortality) data, including: maternal mortality "
            "ratio trends, age distribution of mothers, birth outcomes, geographic "
            "disparities, and international comparison."
        ),
        expected_output=(
            "Professional report integrating SINASC + SIM data, international comparison "
            "via WHO/WB, 4+ visualizations, verified citations."
        ),
        evaluation_criteria=(
            "Multi-database integration (SINASC + SIM), correct maternal mortality ratio "
            "computation, international benchmarking, report quality."
        ),
    ),
    Task(
        id="T18",
        name="Cross-National Health Systems Report",
        level=Level.PLATINUM,
        domain=Domain.D4,
        competencies=tuple(Competency),
        prompt=(
            "Compare health system performance across 5 European countries using Eurostat "
            "data, including: healthcare expenditure, hospital beds, physician density, life "
            "expectancy, and self-perceived health status."
        ),
        expected_output=(
            "Professional report with cross-national comparison, trend analysis, ranking "
            "tables, policy implications, verified citations."
        ),
        evaluation_criteria=(
            "Eurostat multi-indicator retrieval, correct expenditure unit normalization, "
            "meaningful comparisons, report quality."
        ),
    ),
    Task(
        id="T19",
        name="Global Health Inequality Report",
        level=Level.PLATINUM,
        domain=Domain.D4,
        competencies=tuple(Competency),
        prompt=(
            "Produce a report comparing health indicators (life expectancy, infant "
            "mortality, healthcare expenditure) across WHO regions or PAHO subregions, "
            "analyzing inequalities and trends."
        ),
        expected_output=(
            "Professional report with international comparisons from WHO/WB/Eurostat, "
            "trend analysis, inequality metrics, regional patterns, verified citations."
        ),
        evaluation_criteria=(
            "Multi-source international data, multiple indicators, inequality "
            "quantification, regional analysis, report quality."
        ),
    ),
    Task(
        id="T20",
        name="Multi-Source Outbreak Investigation",
        level=Level.PLATINUM,
        domain=Domain.D4,
        competencies=tuple(Competency),
        prompt=(
            "Investigate a hypothetical or real disease outbreak using all available data "
            "sources: case notification data, genomic sequences, climate data, hospital "
            "capacity, and international surveillance reports. Produce a comprehensive "
            "investigation report."
        ),
        expected_output=(
            "Full investigation integrating 5+ data sources, epidemiological curve, "
            "genomic context, environmental assessment, health system capacity assessment, "
            "international context, verified citations."
        ),
        evaluation_criteria=(
            "5+ data source integration, coherent narrative, proper investigation "
            "methodology, multi-jurisdictional awareness, publication quality."
        ),
    ),
    Task(
        id="T21",
        name="Predictive Model Evaluation Report",
        level=Level.PLATINUM,
        domain=Domain.D4,
        competencies=tuple(Competency),
        prompt=(
            "Evaluate available prediction models for a given disease in Brazil from the "
            "Mosqlimate model registry. Compare model types, spatial/temporal resolution, "
            "and prediction records. Assess forecast accuracy where scores are available."
        ),
        expected_output=(
            "Model comparison report with registry analysis, model type classification, "
            "resolution comparison, performance assessment, recommendations."
        ),
        evaluation_criteria=(
            "Mosqlimate registry navigation, model metadata extraction, proper comparison "
            "methodology, actionable recommendations."
        ),
    ),
]


_BY_ID: dict[str, Task] = {t.id: t for t in _TASKS}


def all_tasks() -> list[Task]:
    """Return all 21 benchmark tasks in canonical order."""
    return list(_TASKS)


def get_task(task_id: str) -> Task:
    """Look up a single task by id (e.g. 'T01'). Case-insensitive."""
    key = task_id.strip().upper()
    if key not in _BY_ID:
        raise KeyError(f"Unknown task id: {task_id!r}. Valid ids: T01..T21")
    return _BY_ID[key]


def total_max_points() -> int:
    """Sum of max points across all tasks (should be 540)."""
    return sum(t.max_points for t in _TASKS)


def _coerce_level(value: Level | str) -> Level:
    if isinstance(value, Level):
        return value
    needle = value.strip().lower()
    for lvl in Level:
        if lvl.value.lower() == needle:
            return lvl
    valid = ", ".join(lvl.value for lvl in Level)
    raise ValueError(f"{value!r} is not a valid level ({valid})")


def tasks_by_level(levels: Iterable[Level | str]) -> list[Task]:
    wanted = {_coerce_level(lvl) for lvl in levels}
    return [t for t in _TASKS if t.level in wanted]


def tasks_by_domain(domains: Iterable[Domain | str]) -> list[Task]:
    wanted = {Domain(d) if isinstance(d, str) else d for d in domains}
    return [t for t in _TASKS if t.domain in wanted]


def parse_task_selector(
    selector: str,
) -> list[Task]:
    """Parse a CLI selector string into a list of tasks.

    Examples:
        "all"                 -> every task
        "T01,T03"             -> just those tasks
        "bronze,silver"       -> all tasks in those levels
        "T01;bronze"          -> T01 plus every bronze task (deduped, ordered)
    """
    selector = selector.strip()
    if selector.lower() == "all":
        return all_tasks()

    parts: Iterable[str] = re.split(r"[;,]", selector)
    seen: set[str] = set()
    out: list[Task] = []
    for raw in parts:
        raw = raw.strip()
        if not raw:
            continue
        if raw.upper().startswith("T"):
            t = get_task(raw)
            if t.id not in seen:
                seen.add(t.id)
                out.append(t)
        else:
            for t in tasks_by_level([raw]):
                if t.id not in seen:
                    seen.add(t.id)
                    out.append(t)
    if not out:
        raise ValueError(f"Task selector {selector!r} matched no tasks")
    return out


__all__ = [
    "TOTAL_MAX_POINTS",
    "CATEGORY_WEIGHTS",
    "COMPETENCY_TO_CATEGORY",
    "LEVEL_TIME_BUDGETS",
    "LEVEL_MAX_POINTS",
    "Level",
    "Domain",
    "Competency",
    "Task",
    "all_tasks",
    "get_task",
    "total_max_points",
    "tasks_by_level",
    "tasks_by_domain",
    "parse_task_selector",
]


# Sentinel used by type checkers to indicate the registry is complete.
_TASK_COUNT: ClassVar = 21
assert len(_TASKS) == _TASK_COUNT, f"Expected {_TASK_COUNT} tasks, got {len(_TASKS)}"
assert total_max_points() == TOTAL_MAX_POINTS, "Task points mismatch"
assert TOTAL_MAX_POINTS == 610, (
    f"Per-task points sum to {TOTAL_MAX_POINTS}, expected 610 "
    "(README states 540 — see TOTAL_MAX_POINTS docstring)."
)
