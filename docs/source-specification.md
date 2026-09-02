좋아. 이 방향이면 핵심을 **“Gesture Recognition 앱”이 아니라 “개인 행동 언어를 학습하는 Spatial Agent”**로 잡고, DB도 단순 `gesture → command` 매핑이 아니라 **관찰 → 패턴 → 제안 → 승인 → 기억 → 실행 → 피드백**을 저장할 수 있어야 해.

## 1. 전체 서비스 구조

나는 이렇게 잡는 걸 추천해.

```text
┌───────────────────────────────────────────────┐
│              SilentOrchestra 2.0              │
│           Personalized Spatial Agent          │
└───────────────────────────────────────────────┘

 Camera
   │
   ▼
[Motion Feature Extractor]
 Optical Flow / Hand Landmark
   │
   │ 원본 Frame 즉시 폐기
   ▼
[Gesture Encoder]
 "오른쪽 휘두름"을 feature vector로 변환
   │
   ▼
[Observation Engine]
 ├─ 어떤 gesture?
 ├─ 현재 어떤 앱?
 ├─ 어떤 공간?
 ├─ 직후 사용자가 뭘 했나?
 └─ 이전 행동과 비슷한가?
   │
   ▼
[Pattern Learning]
 Gesture + Context + Subsequent Action
   │
   │ 반복 패턴 발견
   ▼
[Agent Reasoning]
 "이 제스처가 Next Slide를 의미하는 것 같다"
   │
   ▼
[Suggestion]
 "이 동작을 다음 슬라이드로 기억할까요?"
   │
   ├── 승인 → Memory
   └── 거절 → Negative Feedback
              │
              ▼
         [Gesture Memory]
              │
        다음 동작 발생
              ▼
     Gesture + Context + History
              │
              ▼
          Intent 추론
              │
              ▼
        [Action Executor]
      PPT / Music / IoT / Timer
```

**Agent가 들어가는 부분은** **`Gesture → Action`** **사이**야.

기존:

```text
Gesture → Classifier → Command
```

2.0:

```text
Observation
    ↓
Gesture + Context + History
    ↓
Candidate Intent 검색
    ↓
Confidence 판단
    ↓
┌────────────────────┐
높음              애매함
↓                    ↓
자동 실행          사용자에게 질문
↓                    ↓
Feedback           승인/수정
└──────── Memory 업데이트
```

이 구조여야 “Agent”라는 설명도 훨씬 설득력이 있어.

---

# 2. DB는 이렇게

핵심 테이블은 **7개 정도**면 충분해.

### `users`

```sql
users
-----
id
name
created_at
```

### `gesture_observations`

AI가 관찰한 **원시 행동 기록**.

```sql
gesture_observations
--------------------
id
user_id

gesture_embedding
motion_type
direction
duration_ms

context_id

detected_at
```

여기서 중요한 게:

**원본 카메라 이미지는 저장하지 않는 것.**

예:

```text
motion_type: swipe
direction: right
duration: 430ms
embedding: [0.21, -0.31, ...]
```

정도만 저장.

---

### `contexts`

몸짓이 발생했을 때 상황.

```sql
contexts
--------
id
user_id

active_app
activity
space
device
timestamp
```

예를 들면:

```json
{
  "active_app": "PowerPoint",
  "activity": "presentation",
  "space": "meeting_room",
  "device": "laptop"
}
```

MVP에서는 공간까지 자동 인식하려고 욕심낼 필요 없어.

처음에는:

```text
active_app
presentation / music / browser
```

정도만 해도 충분해.

---

### `actions`

몸짓 직후 실제 사용자가 수행한 행동.

```sql
actions
-------
id
user_id
observation_id

action_type
target
parameters

executed_by
executed_at
```

예:

```text
gesture
↓
3초 이내 사용자가 →
Keyboard ArrowRight

action_type = NEXT
target = powerpoint
executed_by = USER
```

이 데이터가 엄청 중요해.

AI가

> “저 몸짓의 의미가 다음 슬라이드인가?”

를 학습할 근거니까.

---

# 3. 핵심은 `gesture_patterns`

여기가 SilentOrchestra의 **개인 Gesture Memory**야.

```sql
gesture_patterns
----------------
id
user_id

gesture_embedding

intent
context_scope

confidence
observation_count

auto_execute

created_at
updated_at
```

예를 들어 나영이가:

```text
오른쪽으로 손 휘두르기
```

를 자주 한다고 해보자.

DB에는:

```text
User: N

Gesture:
right_swipe_embedding

Context:
presentation

Intent:
NEXT

Confidence:
0.94

Observation Count:
12

Auto Execute:
true
```

가 들어감.

그런데 같은 동작을 음악에서는:

```text
Context:
music

Intent:
NEXT_TRACK
```

으로 기억할 수 있어.

즉 DB상에서도:

```text
Gesture ≠ Command

Gesture
 + Context
 + User
 = Intent
```

구조를 유지하는 게 중요해.

---

