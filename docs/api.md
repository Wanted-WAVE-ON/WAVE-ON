# SilentOrchestra 2.0 API 계약

Base URL: `http://127.0.0.1:8000/api/v1`

## 공통 오류

```json
{
  "detail": "오류 원인"
}
```

- `400`: 요청은 형식상 유효하지만 현재 상태에서 수행할 수 없음
- `404`: 사용자, 제안, 실행 등 대상 리소스를 찾을 수 없음
- `422`: Pydantic 입력 검증 실패

요청 스키마에 정의되지 않은 필드는 허용하지 않습니다. MVP `activity`는 `presentation`과 `music`만 지원합니다.

## 1. 데모 준비

### `POST /demo/bootstrap`

데모 사용자를 생성하거나 기존 사용자를 반환합니다.

```json
{
  "user": {"id": "demo-user", "name": "수영", "created_at": "..."},
  "suggestion_threshold": 3,
  "auto_execution_threshold": 0.60,
  "os_actions_enabled": false
}
```

### `POST /demo/reset`

데모 사용자의 관찰, 행동, 패턴, 제안, 실행, 피드백 데이터를 모두 삭제하고 초기 상태로 되돌립니다.

## 2. 몸짓 관찰 및 추론

### `POST /observe`

```json
{
  "user_id": "demo-user",
  "context": {
    "active_app": "PowerPoint",
    "activity": "presentation",
    "space": "meeting_room",
    "device": "laptop"
  },
  "gesture": {
    "motion_type": "swipe",
    "direction": "right",
    "duration_ms": 430
  },
  "attempt_inference": true
}
```

학습 전 응답 예시:

```json
{
  "inference": {
    "matched": false,
    "intent": null,
    "confidence": 0,
    "reason": "현재 상황에서 활성화된 개인 제스처 기억이 없습니다.",
    "execution": null
  }
}
```

학습 후 응답 예시:

```json
{
  "inference": {
    "matched": true,
    "intent": "NEXT_SLIDE",
    "target": "powerpoint",
    "confidence": 0.91,
    "reason": "presentation 맥락의 개인 기억과 100% 유사하여 '다음 슬라이드' 의도로 해석했습니다.",
    "execution": {
      "execution_mode": "DRY_RUN",
      "status": "SIMULATED"
    }
  }
}
```

## 3. 후속 행동 연결

### `POST /teach`

```json
{
  "user_id": "demo-user",
  "observation_id": "uuid",
  "action_type": "NEXT_SLIDE",
  "target": "powerpoint",
  "parameters": {}
}
```

응답 예시:

```json
{
  "action": {},
  "pattern": {
    "status": "CANDIDATE",
    "observation_count": 3,
    "confidence": 0.87
  },
  "suggestion": {
    "status": "PENDING",
    "reason": "presentation 상황에서 유사한 동작 후 '다음 슬라이드' 행동이 3회 관찰되었습니다."
  },
  "progress_current": 3,
  "progress_required": 3
}
```

## 4. 제안 조회와 응답

### `GET /suggestions?user_id=demo-user&status=PENDING`

대기 중인 Agent 제안을 조회합니다.

### `POST /suggestions/{suggestion_id}/respond`

승인:

```json
{"decision": "ACCEPTED"}
```

거절:

```json
{"decision": "REJECTED"}
```

수정 승인:

```json
{
  "decision": "MODIFIED",
  "modified_intent": "PREVIOUS_SLIDE"
}
```

## 5. Personal Gesture Memory

### `GET /memories?user_id=demo-user&gesture_key=swipe:right&context_scope=presentation`

`gesture_key`와 `context_scope`는 선택 필터입니다. `ACTIVE`이고 confidence가 자동 실행 기준 이상인 개인 제스처 기억만 반환합니다.

## 6. 실행 피드백

### `POST /executions/{execution_id}/feedback`

```json
{
  "user_id": "demo-user",
  "feedback_type": "WRONG_ACTION",
  "corrected_intent": "PREVIOUS_SLIDE"
}
```

피드백별 기본 confidence 변화:

| Feedback | 변화 |
|---|---:|
| `CORRECT` | +0.03 |
| `WRONG_ACTION` | -0.15 |
| `ACCIDENTAL_GESTURE` | -0.10 |
| `IGNORE` | -0.05 |

confidence가 0.60 미만이면 자동 실행을 중지하고 다시 `CANDIDATE` 상태로 전환합니다.
동일 실행에 Feedback을 다시 제출하면 `400`을 반환하며 confidence를 중복 변경하지 않습니다.

## 7. 대시보드

### `GET /dashboard?user_id=demo-user`

현재 Context와 UI에 필요한 집계, memories, candidates, pending suggestions, recent events를 한 번에 반환합니다. 아직 Observation이 없으면 `context`는 `null`입니다.

## 8. Privacy 상태

### `GET /demo/privacy`

```json
{
  "raw_video_stored": false,
  "face_recognition_used": false,
  "cloud_video_uploaded": false,
  "motion_features_stored": true,
  "processing_mode": "on-device / local-first"
}
```
