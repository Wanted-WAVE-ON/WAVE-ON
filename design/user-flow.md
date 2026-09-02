# 사용자 흐름 및 상태 전이

## 1. 첫 실행

```text
Landing
→ Demo user bootstrap
→ Current Context 표시
→ Learned memory 0개
→ “몸짓을 자연스럽게 사용해 보세요”
```

## 2. 학습 전 관찰

```text
Gesture input
→ Listening state
→ Observation saved
→ Active memory search
→ No match
→ 후속 행동 선택 UI
```

## 3. 패턴 학습

```text
후속 행동 선택
→ Action linked to Observation
→ 같은 Gesture + Context 집계
→ 1/3, 2/3 진행 표시
→ 3/3에서 Suggestion card
```

## 4. 제안 응답

```text
Accept → Pattern ACTIVE + auto_execute ON → My Language 표시
Reject → Pattern REJECTED + auto_execute OFF
Modify → Intent 수정 후 ACTIVE
```

## 5. 자동 실행

```text
Gesture input
→ Context-specific memory match
→ Confidence threshold 통과
→ Action overlay
→ Feedback buttons
```

## 6. 피드백

```text
맞아요 → confidence 상승
아니에요 → confidence 하락
confidence < 0.60 → 자동 실행 중지 + CANDIDATE 복귀
```

## 7. 주요 UI 상태

- Empty memory
- Listening
- Observation ready
- Learning progress
- Suggestion pending
- Memory accepted
- Auto-execution overlay
- Correct/wrong feedback
- API error toast
- Demo reset
