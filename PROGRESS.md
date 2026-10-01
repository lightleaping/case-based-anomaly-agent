# 웹서비스 로그 기반 이상탐지·근거 기반 사건 분석 — 진행 기록

기준일: 2026-10-01

## 현재 상태

| 항목 | 상태 |
|---|---|
| 프로젝트 주제·MVP 범위 | 정리 |
| 전체 Pipeline 설계 | 진행 |
| 모듈 간 Input / Output 규격 | 조율 중 |
| 정상 A/B 비교 실험 | 진행 중 |
| 규칙 기반 탐지 기준선 | 진행 중 |
| TF-IDF 검색 기준선 | 채택 · 구현/연결 진행 중 |
| Agent·Backend 연결 초안 | 로컬 초안 존재 |
| 실제 Detection → Retrieval → Agent 연결 | 미완료 |
| UI·보고서 연결 | 목업·계획 단계 |
| End-to-End 검증 | 미완료 |
| 최종 성능 평가 | 미실시 |

---

## 담당

**김수진 — Team Lead / Agent·Backend**

현재 담당 범위:

- 프로젝트 주제와 MVP 범위 정리
- 전체 Pipeline과 모듈 간 Input / Output 규격 조율
- Ground Truth와 실제 분석 입력의 분리 원칙 정리
- 정상 데이터 A/B 비교 실험 방향 조율
- 이상탐지 결과와 원인 후보 분석의 역할 구분
- 근거·출처·불확실성을 포함한 분석 출력 구조 설계
- Agent·Backend 연결 작업
- 사건 식별자 기준 JSON 파일 저장 방식 설계
- 팀 발표자료 검토와 전체 프로젝트 설명 통합

---

## 현재 Pipeline

```text
웹서비스 장애 실험
→ 요청 로그
→ Window 집계
→ 이상탐지
→ events.json
→ 사례·Runbook 검색
→ related_cases.json
→ Agent·Backend
→ analysis.json
→ 사건 식별자 기준 JSON 저장
→ UI·보고서
```

현재 전체 Pipeline은 아직 연결 완료되지 않았습니다.

---

## 정상 A/B 첫 실험

첫 실험은 동일한 이상탐지 알고리즘을
서로 다른 정상 데이터 A/B에 각각 적용해 비교하는 방향으로 진행합니다.

```text
Normal A
→ Detector A
          ↘
           동일 Evaluation Data
          ↗
Normal B
→ Detector B
```

현재 방향:

- 정상 A/B의 요청량 조건은 우선 동일하게 유지
- 응답시간 분포를 다르게 구성
- 초기 Window는 10초
- 필요 시 20초·30초 비교
- 초기 특징:
  - `request_count`
  - `error_rate`
  - `mean_ms`
  - `p95_ms`
- 규칙 기반 탐지를 비교 기준선으로 사용
- 두 번째 AI 알고리즘 비교 여부는 첫 실험 결과 확인 후 결정

---

## Retrieval 방향

MVP 검색 기준선으로 **TF-IDF 기반 검색을 채택**했습니다.

현재는 구현 및 모듈 연결을 진행하는 단계이며,
작동이 완료된 것으로 기록하지 않습니다.

검색 결과는 Agent에 다음과 같은 근거 정보를 전달하는 방향으로 설계합니다.

```text
Document ID
Title
Source
Relevant Evidence
```

---

## Agent·Backend 연결 초안

현재 로컬에는 임시 Event와 가상 Retrieval 결과를 입력으로 받아
다음 흐름을 수행하는 연결 초안이 있습니다.

```text
입력 검증
→ 규칙 기반 원인 후보 생성
→ 근거 문서 ID 확인
→ 근거 부족 여부 확인
→ 판단 보류 처리
→ analysis.json 저장
```

현재 초안의 사건 식별에는 다음 값을 사용합니다.

```text
experiment_id
event_id
```

