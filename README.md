# 사례 기반 웹서비스 이상탐지·분석 Agent

**Web Service Incident Analysis · Anomaly Detection · Case/Runbook Retrieval · Agent Backend**

> **Status: Work in Progress**  
> **Team Project · Team Lead / Agent·Backend**
>
> 웹서비스 요청 로그에서 이상 사건을 탐지하고, 관련 사례와 Runbook을 검색하여
> 근거 기반 원인 후보와 사건 분석 결과를 제공하는 졸업작품 팀 프로젝트입니다.
>
> 현재 각 모듈을 구현·검증 중이며,
> **구현된 기능과 설계·진행 중인 기능을 구분하여 기록합니다.**

---

## Project Overview

웹서비스 장애가 발생했을 때 단순히

```text
"이상이다"
```

라고 탐지하는 것에서 끝나는 것이 아니라,

```text
어떤 변화가 발생했는가
→ 어떤 장애 사례와 관련 있는가
→ 가능한 원인 후보는 무엇인가
→ 어떤 근거로 그렇게 판단했는가
```

까지 연결하는 분석 흐름을 목표로 합니다.

전체 방향은 다음과 같습니다.

```text
Request Logs
↓
Anomaly Detection
↓
Case / Runbook Retrieval
↓
Evidence-based Cause Analysis
↓
Incident Report
```

---

## Project Goals

이 프로젝트에서 해결하려는 핵심 문제는 다음과 같습니다.

1. 정상 상태와 장애 상태의 요청 로그를 구분해 수집
2. 서로 다른 장애 상황을 재현하고 정답 정보를 별도로 관리
3. 요청 로그를 일정 시간 구간으로 집계
4. 정상 패턴과 다른 구간을 이상 사건으로 탐지
5. 이상 사건과 관련된 과거 사례·Runbook 검색
6. 탐지 결과와 검색 근거를 이용해 원인 후보 생성
7. 원인 후보와 근거를 구조화된 형태로 전달
8. 최종적으로 사건 분석 결과를 UI·보고서로 연결

---

## System Flow

현재 팀에서 맞추고 있는 전체 데이터 흐름입니다.

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
UI / Incident Report
```

모듈별 결과를 JSON 형태로 연결해
각 담당자가 독립적으로 개발하더라도 전체 Pipeline을 조립할 수 있도록 구성하고 있습니다.

---

## Data Flow

### 1. Request Logs

웹서비스 요청 단위의 로그를 수집합니다.

예상되는 정보:

```text
timestamp
endpoint
status_code
latency
```

원본 요청 로그와 별도로 일정 시간 Window 기준 집계 데이터를 생성합니다.

초기 실험에서는 다음과 같은 집계 지표를 사용하고 있습니다.

```text
request_count
error_rate
mean_ms
p95_ms
```

---

### 2. Anomaly Detection

집계된 요청 로그를 이용해
정상 상태와 다른 패턴을 탐지합니다.

현재 첫 실험에서는 동일한 탐지 방식에 대해
서로 다른 정상 패턴을 별도로 학습·비교하는 방향을 우선 검토하고 있습니다.

```text
Normal Pattern A
→ Detector A

Normal Pattern B
→ Detector B
```

규칙 기반 탐지 결과를 비교 기준선으로 함께 사용합니다.

> 최종 이상탐지 알고리즘과 모델은 아직 확정되지 않았습니다.

---

### 3. Case / Runbook Retrieval

탐지된 사건의 특징을 입력으로 받아
관련 장애 사례와 Runbook을 검색하는 모듈입니다.

```text
Anomaly Event
+
Observed Features
↓
Case / Runbook Retrieval
↓
Related Cases + Evidence
```

검색 결과는 Agent가 원인 후보를 생성할 때 사용할
**근거 데이터**로 전달하는 것을 목표로 합니다.

---

### 4. Agent / Backend

Agent·Backend 영역에서는 다음 정보를 입력으로 받는 구조를 설계하고 있습니다.

```text
Anomaly Event
+
Observed Metrics
+
Related Cases / Runbooks
```

이를 바탕으로 다음 정보를 구조화합니다.

```text
원인 후보
근거
관련 사례
불확실성
추가 확인 항목
```

핵심 원칙은 다음과 같습니다.

```text
Anomaly Score ≠ Root Cause
```

이상탐지 결과 자체를 장애 원인으로 단정하지 않고,
검색된 사례와 실제 관측 데이터를 근거로
**확인 가능한 원인 후보**를 제시하도록 구성합니다.

근거가 부족한 경우에는 원인을 확정하지 않는 방향을 사용합니다.

---

## Planned Agent Output

Agent·Backend 출력은 `analysis.json` 형태의
구조화된 데이터로 연결하는 것을 목표로 합니다.

예시 구조:

```json
{
  "incident_id": "incident-001",
  "summary": "오류율과 응답 시간이 함께 증가한 이상 구간",
  "cause_candidates": [
    {
      "cause": "candidate cause",
      "evidence": [
        "observed metric",
        "related case"
      ]
    }
  ],
  "uncertainty": "추가 확인 필요",
  "recommended_checks": [
    "관련 로그 확인"
  ]
}
```

> 위 JSON은 현재 모듈 간 Interface를 설명하기 위한 예시이며,
> 최종 Schema는 구현 과정에서 변경될 수 있습니다.

---

## Ground Truth Separation

실험에서는 **평가용 정답과 시스템 입력을 분리**합니다.

예를 들어 장애를 직접 발생시킬 때 기록하는:

```text
실제 장애 종류
발생 시작 시점
종료 시점
장애 강도
실제 원인
```

등은 평가를 위한 Ground Truth로 관리합니다.

이 정보가 모델이나 Agent 입력에 그대로 포함되면
정답을 이미 알고 분석하는 문제가 생기므로,
실제 분석 입력과 분리하는 것을 원칙으로 합니다.

---

## Evaluation Direction

### Anomaly Detection

검토할 항목:

```text
정상 구간 오탐
장애 구간 탐지 여부
탐지 지연
장애 종류별 탐지 결과
정상 패턴 A/B에 따른 차이
```

### Retrieval

검토할 항목:

```text
관련 사례 검색 여부
관련 Runbook 검색 여부
검색 결과와 실제 장애의 관련성
```

### Agent Analysis

검토할 항목:

```text
원인 후보에 근거가 포함되는가
관측 데이터와 모순되지 않는가
검색되지 않은 정보를 임의로 단정하지 않는가
근거 부족 시 불확실성을 표시하는가
```

### End-to-End

최종적으로 다음 흐름이 연결되는지 확인합니다.

```text
Log
→ Detection
→ Retrieval
→ Agent
→ UI / Report
```

---

## Team Structure

프로젝트는 모듈별 담당을 나누되
앞 단계의 출력이 다음 단계의 입력이 되도록 Interface를 맞추는 방식으로 진행하고 있습니다.

```text
Request Log / Experiment
        ↓
