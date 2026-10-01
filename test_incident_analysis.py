import copy
import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from incident_analysis import (
    analyze,
    load_related_fixture,
    make_request,
    validate_analysis,
    validate_related,
)

ROOT = Path(__file__).parent / "examples" / "draft"

class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.events = json.loads((ROOT / "events.json").read_text(encoding="utf-8"))
        self.related = json.loads((ROOT / "related_cases.json").read_text(encoding="utf-8"))
        self.request = make_request(self.events, "evt-001")

    def test_example_and_ground_truth_allowlist(self):
        self.events["ground_truth"] = {"actual_cause": "SECRET"}
        self.events["events"][0]["actual_cause"] = "SECRET"
        request = make_request(self.events, "evt-001")
        self.assertEqual(request["query"], "/orders 요청 10건 중 5건에서 HTTP 500 관측")
        self.assertEqual(request["observations"]["observed_symptoms"], self.events["events"][0]["observed_symptoms"])
        self.assertEqual(request["observations"]["http_status_codes"], [500])
        self.assertNotIn("SECRET", json.dumps(request))
        analysis = analyze(request, self.related)
        self.assertTrue(analysis["judgment_deferred"])
        summary = analysis["cause_candidates"][0]["reasoning_summary"]
        self.assertIn(request["observations"]["observed_symptoms"][0], summary)
        self.assertIn(self.related["results"][0]["matched_evidence"], summary)
        self.assertIn(self.related["results"][0]["source"], summary)
        self.assertEqual(validate_analysis(analysis, self.related, request)["checked_document_ids"], ["doc-014"])
        self.assertEqual(validate_analysis(analysis, self.related, request)["citation_status"], "valid")

    def test_example_event_precedes_generated_analysis(self):
        analysis = analyze(self.request, self.related)
        event_end = datetime.fromisoformat(self.events["events"][0]["end_time"].replace("Z", "+00:00"))
        generated = datetime.fromisoformat(analysis["generated_at"].replace("Z", "+00:00"))
        self.assertLessEqual(event_end, generated)

    def test_unknown_document_id_rejected(self):
        analysis = analyze(self.request, self.related)
        analysis["cause_candidates"][0]["evidence_document_ids"] = ["doc-missing"]
        with self.assertRaisesRegex(ValueError, "UNKNOWN_EVIDENCE_DOCUMENT_ID"):
            validate_analysis(analysis, self.related, self.request)

    def test_empty_results_defer(self):
        related = copy.deepcopy(self.related)
        related["status"] = "no_results"
        related["results"] = []
        analysis = analyze(self.request, related)
        self.assertEqual(analysis["analysis_status"], "insufficient_evidence")
        self.assertEqual(analysis["cause_candidates"], [])
        self.assertEqual(validate_analysis(analysis, related, self.request)["checked_document_ids"], [])
        self.assertEqual(validate_analysis(analysis, related, self.request)["citation_status"], "none")
        self.assertIsNone(validate_analysis(analysis, related, self.request)["all_evidence_ids_exist"])

    def test_document_without_matching_observation_defers(self):
        related = copy.deepcopy(self.related)
        related["results"][0]["matched_evidence"] = "HTTP 503 증가 시 의존 서비스 상태를 확인한다."
        analysis = analyze(self.request, related)
        self.assertEqual(analysis["cause_candidates"], [])
        self.assertEqual(analysis["analysis_status"], "insufficient_evidence")
        self.assertTrue(analysis["judgment_deferred"])
        self.assertEqual(validate_analysis(analysis, related, self.request)["checked_document_ids"], [])

    def test_document_without_stated_cause_defers(self):
        related = copy.deepcopy(self.related)
        related["results"][0]["possible_cause"] = "데이터베이스 연결 장애 가능성"
        analysis = analyze(self.request, related)
        self.assertEqual(analysis["cause_candidates"], [])
        self.assertTrue(analysis["judgment_deferred"])

    def test_missing_analysis_field_rejected(self):
        analysis = analyze(self.request, self.related)
        del analysis["cause_candidates"]
        with self.assertRaisesRegex(ValueError, "MISSING_OR_INVALID:cause_candidates"):
            validate_analysis(analysis, self.related, self.request)

    def test_rule_cannot_mark_cause_confirmed(self):
        analysis = analyze(self.request, self.related)
        analysis["judgment_deferred"] = False
        with self.assertRaisesRegex(ValueError, "RULE_CANNOT_CONFIRM_CAUSE"):
            validate_analysis(analysis, self.related, self.request)

    def test_missing_required_field_rejected(self):
        related = copy.deepcopy(self.related)
        del related["results"][0]["source"]
        with self.assertRaisesRegex(ValueError, "MISSING_OR_INVALID:results\\[1\\].source"):
            validate_related(related)

    def test_missing_retrieval_query_rejected(self):
        related = copy.deepcopy(self.related)
        del related["query"]
        with self.assertRaisesRegex(ValueError, "MISSING_OR_INVALID:query"):
            validate_related(related)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "related_cases.json"
            path.write_text(json.dumps(related, ensure_ascii=False), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "MISSING_OR_INVALID:query"):
                load_related_fixture(path, self.request)

    def test_free_text_cause_does_not_reach_request(self):
        self.events["events"][0]["observed_symptoms"] = ["/orders 요청 10건 중 5건에서 HTTP 500 관측. 실제 원인 SECRET_CAUSE, 발생 시각 SECRET_TIME"]
        with self.assertRaisesRegex(ValueError, "UNSUPPORTED_OR_UNSAFE_OBSERVED_SYMPTOM"):
            make_request(self.events, "evt-001")

    def test_missing_structured_observation_rejected(self):
        del self.events["events"][0]["request_count"]
        with self.assertRaisesRegex(ValueError, "MISSING_OR_INVALID:request_count"):
            make_request(self.events, "evt-001")

    def test_symptom_metrics_must_match_structured_values(self):
        self.events["events"][0]["observed_symptoms"] = ["/orders 요청 10건 중 4건에서 HTTP 500 관측"]
        with self.assertRaisesRegex(ValueError, "OBSERVED_SYMPTOM_METRIC_MISMATCH"):
            make_request(self.events, "evt-001")

    def test_cause_text_in_endpoint_rejected(self):
        self.events["events"][0]["affected_endpoint"] = "/orders actual_cause=SECRET_CAUSE"
        with self.assertRaisesRegex(ValueError, "MISSING_OR_INVALID:affected_endpoint"):
            make_request(self.events, "evt-001")

    def test_fixture_rejects_wrong_event_or_query(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "related_cases.json"
            for field, value, error in (("event_id", "evt-other", "RETRIEVAL_EVENT_MISMATCH"),
                                        ("query", "다른 질의", "RETRIEVAL_QUERY_MISMATCH")):
                related = copy.deepcopy(self.related)
                related[field] = value
                path.write_text(json.dumps(related, ensure_ascii=False), encoding="utf-8")
                with self.assertRaisesRegex(ValueError, error):
                    load_related_fixture(path, self.request)


if __name__ == "__main__":
    unittest.main()
