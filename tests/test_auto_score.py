from __future__ import annotations

from epibench.scoring.auto import (
    auto_score,
    detect_privacy_violation,
    detect_source_mismatch,
    extract_labeled_numbers,
    extract_pmids,
    verify_pmids,
)
from epibench.scoring.reference import ReferenceAnswer
from epibench.scoring.rubric import Penalty
from epibench.tasks import get_task


def test_extract_pmids_handles_various_formats():
    text = "See PMID: 36631231 and PMID:12345 and also #99999."
    assert extract_pmids(text) == {36631231, 12345, 99999}


def test_extract_labeled_numbers_finds_pairs():
    text = "Incidence rate: 123.4 per 100k. Case-fatality rate=0.05"
    vals = extract_labeled_numbers(text)
    assert vals["incidence_rate"] == 123.4
    assert vals["case-fatality_rate"] == 0.05


def test_detect_privacy_violation_cpf():
    assert detect_privacy_violation("Patient CPF: 123.456.789-00") is True
    assert detect_privacy_violation("Aggregated case counts only.") is False


def test_detect_source_mismatch():
    text = "We used SINAN and WHO data."
    missing = detect_source_mismatch(text, {"SINAN", "SIM", "WHO"})
    assert missing == ["SIM"]


def test_auto_score_no_reference_flags_human_review(monkeypatch):
    monkeypatch.setenv("EPIBENCH_NETWORK_SCORING", "0")
    task = get_task("T03")
    result = auto_score(task, "Some answer text.", ReferenceAnswer(task_id="T03"))
    assert result.needs_human_review is True
    assert result.penalties == {}


def test_auto_score_source_coverage(monkeypatch):
    monkeypatch.setenv("EPIBENCH_NETWORK_SCORING", "0")
    task = get_task("T01")
    reference = ReferenceAnswer(
        task_id="T01",
        expected_sources={"SINAN", "SIM", "SINASC"},
        raw={"placeholder": True},
    )
    # Mentions 2 of 3 expected sources.
    result = auto_score(task, "Data from SINAN and SIM are available.", reference)
    assert result.category_scores.data_retrieval is not None
    assert 0 < result.category_scores.data_retrieval < 1.0
    # Missing one source triggers the incorrect-source penalty.
    assert Penalty.INCORRECT_SOURCE in result.penalties


def test_auto_score_numerical(monkeypatch):
    monkeypatch.setenv("EPIBENCH_NETWORK_SCORING", "0")
    task = get_task("T03")
    reference = ReferenceAnswer(
        task_id="T03",
        expected_values={"incidence_rate": 100.0},
        raw={"placeholder": True},
    )
    # Exact match.
    result = auto_score(task, "Incidence rate: 100.0", reference)
    assert result.category_scores.methodology == 1.0
    # 8% off → within 10% tier (0.6 credit).
    result = auto_score(task, "Incidence rate: 108.0", reference)
    assert result.category_scores.methodology == 0.6


def test_verify_pmids_handles_non_json_response(monkeypatch):
    """If NCBI returns an empty or non-JSON body, verify_pmids must not crash."""
    monkeypatch.setenv("EPIBENCH_NETWORK_SCORING", "1")

    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            raise ValueError("No JSON object could be decoded")

    monkeypatch.setattr("requests.get", lambda *args, **kwargs: FakeResponse())
    result = verify_pmids({12345678})
    assert result == {12345678: False}
