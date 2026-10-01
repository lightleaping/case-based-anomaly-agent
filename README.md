# 웹서비스 로그 기반 이상탐지·근거 기반 사건 분석
### Case-based Web Service Incident Analysis Agent

**Anomaly Detection, Case/Runbook Retrieval, Evidence-based Analysis, and Agent Backend**

<p>
  <img src="https://img.shields.io/badge/Status-Work%20in%20Progress-EAA12B?style=flat-square" alt="Work in Progress">
  <img src="https://img.shields.io/badge/Project-Team%20Project-3561D8?style=flat-square" alt="Team Project">
  <img src="https://img.shields.io/badge/Role-Team%20Lead-151F32?style=flat-square" alt="Team Lead">
  <img src="https://img.shields.io/badge/Area-Agent%20%26%20Backend-21AFC4?style=flat-square" alt="Agent Backend">
</p>

> 웹서비스 요청 로그에서 이상 사건을 탐지하고,
> 관련 사례·Runbook을 검색해 **근거 기반 원인 후보와 사건 분석 결과**로 연결하는
> AI종합설계 팀 프로젝트입니다.
>
> **Status: Work in Progress · Team Lead / Agent·Backend**  
> 상태 기준일: 2026-10-01

---

## Why This Project

웹서비스 장애 대응에서는 단순히 이상 여부를 탐지하는 것만으로는 충분하지 않습니다.

이상이 발생했다면 다음 질문까지 이어져야 합니다.

```text
어떤 변화가 발생했는가?
→ 어떤 장애 사례와 관련 있는가?
→ 가능한 원인 후보는 무엇인가?
→ 어떤 근거로 그렇게 판단했는가?
```

이 프로젝트는 이상탐지 결과만 반환하는 것이 아니라,

```text
요청 로그
→ 이상탐지
→ 사례·Runbook 검색
→ 근거 기반 원인 후보 분석
→ 사건 분석 결과
```

까지 연결하는 것을 목표로 합니다.

---

## Project Overview

| 항목 | 내용 |
|---|---|
| **기간** | 2026.09–현재 |
| **형태** | AI종합설계 팀 프로젝트 |
| **역할** | 팀장 / Agent·Backend |
| **대상** | 웹서비스 요청 로그 기반 장애 실험 |
| **목표** | 탐지 → 검색 → 근거 기반 분석 → UI·보고서 연결 |
| **현재 단계** | 각 모듈 구현 및 Interface 연결 진행 중 |
| **Agent 방향** | 관측 데이터와 검색 근거를 기반으로 원인 후보·근거·불확실성 구조화 |
| **평가 원칙** | Ground Truth를 모델·Agent 입력에서 분리 |

현재 공개 저장소에는 설계 및 진행 문서가 있으며,
Agent·Backend의 로컬 연결 초안은 아직 공개 저장소에 포함되어 있지 않습니다.

---

## Problem → Implementation → Result

| Problem | Implementation / Design | Current Result |
|---|---|---|
| 정상 상태 자체가 하나의 고정 패턴이 아닐 수 있음 | 서로 다른 정상 데이터 A/B를 기준으로 동일한 탐지 알고리즘 비교 | 첫 실험 방향으로 진행 |
| AI 이상 점수가 실제 장애 원인처럼 해석될 수 있음 | 이상탐지 결과와 원인 분석 결과를 분리 | Detection과 Cause Analysis 역할 구분 |
| 평가용 장애 정보가 입력에 포함되면 정답 누출이 발생함 | Ground Truth와 실제 분석 입력 분리 원칙 및 Interface 설계 | 평가 구조에 반영 |
| 탐지 결과만으로 원인을 설명하기 어려움 | 사례·Runbook 검색 결과를 Agent 근거로 전달 | Retrieval 구현·연결 진행 중 |
| Agent가 근거 없는 원인을 생성할 수 있음 | 근거 문서 ID·출처·불확실성 및 판단 보류 구조 설계 | 로컬 연결 초안에 일부 반영 |
| 팀원이 각 모듈을 별도로 개발함 | JSON 기반 Input / Output Interface 정의 | 모듈 연결 규격 조율 중 |