주요 출력 구조에는 다음 항목이 포함됩니다.

```text
analysis_status
cause_candidates
evidence_document_ids
judgment_deferred
additional_checks
```

이 필드들은 현재 **Agent·Backend 로컬 초안 규격**이며,
팀 전체의 최종 확정 Interface는 아닙니다.

실제 `events.json`, `related_cases.json`과 연결하면서 조정할 예정입니다.

---

## 현재 연결되지 않은 범위

로컬 Agent 초안은 아직 다음과 실제로 연결되지 않았습니다.

```text
실제 AI 이상탐지 결과
실제 TF-IDF 검색 결과
실제 LLM 호출
실제 UI·보고서
```

현재 공개 GitHub 저장소에도
Agent·Backend 실행 코드는 아직 포함되어 있지 않습니다.

---

## Ground Truth 원칙

장애 실험 과정에서 알고 있는 실제 장애 정보는
평가용 Ground Truth로 별도 관리합니다.

```text
System Input
→ 요청 로그
→ 집계 특징
→ 탐지 결과
→ 검색 결과

Evaluation Ground Truth
→ 실제 장애 종류
→ 발생 시점
→ 실제 원인
```

현재는 **정답 누출 방지를 위한 분리 원칙과 Interface를 설계한 단계**입니다.

전체 Pipeline에서 Ground Truth가 분석 입력에 노출되지 않는지에 대한
End-to-End 검증은 아직 완료되지 않았습니다.

---

## AI 도구 사용 및 검증

Agent·Backend 로컬 연결 초안에는
AI 코딩 도구를 활용한 작성·수정·실행 기록이 있습니다.

AI 도구가 작성하거나 실행한 결과만으로
김수진의 직접 구현·설명 가능 범위로 간주하지 않습니다.

다음 항목을 직접 확인한 범위부터 구현 경험으로 기록합니다.

```text
Clean Run
→ 코드 흐름 설명
→ 핵심 코드 직접 수정
→ Test 확인
→ 실패 조건 확인
→ 한계 설명
```

과거 AI 도구 실행 기록의 테스트 결과를
현재 공개 저장소에서 다시 검증한 결과처럼 표시하지 않습니다.

---

## 현재 면접 활용 범위

현재 설명 가능한 핵심 범위:

- 프로젝트 문제 정의
- 전체 Pipeline 설계
- 팀장으로서 모듈 Interface 조율
- 정상 A/B 비교 실험 방향
- Ground Truth 분리 원칙
- 이상탐지와 원인 분석 역할 구분
- TF-IDF 검색 기준선 채택 이유
- 근거·출처·불확실성을 포함한 Agent 출력 설계
- 근거 부족 시 판단 보류 정책

Agent·Backend 코드 구현 경험은
직접 실행·수정·설명 검증이 끝난 범위부터 추가합니다.

---

## 다음 작업

```text
1. 팀 공통 JSON Interface 확정
2. 정상 A/B 및 장애 실험 데이터 확인
3. Detection의 실제 events.json 연결
4. TF-IDF Retrieval 구현 및 related_cases.json 연결
5. 기존 Agent 초안을 실제 입력 규격에 맞게 수정
6. Agent 코드 직접 실행·설명·수정
7. Evidence / Uncertainty / Judgment Deferred 검증
8. 사건 식별자 기준 JSON 저장 연결
9. UI·Report 연결
10. End-to-End 및 실패 사례 평가
```

---

## 작업 기록

- **2026-09-10** — 초기 저장소와 프로젝트 운영 문서 작성
- **2026-09-29** — 정상 데이터 A/B 비교를 첫 실험 방향으로 정리
- **2026-10-01** — 최신 팀 프로젝트 구조와 Agent·Backend 담당 범위를 README에 반영
- **2026-10-01** — 로컬 Agent 초안, 실제 공개 구현, 미완료 연결 범위를 구분하여 기록