# 4. Agent 제안 DB도 따로 두자

### `agent_suggestions`

```sql
agent_suggestions
-----------------
id
user_id

gesture_pattern_id

suggested_intent
reason
confidence

status
created_at
responded_at
```

status:

```text
PENDING
ACCEPTED
REJECTED
MODIFIED
```

예:

```text
suggested_intent:
NEXT_SLIDE

reason:
최근 PowerPoint 사용 중 유사 동작 후
ArrowRight 입력이 4회 관찰됨

confidence:
0.87
```

이게 UI에서:

> 새로운 행동 패턴을 발견했어요.
> 이 동작 후 다음 슬라이드로 이동하는 행동이 4번 반복됐어요.
> **이 몸짓을 '다음 슬라이드'로 기억할까요?**

가 되는 거야.

이게 데모에서 **제일 중요한 화면**이라고 봐.

---

# 5. Feedback 테이블

```sql
feedback
--------
id
user_id
gesture_pattern_id
execution_id

feedback_type
corrected_intent

created_at
```

예:

```text
CORRECT
WRONG_ACTION
ACCIDENTAL_GESTURE
IGNORE
```

AI가 볼륨을 줄였는데 사용자가:

> 아니야

하면 해당 gesture-intent 연결 confidence를 낮춰.

반대로 계속 수정하지 않으면 높여.

그래서

```text
Observation
     ↓
Pattern
     ↓
Suggestion
     ↓
User Feedback
     ↓
Memory Update
```

라는 **Agent learning loop**가 생겨.

---

# 6. 최종 DB 관계

이 정도가 깔끔해.

```text
User
 │
 ├──────────────┐
 ▼              ▼
Observation    Context
 │
 ▼
Action
 │
 ▼
Pattern
 │
 ├───────────────┐
 ▼               ▼
Suggestion     Execution
 │               │
 └──────┬────────┘
        ▼
     Feedback
        │
        ▼
   Pattern Update
```

포트폴리오/PPT에서는 이걸 **Personal Gesture Memory**라고 부르는 게 좋아.

---

# 7. 서비스는 5개 모듈로

백엔드도 너무 크게 만들 필요 없어.

```text
silent-orchestra/
│
├── perception/
│   ├── camera.py
│   ├── optical_flow.py
│   ├── hand_tracker.py
│   └── gesture_encoder.py
│
├── context/
│   ├── app_detector.py
│   ├── activity_detector.py
│   └── context_manager.py
│
├── agent/
│   ├── pattern_detector.py
│   ├── intent_reasoner.py
│   ├── suggestion_agent.py
│   └── memory.py
│
├── actions/
│   ├── powerpoint.py
│   ├── media.py
│   ├── browser.py
│   └── iot.py
│
├── api/
│   ├── gestures.py
│   ├── suggestions.py
│   ├── memories.py
│   └── feedback.py
│
└── db/
    ├── models.py
    └── repository.py
```

그리고 흐름은:

```text
Perception
    ↓
Context Engine
    ↓
Agent
    ↓
Memory
    ↓
Action Executor
```

로 보여줘.

---

# 8. UI/UX는 오히려 단순해야 함

여기서 UI를 관리자 대시보드처럼 만들면 별로야.

이 서비스의 철학 자체가:

> **사용자가 AI를 설정하는 게 아니라 AI가 사용자를 배운다.**

잖아.

그러니까 설정 페이지에

```text
S → Next Slide
O → Volume Up
V → Light On
```

이런 식으로 나오면 기존 프로젝트로 돌아가 버려.

## 메인 화면

이렇게 극단적으로 단순하게.

```text
┌────────────────────────────────────────┐
│ SilentOrchestra                        │
│                                        │
│              ◉                         │
│                                        │
│         공간을 이해하고 있어요          │
│                                        │
│      PowerPoint · Presentation         │
│                                        │
│   손짓을 자연스럽게 사용해 보세요.       │
│   별도의 제스처를 외울 필요가 없습니다.   │
│                                        │
│                     12 gestures learned│
└────────────────────────────────────────┘
```

카메라 영상 자체를 화면에 띄우지 않는 것도 좋아.

오히려 privacy 철학을 보여줄 수 있음.

---

# 9. 동작했을 때 UX

손을 오른쪽으로 휘두르면:

```text
            →→→

     다음 슬라이드

   Learned gesture · 96%
```

2초 정도 나타났다가 사라짐.

사용자가 **AI가 왜 움직였는지는 알 수 있지만 방해받지는 않는 UX**.

---

# 10. 가장 중요한 Learning UX

새로운 패턴이 발견되면 화면 오른쪽 아래에 작게:

```text
┌───────────────────────────────────┐
│ ✦ 새로운 패턴을 발견했어요          │
│                                   │
│ 이 동작 후 '다음 슬라이드'를        │
│ 4번 실행했어요.                    │
│                                   │
│ 앞으로 이 동작을 기억할까요?        │
│                                   │
│ [기억하기]        [아니요]          │
└───────────────────────────────────┘
```

