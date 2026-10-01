"""Draft event -> retrieval handoff -> evidence-bound analysis. Standard library only."""

import argparse
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path

VERSION = "draft-rule-1"


def require_text(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"MISSING_OR_INVALID:{name}")
    return value


def make_request(events, event_id):
    """Pass complete observed symptoms only after a narrow MVP format check."""
    experiment_id = require_text(events.get("experiment_id"), "experiment_id")
    matches = [e for e in events.get("events", []) if e.get("event_id") == event_id]
    if len(matches) != 1:
        raise ValueError("EVENT_ID_NOT_UNIQUE_OR_MISSING")
    event = matches[0]
    endpoint = require_text(event.get("affected_endpoint"), "affected_endpoint")
    if not re.fullmatch(r"/[A-Za-z0-9/_{}.-]*", endpoint):
        raise ValueError("MISSING_OR_INVALID:affected_endpoint")
    anomaly_type = event.get("anomaly_type")
    if anomaly_type != "error_rate_increase":
        raise ValueError("MISSING_OR_INVALID:anomaly_type")
    request_count = event.get("request_count")
    if type(request_count) is not int or request_count < 0:
        raise ValueError("MISSING_OR_INVALID:request_count")
    error_rate = event.get("error_rate")
    if error_rate is not None and (type(error_rate) not in (int, float) or not math.isfinite(error_rate) or not 0 <= error_rate <= 1):
        raise ValueError("MISSING_OR_INVALID:error_rate")
    symptoms = event.get("observed_symptoms")
    if not isinstance(symptoms, list) or not symptoms or any(not isinstance(s, str) for s in symptoms):
        raise ValueError("MISSING_OR_INVALID:observed_symptoms")
    status_codes = []
    for symptom in symptoms:
        match = re.fullmatch(r"(/[A-Za-z0-9/_{}.-]*) 요청 (\d+)건 중 (\d+)건에서 HTTP ([45]\d{2}) 관측", symptom)
        if not match:
            raise ValueError("UNSUPPORTED_OR_UNSAFE_OBSERVED_SYMPTOM")
        symptom_endpoint, total, errors, status = match.groups()
        if symptom_endpoint != endpoint or int(total) != request_count or int(total) == 0 or int(errors) > int(total) or error_rate is None or not math.isclose(int(errors) / int(total), error_rate, abs_tol=1e-9):
            raise ValueError("OBSERVED_SYMPTOM_METRIC_MISMATCH")
        status_codes.append(int(status))
    status_codes = sorted(set(status_codes))
    return {"experiment_id": experiment_id, "event_id": event_id,
            "query": " ".join(symptoms),
            "observations": {"affected_endpoint": endpoint, "anomaly_type": anomaly_type,
                             "request_count": request_count, "error_rate": error_rate,
                             "http_status_codes": status_codes,
                             "observed_symptoms": symptoms,
                             "evidence_log_ids": event.get("evidence_log_ids", [])}}


def load_related_fixture(path, request):
    """Replace this adapter with Lee's search API invocation when its contract arrives."""
    related = json.loads(Path(path).read_text(encoding="utf-8"))
    validate_related(related)
    if related.get("experiment_id") != request["experiment_id"] or related.get("event_id") != request["event_id"]:
        raise ValueError("RETRIEVAL_EVENT_MISMATCH")
    if related.get("query") != request["query"]:
        raise ValueError("RETRIEVAL_QUERY_MISMATCH")
    return related


def validate_related(related):
    for key in ("schema_version", "experiment_id", "event_id", "query", "retrieval_method"):
        require_text(related.get(key), key)
    results = related.get("results")
    if related.get("status") not in ("ok", "no_results") or not isinstance(results, list):
        raise ValueError("MISSING_OR_INVALID:retrieval_status_or_results")
    if (related["status"] == "ok") != bool(results):
        raise ValueError("RETRIEVAL_STATUS_RESULTS_MISMATCH")
    ids = set()
    for index, item in enumerate(results, 1):
        if not isinstance(item, dict) or item.get("rank") != index:
            raise ValueError("INVALID_RETRIEVAL_RANK")
        for key in ("document_id", "document_type", "title", "source_type", "source", "matched_evidence"):
            require_text(item.get(key), f"results[{index}].{key}")
        if "possible_cause" not in item or (item["possible_cause"] is not None and (not isinstance(item["possible_cause"], str) or not item["possible_cause"].strip())):
            raise ValueError(f"MISSING_OR_INVALID:results[{index}].possible_cause")
        checks = item.get("recommended_checks")
        if not isinstance(checks, list) or any(not isinstance(check, str) or not check.strip() for check in checks):
            raise ValueError(f"MISSING_OR_INVALID:results[{index}].recommended_checks")
        if item["document_id"] in ids:
            raise ValueError("DUPLICATE_DOCUMENT_ID")
        ids.add(item["document_id"])
    return ids


