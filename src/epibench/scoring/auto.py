"""Automated scoring against reference answers.

Per README §6, the following are graded automatically:
  - metric computation (numerical tiers, §5.3)
  - citation verification (PMID existence via NCBI E-utilities)
  - critical-error detection (§5.2 penalties): fabricated PMIDs, source
    attribution mismatches, unit/scale heuristics.

Everything else (interpretation quality, methodological rigor, report
structure, misleading-visualization judgment) is flagged for human review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..config import Settings
from ..tasks import Competency, Task
from .reference import ReferenceAnswer
from .rubric import (
    CategoryScores,
    Penalty,
    numerical_credit,
)


@dataclass
class AutoScoreResult:
    category_scores: CategoryScores
    penalties: dict[Penalty, int] = field(default_factory=dict)
    needs_human_review: bool = False
    notes: list[str] = field(default_factory=list)
    extracted_values: dict[str, float] = field(default_factory=dict)
    extracted_pmids: set[int] = field(default_factory=set)
    verified_pmids: dict[int, bool] = field(default_factory=dict)

    @property
    def has_privacy_violation(self) -> bool:
        return Penalty.PRIVACY_VIOLATION in self.penalties


# --------------------------------------------------------------------------- #
# Extraction helpers
# --------------------------------------------------------------------------- #
_PMID_RE = re.compile(r"(?:PMID[:\s]*|#)(\d{1,9})", re.IGNORECASE)
_NUMBER_TAG_RE = re.compile(
    r"(?P<key>[A-Za-z][\w \-/%]{0,40}?)\s*[:=]\s*(?P<value>-?\d+(?:[.,]\d+)?)"
)


def extract_pmids(text: str) -> set[int]:
    return {int(m) for m in _PMID_RE.findall(text)}


def extract_labeled_numbers(text: str) -> dict[str, float]:
    """Find 'label: number' patterns in the response. Best-effort, not strict."""
    out: dict[str, float] = {}
    for m in _NUMBER_TAG_RE.finditer(text):
        key = m.group("key").strip().lower().replace(" ", "_")
        try:
            out[key] = float(m.group("value").replace(",", ""))
        except ValueError:
            continue
    return out


# Privacy heuristic flags: obvious individual-level identifiers being reported.
_PRIVACY_PATTERNS = [
    re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"),  # BR CPF
    re.compile(r"\bCPF\b", re.IGNORECASE),
    re.compile(r"\bpatient\s+name", re.IGNORECASE),
    re.compile(r"\bnome\s+do\s+paciente", re.IGNORECASE),
]


def detect_privacy_violation(text: str) -> bool:
    return any(p.search(text) for p in _PRIVACY_PATTERNS)


def detect_source_mismatch(text: str, expected_sources: set[str]) -> list[str]:
    """Return the subset of expected sources that the response fails to mention."""
    lowered = text.lower()
    missing = []
    for src in expected_sources:
        if src.lower() not in lowered:
            missing.append(src)
    return missing


# --------------------------------------------------------------------------- #
# Keyword-based proxies for methodology, visualization and interpretation.
# These are intentionally coarse: they give models partial auto-credit while
# still flagging the task for human review (README §6).
# --------------------------------------------------------------------------- #
_VIZ_KEYWORDS = re.compile(
    r"\b(plot|chart|figure|graph|visualization|visualisation|map|choropleth|"
    r"time.series|bar chart|line chart|histogram|scatter)\b",
    re.IGNORECASE,
)


def detect_visualization(text: str) -> float:
    """Return 1.0 if the response mentions creating a visualization, else 0.0."""
    return 1.0 if _VIZ_KEYWORDS.search(text) else 0.0


def detect_keyword_coverage(text: str, keywords: list[str]) -> float:
    """Fraction of reference keywords that appear in the text.

    Keywords may use underscores (e.g. "peak_month"); the text may use spaces,
    underscores or hyphens ("peak month", "peak-month"). Matching is word-based
    and treats these separators equivalently.
    """
    if not keywords:
        return 0.0
    lowered = text.lower()
    # Normalize separators to spaces so "peak_month" matches "peak month".
    normalized_text = re.sub(r"[_\-]+", " ", lowered)
    hits = 0
    for kw in keywords:
        normalized_kw = re.sub(r"[_\-]+", " ", kw.lower())
        if re.search(rf"\b{re.escape(normalized_kw)}\b", normalized_text):
            hits += 1
    return hits / len(keywords)


def detect_interpretation_keywords(text: str, keywords: list[str]) -> float:
    """Alias for detect_keyword_coverage; used for interpretation scoring."""
    return detect_keyword_coverage(text, keywords)


# --------------------------------------------------------------------------- #
# PMID verification (NCBI E-utilities). Network is optional.
# --------------------------------------------------------------------------- #
def verify_pmids(
    pmids: set[int], settings: Settings | None = None
) -> dict[int, bool]:
    """Verify PMIDs exist in PubMed. Returns {pmid: exists?}.

    Uses NCBI ESummary. On any error or when network scoring is disabled,
    returns every PMID as `False` (cannot verify) — never raises.
    """
    if not pmids:
        return {}
    from ..config import load_settings

    settings = settings or load_settings()
    if not settings.allow_network_scoring:
        return {p: False for p in pmids}

    try:
        import requests  # local import keeps test surface small
    except ImportError:  # pragma: no cover
        return {p: False for p in pmids}

    params = {
        "db": "pubmed",
        "id": ",".join(str(p) for p in pmids),
        "tool": settings.ncbi_tool,
    }
    if settings.ncbi_email:
        params["email"] = settings.ncbi_email
    if settings.ncbi_api_key:
        params["api_key"] = settings.ncbi_api_key

    try:
        resp = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params=params,
            timeout=settings.http_timeout,
        )
        resp.raise_for_status()
    except Exception:
        return {p: False for p in pmids}

    payload = resp.json()
    result = {}
    uids = set(payload.get("result", {}).get("uids", []))
    for p in pmids:
        result[p] = str(p) in uids
    return result


# --------------------------------------------------------------------------- #
# Top-level auto-score
# --------------------------------------------------------------------------- #
def auto_score(
    task: Task,
    response_text: str,
    reference: ReferenceAnswer,
    settings: Settings | None = None,
) -> AutoScoreResult:
    """Score a single response against its reference (if any)."""
    from ..config import load_settings

    settings = settings or load_settings()

    result = AutoScoreResult(category_scores=CategoryScores())
    result.extracted_pmids = extract_pmids(response_text)
    result.extracted_values = extract_labeled_numbers(response_text)

    # Privacy violation overrides everything (§5.2 rule 3).
    if detect_privacy_violation(response_text):
        result.penalties[Penalty.PRIVACY_VIOLATION] = -20
        result.notes.append("Privacy violation detected — automatic failure.")

    # If no reference answer exists yet, we cannot auto-score; flag for review.
    if not reference.exists:
        result.needs_human_review = True
        result.notes.append("No reference answer published yet — requires human review.")
        return result

    # ---- Data retrieval & quality ----------------------------------------- #
    if reference.expected_sources:
        missing = detect_source_mismatch(response_text, reference.expected_sources)
        if reference.require_all_sources:
            coverage = 1.0 - len(missing) / len(reference.expected_sources)
            result.category_scores.data_retrieval = coverage
            if missing:
                result.penalties[Penalty.INCORRECT_SOURCE] = -5
                result.notes.append(f"Missing/incorrect sources: {', '.join(missing)}")
        else:
            # Any acceptable source counts; full credit if at least one is mentioned.
            mentioned = len(reference.expected_sources) - len(missing)
            coverage = 1.0 if mentioned > 0 else 0.0
            result.category_scores.data_retrieval = coverage
            result.notes.append(
                f"Acceptable sources: {', '.join(sorted(reference.expected_sources))}; "
                f"mentioned: {mentioned}"
            )
    elif task.weight_categories and "data_retrieval" in task.weight_categories:
        result.category_scores.data_retrieval = None  # needs human review
        result.needs_human_review = True

    # ---- Methodological correctness (numerical or keyword-based) ---------- #
    if reference.expected_values:
        credits = []
        matched = 0
        for name, ref_val in reference.expected_values.items():
            cand = _match_extracted_value(name, result.extracted_values)
            if cand is None:
                credits.append(0.0)
                continue
            credit, tier = numerical_credit(ref_val, cand)
            credits.append(credit)
            if tier.credit > 0:
                matched += 1
            result.notes.append(f"{name}: candidate={cand}, reference={ref_val} -> {tier.name}")
        if credits:
            result.category_scores.methodology = sum(credits) / len(credits)
        if matched == 0 and reference.expected_values:
            # correct-method/wrong-result is a human judgment; flag it.
            result.needs_human_review = True
    elif reference.methodology_keywords:
        # No numerical reference values, but methodology keywords are provided.
        # Give partial credit for mentioning expected methodological elements.
        coverage = detect_keyword_coverage(response_text, reference.methodology_keywords)
        result.category_scores.methodology = coverage
        result.notes.append(
            f"Methodology keyword coverage: {coverage:.0%} "
            f"({reference.methodology_keywords})"
        )
        result.needs_human_review = True
    else:
        result.category_scores.methodology = None  # human review
        result.needs_human_review = True

    # ---- Citations -------------------------------------------------------- #
    has_citation_focus = (
        Competency.J in task.competencies
        or bool(reference.expected_pmids)
        or bool(reference.minimum_required_pmids)
    )
    if has_citation_focus:
        verified = verify_pmids(result.extracted_pmids, settings)
        result.verified_pmids = verified
        cited = result.extracted_pmids
        # Fabricated citation: a PMID the model cited that does not exist.
        fabricated = [p for p, ok in verified.items() if not ok] if verified else []
        if fabricated and settings.allow_network_scoring:
            result.penalties[Penalty.FABRICATED_CITATION] = -10
            result.notes.append(f"Fabricated/unverified PMIDs: {fabricated}")

        if reference.minimum_required_pmids:
            coverage = min(1.0, len(cited) / reference.minimum_required_pmids)
            result.category_scores.citations = coverage
        elif verified:
            ok = sum(1 for v in verified.values() if v)
            result.category_scores.citations = ok / len(verified) if verified else 0.0

    # ---- Visualization & interpretation ----------------------------------- #
    # Both require a human reviewer per §6, but we award coarse auto-credit when
    # the response mentions a visualization or expected interpretive keywords.
    if task.weight_categories and "visualization" in task.weight_categories:
        viz_score = detect_visualization(response_text)
        result.category_scores.visualization = viz_score
        if viz_score < 1.0:
            result.notes.append("Visualization mentioned? no (flagged for human review)")
        else:
            result.notes.append("Visualization mentioned: yes (still requires human review)")
        result.needs_human_review = True
    if task.weight_categories and "interpretation" in task.weight_categories:
        interp_keywords = reference.methodology_keywords or []
        interp_score = detect_interpretation_keywords(response_text, interp_keywords)
        result.category_scores.interpretation = interp_score
        if interp_keywords:
            result.notes.append(
                f"Interpretation keyword coverage: {interp_score:.0%} "
                f"({interp_keywords})"
            )
        result.needs_human_review = True

    return result


def _match_extracted_value(name: str, extracted: dict[str, float]) -> float | None:
    """Match a reference value name against best-effort extracted labels."""
    key = name.strip().lower().replace(" ", "_")
    if key in extracted:
        return extracted[key]
    # Loose substring match.
    for ex_key, val in extracted.items():
        if key in ex_key or ex_key in key:
            return val
    return None