---

## System Overview

목표하는 전체 흐름은 다음과 같습니다.

```text
Web Service
↓
Request Logs
↓
Window Aggregation
↓
Anomaly Detection
↓
events.json
↓
Case / Runbook Retrieval
↓
related_cases.json
↓
Agent / Backend
↓
analysis.json
↓
사건 식별자 기준 JSON 파일 저장 — MVP 설계
↓
UI / Incident Report
```

현재 전체 End-to-End 연결은 완료되지 않았으며,
각 모듈의 출력 형식을 맞추면서 순차적으로 연결하고 있습니다.

---

## My Role

**Team Lead / Agent·Backend**

- 프로젝트 주제와 MVP 범위 정리
- 전체 Pipeline과 모듈 간 Input / Output 규격 조율
- Ground Truth와 실제 분석 입력의 분리 원칙 정리
- 정상 데이터 A/B 비교 실험 방향 조율
- 이상탐지 결과와 Agent 원인 후보의 역할 구분
- 근거·출처·불확실성을 포함한 분석 출력 구조 설계
- Agent·Backend 연결 작업
- 사건 식별자 기준 JSON 저장 방식 설계
- 팀 발표자료 검토와 전체 프로젝트 설명 통합

Agent·Backend 구현은 진행 중이며,
직접 실행·수정·설명할 수 있는 범위를 기준으로 공개 상태를 갱신합니다.

---

## Technical Details

<details open>
<summary><b>01 | Normal A/B Experiment</b></summary>

<br>

첫 실험은 **동일한 이상탐지 알고리즘을 서로 다른 정상 데이터 A/B로 각각 학습**하여,
동일한 평가 데이터에 대한 이상 점수와 판정 차이를 비교합니다.

```text
Normal A
→ Detector A
          ↘
           Same Evaluation Data
          ↗
Normal B
→ Detector B
```

정상 A/B는 우선 요청량 조건을 동일하게 두고,
응답시간 분포를 다르게 구성합니다.

규칙 기반 탐지는 비교 기준선으로 사용합니다.

두 번째 AI 알고리즘 비교 여부는
첫 실험 결과를 확인한 뒤 결정합니다.

</details>

<details>
<summary><b>02 | Request Log and Window Aggregation</b></summary>

<br>

원본 요청 로그는 팀에서 합의한 `requests.csv` 규격을 사용합니다.

현재 README에서는 실제 공개 파일과 규격이 일치하기 전까지
구체적인 원본 열 이름을 임의로 기재하지 않습니다.

요청 로그는 일정 시간 Window 단위로 집계한 뒤
이상탐지 입력으로 사용합니다.

초기 집계 구간:

```text
10 seconds
```

구간당 요청 수가 적어 `p95_ms`가 불안정한 경우
20초·30초 Window를 비교합니다.

첫 집계 특징:

```text
request_count
error_rate
mean_ms
p95_ms
```

</details>

<details>
<summary><b>03 | Anomaly Detection</b></summary>

<br>

Window 단위 특징을 이용해
정상 패턴과 다른 구간을 식별하는 구조입니다.

```text
Aggregated Window
→ Anomaly Detector
→ Anomaly Score / Decision
→ events.json
```

핵심 원칙은 다음과 같습니다.

```text
Anomaly Score ≠ Root Cause
```

높은 이상 점수는 비정상적인 관측이 나타났다는 의미이며,
그 자체를 장애의 실제 원인으로 해석하지 않습니다.

규칙 기반 탐지는 AI 탐지 결과와 비교하기 위한 기준선으로 사용합니다.

</details>

<details>
<summary><b>04 | Case / Runbook Retrieval</b></summary>

<br>

탐지된 사건과 관측 특징을 이용해
관련 장애 사례와 Runbook을 검색하는 모듈입니다.

```text
Anomaly Event
+
Observed Features
↓
Case / Runbook Retrieval
↓
related_cases.json
```

MVP 검색 기준선으로 **TF-IDF 기반 검색을 채택했으며,
현재 구현 및 연결을 진행하고 있습니다.**