Anomaly Detection
        ↓
Case / Runbook Retrieval
        ↓
Agent / Backend
        ↓
UI / Report
```

### My Role

**Team Lead / Agent·Backend**

담당 범위:

- 프로젝트 주제와 MVP 범위 정리
- 전체 Pipeline 흐름 조율
- 모듈 간 Input / Output 규격 조율
- Ground Truth와 분석 입력 분리 원칙 정리
- 정상 A/B 비교 실험 방향 조율
- 이상탐지 결과와 Agent 원인 후보의 역할 구분
- Evidence와 Source를 포함한 Agent 출력 구조 설계
- 근거 부족 및 불확실성 표현 방식 설계
- Agent·Backend 구현
- 발표자료와 전체 프로젝트 설명 통합

현재 Agent·Backend 영역은 구현·검증 중입니다.

---

## Current Status

**Work in Progress**

### Team Progress

현재 팀 단위로 다음 영역을 순차적으로 구현·검증하고 있습니다.

```text
웹서비스 장애 실험
→ 요청 로그 수집
→ Window 집계
→ 이상탐지
→ 사례 / Runbook 검색
→ Agent 분석
→ UI / 보고서
```

### My Area

현재 공개 저장소에는
Agent·Backend의 최종 실행 코드와 End-to-End 결과가 아직 포함되어 있지 않습니다.

로컬에서 작성한 초안 역시
직접 실행·수정·설명 검증을 마친 범위부터 공개할 예정입니다.

따라서 현재 상태를 다음과 같이 구분합니다.

```text
Project / Interface Design     → 진행
Team Integration               → 진행 중
Agent / Backend Implementation → 진행 중
End-to-End Validation          → 미완료
Final Evaluation               → 미완료
```

---

## Current Limitations

- 전체 End-to-End Pipeline이 아직 완성되지 않았습니다.
- 최종 이상탐지 알고리즘과 모델이 확정되지 않았습니다.
- Retrieval 모듈의 최종 구현과 평가가 완료되지 않았습니다.
- Agent·Backend 최종 구현과 테스트가 완료되지 않았습니다.
- UI는 최종 시스템과 연결된 상태가 아닙니다.
- 모델·Agent 성능 수치는 아직 확정하지 않았습니다.
- 실제 운영 웹서비스 장애 진단 성능을 의미하지 않습니다.

완료되지 않은 기능을 구현된 것으로 표시하지 않습니다.

---

## Next Steps

```text
1. 팀 공통 데이터와 JSON Interface 확정
2. 정상 A/B 및 장애 실험 데이터 검증
3. Detection 출력 events.json 연결
4. Retrieval 출력 related_cases.json 연결
5. Agent / Backend analysis.json 구현
6. Evidence / Uncertainty 처리 검증
7. UI / Report 연결
8. End-to-End Test
9. 실패 사례 분석
10. 최종 평가 및 논문형 보고서 정리
```

---

## Repository Policy

이 저장소는 졸업작품 개발 기록과
취업 포트폴리오를 함께 관리하기 위한 공개 저장소입니다.

- 직접 확인한 구현과 결과만 완료 상태로 기록합니다.
- 팀원의 코드와 결과물은 공개 동의를 받은 범위만 포함합니다.
- 담당자와 구현 범위를 구분합니다.
- Mock Data와 실제 실험 결과를 구분합니다.
- API Key, 개인 정보, 비공개 원본 자료는 포함하지 않습니다.
- 계획과 실제 구현 결과를 구분합니다.

---

## Tech Direction

현재 프로젝트에서 검토·사용 중인 기술 영역입니다.

```text
Python
Pandas
Anomaly Detection
Case / Runbook Retrieval
LLM / Agent
Backend API
Structured JSON
Evidence-based Analysis
```

기술 목록은 프로젝트 진행 단계에 따라 변경될 수 있으며,
실제 구현·검증된 범위는 Current Status에서 별도로 구분합니다.

---

## Project Summary

```text
Request Logs
↓
Anomaly Detection
↓
Case / Runbook Retrieval
↓
Evidence-based Cause Analysis
↓
Incident Report
```

단순 이상탐지 모델 하나를 만드는 것이 아니라,
**탐지 → 사례 검색 → 근거 기반 분석 → 서비스 출력**까지 연결하는 것을 목표로 합니다.

현재는 팀 프로젝트의 각 모듈을 구현·검증하면서
전체 시스템으로 연결하는 단계입니다.