def analyze(request, related):
    """Conservative rule baseline; a future LLM replaces only this function."""
    validate_related(related)
    observations = request["observations"]
    candidates = []
    checks = []
    for item in related["results"]:
        documented_codes = {int(code) for code in re.findall(r"\bHTTP\s+([45]\d{2})(?!\d)", item["matched_evidence"], re.IGNORECASE)}
        if not documented_codes.intersection(observations["http_status_codes"]):
            continue
        checks.extend(item["recommended_checks"])
        cause = item.get("possible_cause")
        if isinstance(cause, str) and cause.strip() in item["matched_evidence"]:
            observed = "; ".join(observations["observed_symptoms"])
            document_context = f'{item["document_id"]} ({item["source"]})'
            candidates.append({"rank": len(candidates) + 1, "cause": cause.strip(),
                               "confidence": "low",
                               "reasoning_summary": f'관측: {observed}. 참고 문서 {document_context}: {item["matched_evidence"]} 이 문서의 가능한 원인을 후보로만 제시하며 현재 사건의 원인은 확인되지 않았다.',
                               "evidence_log_ids": [],
                               "evidence_document_ids": [item["document_id"]]})
    # This baseline never promotes an old case to a confirmed diagnosis.
    return {"schema_version": "draft-1", "experiment_id": request["experiment_id"],
            "event_id": request["event_id"],
            "analysis_status": "analyzed" if candidates else "insufficient_evidence",
            "judgment_deferred": True, "cause_candidates": candidates,
            "uncertainty": "검색 문서의 과거 원인이 현재 사건에도 해당하는지 확인되지 않았다." if candidates else "검색 결과에 현재 사건의 원인 후보로 인용할 정보가 부족하다.",
            "additional_checks": list(dict.fromkeys(checks)) or ["해당 사건의 요청 및 서버 기록 확인"],
            "recommended_actions": [],
            "used_documents": list(dict.fromkeys(d for c in candidates for d in c["evidence_document_ids"])),
            "errors": [], "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "model_or_rule_version": VERSION}


def validate_analysis(analysis, related, request):
    ids = validate_related(related)
    if not isinstance(analysis, dict):
        raise ValueError("MISSING_OR_INVALID:analysis")
    for key in ("schema_version", "experiment_id", "event_id", "analysis_status", "uncertainty", "generated_at", "model_or_rule_version"):
        require_text(analysis.get(key), key)
    if not isinstance(analysis.get("judgment_deferred"), bool):
        raise ValueError("MISSING_OR_INVALID:judgment_deferred")
    for key in ("cause_candidates", "additional_checks", "recommended_actions", "used_documents", "errors"):
        if not isinstance(analysis.get(key), list):
            raise ValueError(f"MISSING_OR_INVALID:{key}")
    if analysis["analysis_status"] not in ("analyzed", "insufficient_evidence") or (analysis["analysis_status"] == "analyzed") != bool(analysis["cause_candidates"]):
        raise ValueError("ANALYSIS_STATUS_CANDIDATES_MISMATCH")
    if analysis["model_or_rule_version"] == VERSION and not analysis["judgment_deferred"]:
        raise ValueError("RULE_CANNOT_CONFIRM_CAUSE")
    if analysis.get("experiment_id") != request["experiment_id"] or analysis.get("event_id") != request["event_id"]:
        raise ValueError("ANALYSIS_EVENT_MISMATCH")
    cited = []
    for index, candidate in enumerate(analysis["cause_candidates"], 1):
        if not isinstance(candidate, dict) or candidate.get("rank") != index:
            raise ValueError("INVALID_CANDIDATE_RANK")
        for key in ("cause", "confidence", "reasoning_summary"):
            require_text(candidate.get(key), f"cause_candidates[{index}].{key}")
        for key in ("evidence_document_ids", "evidence_log_ids"):
            values = candidate.get(key)
            if not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values):
                raise ValueError(f"MISSING_OR_INVALID:cause_candidates[{index}].{key}")
        for doc_id in candidate["evidence_document_ids"]:
            if doc_id not in ids:
                raise ValueError(f"UNKNOWN_EVIDENCE_DOCUMENT_ID:{doc_id}")
            cited.append(doc_id)
        if not candidate["evidence_document_ids"]:
            raise ValueError("CANDIDATE_WITHOUT_DOCUMENT_EVIDENCE")
        for log_id in candidate["evidence_log_ids"]:
            if log_id not in request["observations"]["evidence_log_ids"]:
                raise ValueError(f"UNKNOWN_EVIDENCE_LOG_ID:{log_id}")
    if set(analysis.get("used_documents", [])) != set(cited):
        raise ValueError("USED_DOCUMENTS_MISMATCH")
    return {"candidate_count": len(analysis.get("cause_candidates", [])),
            "checked_document_ids": sorted(set(cited)),
            "citation_status": "valid" if cited else "none",
            "all_evidence_ids_exist": True if cited else None}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", required=True)
    parser.add_argument("--related", required=True)
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    events = json.loads(Path(args.events).read_text(encoding="utf-8"))
    request = make_request(events, args.event_id)
    related = load_related_fixture(args.related, request)
    analysis = analyze(request, related)
    check = validate_analysis(analysis, related, request)
    Path(args.output).write_text(json.dumps(analysis, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"retrieval_request": request, "evidence_check": check}, ensure_ascii=False))


if __name__ == "__main__":
    main()
