# Figma 구현 핸드오프

현재 Figma 파일이 제공되지 않아 실제 캔버스 수정 대신 구현 가능한 화면 명세를 작성합니다.

## 페이지 및 프레임

### `01 / Main Agent`

- Desktop: 1440 × 1024
- 3열 구조: Context 260 / Agent fluid / Memory 330
- 상단 76px 글로벌 헤더
- 중앙에 영상 대신 추상 Agent Orb
- 카메라 영상을 노출하지 않아 privacy 철학 강조

### `02 / Suggestion State`

- 오른쪽 `Agent Suggestion` 카드 활성
- 제목: “이 몸짓을 ‘다음 슬라이드’로 기억할까요?”
- 근거: 반복 횟수와 현재 Context
- 행동: `기억하기`, `아니요`

### `03 / Execution State`

- 전체 화면 반투명 오버레이
- 큰 Gesture symbol
- Intent label
- confidence
- `맞아요`, `아니에요`

### `04 / My Language`

- Command 설정 목록이 아니라 AI가 배운 사용자 모델을 보여주는 화면
- Gesture, Context, Intent, confidence, observation count

### `05 / Privacy`

- Camera → Motion Features → Frame Discarded
- Raw storage OFF
- Face recognition OFF
- Cloud upload OFF
- Local processing ON

## 컴포넌트

- `Context/Switch`
- `Agent/Orb` variants: idle, listening, success, error
- `Gesture/InputButton` variants: default, hover, active, disabled
- `Learning/Progress`
- `Suggestion/Card` variants: pending, accepted, rejected
- `Memory/Row`
- `Execution/Overlay`
- `Feedback/Buttons`
- `Toast`

## 접근성

- 텍스트 대비 WCAG AA 수준 목표
- 색상 외에 상태 텍스트와 아이콘 병행
- 클릭 영역 최소 40px
- 키보드 focus visible
- 애니메이션은 정보 이해를 방해하지 않게 300ms 내외
- 카메라 상태와 저장 여부를 항상 텍스트로 제공

## 개발 기준

실제 구현은 `src/silent_orchestra/static/`에 있으며, Figma 작성 시 해당 화면을 기준으로 재현할 수 있습니다.