이 화면 하나로 기존 Gesture Control과 차별점이 바로 보여.

---

# 11. Gesture Memory 화면

나는 이름을 그냥 **My Language**로 할 것 같아.

```text
My Gesture Language

내가 가르친 동작                     8

→  오른쪽 손짓
   Presentation
   다음 슬라이드
   ●●●●●  매우 확실함

↻  손가락 원형 움직임
   Kitchen
   Timer
   ●●●●○

↑  손바닥 올리기
   Living Room
   Light brighter
   ●●●●●
```

여기서 재밌는 포인트는 명령어 목록이 아니라:

> **“AI가 현재 나에 대해 무엇을 배웠는가?”**

를 보여주는 화면이라는 거야.

---

# 12. Context UX도 넣자

별도 Context 화면에서는:

```text
Current Context

┌──────────────────────────┐
│ Presentation             │
│                          │
│ PowerPoint               │
│ Meeting Room             │
│                          │
│ Active gestures     3    │
└──────────────────────────┘

AI interpretation

Right swipe
→ Next Slide

Pinch
→ Zoom

Open palm
→ Pause
```

그리고 Spotify를 켜면 자연스럽게:

```text
Current Context

Music
Spotify

Right swipe
→ Next Track
```

으로 바뀜.

**같은 Gesture인데 Context에 따라 Action이 바뀌는 장면**을 데모에서 반드시 보여주는 게 좋아.

---

# 13. Privacy 화면

Privacy는 별도 화면 하나를 주는 게 좋아.

```text
Privacy

Camera
   ↓
Motion Features
   ↓
Frame Discarded
   ↓
On-device AI
   ↓
Gesture Memory


✓ Raw video is not stored
✓ Face recognition is not used
✓ Motion features remain on device
```

그리고 UI에:

```text
Camera storage       OFF
Face recognition     OFF
Cloud video upload   OFF
On-device processing ON
```

이렇게 보여주면 말로 Privacy라고 하는 것보다 훨씬 강해.

---

# 14. 처음 만들 MVP 범위

여기서 **주방 + IoT + PPT + 음악 + 공간인식 + LLM Agent**를 한 번에 구현하려고 하면 프로젝트 터질 가능성이 커.

MVP는 딱 이것만 하는 걸 추천해.

1. **PowerPoint**
2. **Media Player**
3. **3\~5개 정도의 motion pattern**
4. 사용자가 실제 키보드 입력을 하면 gesture와 연관성 관찰
5. 3회 정도 반복되면 AI가 gesture 등록 제안
6. 승인하면 Gesture Memory 저장
7. 이후 자동 실행
8. PowerPoint/Media Player에 따라 동일 gesture의 의미 변경

이 정도면 충분해.

그리고 **IoT/주방은 확장 시나리오**로 보여주면 돼.

---

## 15. 데모는 이 순서가 제일 세다

심사위원 앞에서 처음부터 등록된 gesture를 보여주지 말고 **학습 과정 자체를 데모**하는 거야.

```text
① 발표 시작

사용자:
오른쪽 손 휘두름
→ 아무 일 없음
→ 키보드 → 누름

② 다시 반복

손 휘두름
→ 키보드 →

③ 다시 반복

손 휘두름
→ 키보드 →

④ Agent 등장

"반복되는 행동 패턴을 발견했어요.

발표 중 이 동작 이후
'다음 슬라이드'를 3회 실행했습니다.

이 몸짓을 기억할까요?"

              [기억하기]

⑤ 클릭

Personal Gesture Memory
✓ Learned

⑥ 다시 손을 휘두름

손 →→→

AI
"Next Slide · 94%"

→ 슬라이드 자동 이동
```

그리고 여기서 끝내지 말고 **Spotify/음악 플레이어로 Context를 변경**해.

```text
같은 →→→ 몸짓

Presentation
→ Next Slide

Music
→ Next Track
```

이 장면까지 나오면,

**Personalization + Memory + Context Reasoning + Agent + Gesture AI**

가 한 번에 설명돼.

---

### 이 프로젝트의 핵심 문장도 바꿀 수 있어

> **SilentOrchestra는 정해진 제스처를 인식하는 시스템이 아니라, 사용자의 행동 패턴과 상황을 관찰하여 개인의 몸짓 언어를 스스로 학습하는 온디바이스 Spatial AI Agent입니다.**

그리고 기술 구조를 한 줄로 잡으면:

```text
Motion
  ×
Context
  ×
Personal Memory
  ↓
Intent Reasoning
  ↓
Action
  ↓
Feedback
  ↺
```

이게 프로젝트 전체의 중심이야.

특히 **DB를** **`gesture-command mapping`** **중심으로 만들지 말고** **`Observation → Pattern → Memory → Feedback`** **중심으로 설계하는 것**이 중요해. 그래야 나중에 LLM이나 다른 Agent 모델을 붙여도 구조를 갈아엎지 않아도 돼.