# SilentOrchestra 2.0 프로젝트 브리프

## 한 줄 정의

정해진 제스처를 인식하는 시스템이 아니라, 사용자의 행동 패턴과 상황을 관찰해 개인의 몸짓 언어를 스스로 학습하는 로컬 우선 Spatial AI Agent.

## 1. 문제 정의

기존 제스처 제어 서비스는 시스템이 미리 정한 동작을 사용자가 외우고 정확히 재현해야 합니다. 이 방식은 사용자의 자연스러운 습관을 반영하지 못하고, 같은 몸짓이 발표·음악·브라우저 등 상황에 따라 다른 의미를 가질 수 있다는 점을 처리하기 어렵습니다.

## 2. 대상 사용자

- 발표 중 키보드나 리모컨에서 손을 떼고 자연스럽게 화면을 제어하려는 사용자
- 음악 감상 중 같은 몸짓을 개인 습관대로 사용하고 싶은 사용자
- 고정된 제스처 명령 체계보다 학습되는 개인화 인터페이스가 필요한 사용자
- 카메라 기반 서비스에서 영상 저장과 얼굴 인식에 민감한 사용자

## 3. 핵심 가치

1. **No gesture manual**: 사용자가 정해진 제스처를 외우지 않음
2. **Context reasoning**: 동일 몸짓도 현재 활동에 따라 다른 의도로 해석
3. **Human approval first**: 반복 패턴을 발견해도 승인 전에는 자동 실행하지 않음
4. **Personal Gesture Memory**: AI가 현재 사용자에 대해 배운 몸짓 언어를 가시화
5. **Privacy by design**: 원본 프레임은 폐기하고 모션 특징만 로컬 저장

## 4. 핵심 사용자 흐름

```text
몸짓 관찰
→ 현재 앱·활동 맥락 저장
→ 직후 사용자 행동 연결
→ 3회 반복 패턴 발견
→ Agent가 기억 여부 제안
→ 사용자 승인
→ Personal Gesture Memory 활성화
→ 다음 몸짓에서 Intent 추론·자동 실행
→ 사용자 피드백
→ Memory confidence 업데이트
```

## 5. MVP 범위

- Context: `presentation`, `music`
- Motion pattern: swipe right, swipe left, open palm, circle
- 후속 행동 연결
- 3회 반복 시 Agent 제안
- 승인/거절
- 개인 제스처 기억 조회
- 동일 제스처의 상황별 Intent 분기
- 안전한 DRY_RUN 자동 실행
- 맞음/틀림 피드백과 confidence 갱신
- 선택적 OpenCV Optical Flow 웹캠 입력

## 6. 제외 범위

- 공간 위치 자동 인식
- 얼굴·사용자 생체 인식
- 클라우드 영상 저장
- IoT 실기기 연동
- LLM 기반 자유 형식 명령 생성
- 인증·결제·운영자 대시보드
- 완전한 수어 인식

## 7. 해커톤 성공 지표

다음은 제공 문서에 없던 **구현 검증용 목표값**입니다.

| 지표 | 목표 |
|---|---:|
| 반복 학습 기준 | 동일 맥락·동작·후속 행동 3회 |
| 승인 전 자동 실행 | 0회 |
| 원본 프레임 저장 | 0건 |
| Context 분기 정확성 | 데모 시나리오 100% |
| 핵심 API 테스트 | 모두 통과 |
| 전체 데모 완료 | 90초 이내 |

## 8. 차별점

```text
기존 Gesture Control
Gesture → Classifier → Command

SilentOrchestra 2.0
Observation → Context + History → Candidate Intent
→ Confidence → Suggestion/Execution → Feedback → Memory Update
```

## 9. 기술 선택

- Backend: FastAPI
- Database: SQLite + SQLAlchemy
- Frontend: Vanilla HTML/CSS/JavaScript
- Optional perception: OpenCV Optical Flow
- Testing: Pytest + FastAPI TestClient
- Privacy: local-first, raw frame discard

## 10. 핵심 데모 메시지

> 사용자가 AI를 설정하는 것이 아니라, AI가 사용자의 자연스러운 몸짓 언어를 배운다.