첫 검색 결과를 확인한 뒤
필요하면 다른 검색 방식과 비교합니다.

Agent로 전달할 검색 결과에는 단순 문서 ID뿐 아니라
다음 정보를 포함하는 방향으로 설계합니다.

```text
Document ID
Title
Source
Relevant Evidence
```

검색 결과는 원인 후보 생성의 근거이며,
검색 결과 자체가 정답 원인을 의미하지 않습니다.

</details>

<details>
<summary><b>05 | Agent / Backend</b></summary>

<br>

Agent·Backend는 다음 정보를 연결하는 역할을 담당합니다.

```text
Anomaly Event
+
Observed Metrics
+
Related Cases / Runbooks
↓
Evidence-based Cause Analysis
```

분석 결과에는 다음 정보를 포함하는 방향으로 설계하고 있습니다.

```text
사건 식별 정보
원인 후보
근거 문서 ID
불확실성
추가 확인 항목
판단 보류 여부
```

근거가 충분하지 않은 경우
원인을 임의로 확정하지 않고 판단을 보류하도록 구성합니다.

### Local Agent Draft

현재 로컬 연결 초안은
임시 사건과 가상 검색 결과를 입력으로 받아 다음 흐름을 수행합니다.

```text
입력 검증
→ 규칙 기반 원인 후보 생성
→ 근거 문서 ID 확인
→ 판단 보류 처리
→ analysis.json 저장
```

현재 초안에서 사용하는 주요 필드는 다음과 같습니다.

```text
experiment_id
event_id
analysis_status
cause_candidates
  └─ evidence_document_ids
judgment_deferred
additional_checks
```

현재 초안은 `experiment_id`와 `event_id`를 사건 식별에 사용합니다.

다만 세부 필드와 저장 방식은
**Agent·Backend 연결을 위한 초안이며 팀 전체의 최종 합의 규격은 아닙니다.**

실제 Detection 및 Retrieval 출력과 대조한 뒤
최종 Schema를 확정할 예정입니다.

또한 이 초안은 현재 다음과 연결된 결과가 아닙니다.

```text
실제 AI 이상탐지 결과
실제 TF-IDF 검색 결과
실제 LLM 호출
실제 UI·보고서
```

</details>

<details>
<summary><b>06 | Ground Truth Separation</b></summary>

<br>

장애 실험 과정에서 알고 있는 실제 장애 정보는
평가용 Ground Truth로 별도 관리합니다.

예를 들면 다음과 같습니다.

```text
실제 장애 종류
발생 시작 시점
종료 시점
장애 조건
실제 원인
```

이 정보가 모델이나 Agent 입력에 포함되면
시스템이 정답을 미리 알고 분석하는 문제가 발생할 수 있습니다.

따라서 다음과 같이 분리하는 것을 원칙으로 합니다.

```text
System Input
→ 요청 로그 / 집계 특징 / 탐지 결과 / 검색 결과

Evaluation Ground Truth
→ 실제 장애 종류 / 발생 시점 / 실제 원인
```

현재는 **정답 누출 방지를 위한 평가 데이터·분석 입력 분리 원칙과
Interface를 설계한 단계**이며,
전체 End-to-End Pipeline에서의 누출 방지 검증은 아직 완료되지 않았습니다.

</details>

---

## Current Scope and Limitations

### Current Status

**Work in Progress**

현재 팀 단위로 다음 흐름을 구현·검증하고 있습니다.

```text
웹서비스 장애 실험
→ 요청 로그 및 Window 집계
→ 이상탐지
→ 사례·Runbook 검색
→ Agent·Backend
→ UI·보고서
```

첫 정상 A/B 실험과 규칙 기반 탐지 비교를 중심으로
각 모듈의 입력·출력을 연결하는 단계입니다.

현재 공개 GitHub 저장소에는
Agent·Backend 실행 코드가 아직 포함되어 있지 않습니다.

로컬 연결 초안은 AI 코딩 도구를 활용해 작성·수정·실행된 기록이 있으며,
김수진의 직접 실행·수정·설명 확인 범위는 별도로 검증해 기록할 예정입니다.

UI·보고서는 현재 확인된 범위에서
**예시 데이터 기반 목업·계획 단계**입니다.

실제 모듈 출력과 연결된 동작 화면 및
저장·조회 기능은 아직 확인되지 않았습니다.

### Current Scope

- 웹서비스 요청 로그 기반 장애 실험
- 정상 데이터 A/B 비교 실험
- 10초 Window 기반 초기 집계 설계
- `request_count`, `error_rate`, `mean_ms`, `p95_ms` 기반 초기 특징
- 규칙 기반 이상탐지 비교 기준선
- TF-IDF 기반 사례·Runbook 검색 기준선 채택
- Detection → Retrieval → Agent 간 JSON Interface 설계
- Ground Truth와 실제 분석 입력 분리 원칙
- 근거 문서 ID·출처·불확실성을 포함한 Agent 출력 설계
- Agent·Backend 로컬 연결 초안
- 사건 식별자 기준 JSON 파일 저장 방식 설계 — 로컬 초안은 `experiment_id`와 `event_id` 사용, 최종 저장 규격은 팀 조율 중

### Limitations

- 전체 End-to-End Pipeline은 아직 완료되지 않았습니다.
- 최종 이상탐지 알고리즘과 모델은 확정되지 않았습니다.
- 정상 A/B 실험의 전체 반복 검증과 최종 평가는 완료되지 않았습니다.
- TF-IDF 검색은 기준선으로 채택했으며 구현·연결을 진행 중입니다.
- 현재 Agent 연결 초안은 임시 Event와 가상 Retrieval 결과를 사용합니다.
- 실제 AI 탐지 결과와 실제 Retrieval 결과의 Agent 연결은 진행 중입니다.
- LLM 기반 최종 분석은 아직 연결되지 않았습니다.
- UI는 목업·계획 단계이며 실제 동작 화면은 확인되지 않았습니다.
- 모델·Agent의 최종 성능 수치는 아직 확정하지 않았습니다.
- 운영 환경에서의 장애 진단 성능은 검증하지 않았습니다.
- 과거 AI 도구 실행 기록의 테스트 결과를 현재 공개 저장소의 재검증 결과로 사용하지 않습니다.

### Next Steps

```text
팀 공통 데이터·JSON Interface 확정
→ 정상 A/B 및 장애 실험 데이터 검증
→ Detection 출력 events.json 연결
→ TF-IDF Retrieval 구현 및 related_cases.json 연결
→ 기존 Agent 연결 초안을 실제 Detection·Retrieval 출력에 맞게 수정
→ 근거·불확실성·판단 보류 처리 검증
→ 사건 식별자 기준 JSON 저장 연결
→ UI / Report 연결
→ End-to-End Test
→ 실패 사례 분석
→ 최종 평가 및 논문형 보고서 정리
```

---

## What This Project Demonstrates

- 여러 모듈로 구성된 AI 서비스의 전체 Pipeline을 정의하고 조율한 경험
- 팀원 간 모듈 연결을 위한 Input / Output Interface를 설계한 경험
- 정답 누출 방지를 위한 평가 데이터·분석 입력 분리 원칙과 Interface를 설계한 경험
- 정상 데이터 A/B를 이용한 비교 실험 방향을 설계·조율한 경험
- 이상탐지 결과와 원인 분석의 책임을 구분한 경험
- 사례·Runbook 검색 결과를 Agent의 분석 근거로 연결하는 구조를 설계한 경험
- 근거 문서 ID·출처·불확실성을 원인 후보와 함께 관리하는 구조를 설계한 경험
- 근거 부족 시 판단을 보류하도록 Agent 출력 정책을 설계한 경험
- 팀장으로서 MVP 범위, 실험 방향, 모듈 Interface와 발표 내용을 조율한 경험
- 구현 완료 범위와 진행 중인 범위를 구분하여 관리한 경험

---

## Contact

- Developer: 김수진
- Role: Team Lead / Agent·Backend
- GitHub: https://github.com/lightleaping
- Email: workingskyroad@gmail.com
