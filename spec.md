# SPEC — SilentOrchestra 2.0

반복 행동과 맥락에서 `user + gesture_key + context_scope → intent`를 학습하는 로컬 우선 Agent입니다. 흐름은 `Observation → Pattern → Suggestion → Memory → Execution → Feedback`입니다. 이 문서가 구현 규범이며 충돌 시 우선합니다.

## 범위

- 활동: `presentation`, `music`
- UI/웹캠 몸짓: `swipe:right`, `swipe:left`, `open_palm:none`, `circle:clockwise`
- 선택 기능: 데모 초기화(FR-16), OpenCV 웹캠(FR-17)
- 제외: 공간 자동 인식, IoT, 얼굴·생체 인식, 영상 업로드, 자유 형식 LLM Intent, 인증·결제·동기화, 연속 문법
- Intent는 [action_catalog.py](backend/src/silent_orchestra/services/action_catalog.py)의 맥락별 카탈로그로 제한합니다.

## 입력·개인정보 (FR-01, 03, 14, 17)

- P-1: 원본 프레임을 저장·전송하지 않으며 `frame_stored=0`을 DB CHECK로 강제합니다.
- P-2: API는 미정의 필드를 거부하고 이미지 필드를 제공하지 않습니다.
- P-3: 저장 데이터는 모션·방향·시간·속도·진폭 embedding, 맥락, 행동입니다. 얼굴 특징·궤적·키 문자열은 저장하지 않습니다.
- P-4: 카메라 프레임은 메모리에서만 처리합니다.

## 맥락·학습 (FR-02, 04, 05, 07)

- L-1~2: `/teach`는 관찰과 허용된 사용자 행동을 1:1로 연결합니다. 중복·금지 행동은 400입니다.
- L-3: 같은 사용자·몸짓·활동의 최근 30일, 최대 20건을 `0.5^(경과일/반감기)`로 가중해 승자를 정합니다. count는 원시 건수, target은 최빈값(동률은 최신), embedding은 승자 관찰 평균입니다.
- L-4: `confidence = min(0.99, (0.35 + 0.10×min(승자횟수,5) + 0.22×승자횟수/전체횟수) × recency_factor)`. 기본 반감기는 10일입니다.
- L-5~6: 1·2위 가중합이 상대 오차 1e-6 이내이거나 승자가 바뀌면 기존 기억을 강등합니다. 승자 3회 이상·비동률·비활성일 때만 패턴당 `PENDING` 제안 하나를 만듭니다.
- L-7: `(user_id, gesture_key, context_scope, intent)`는 유일합니다.
- L-8: activity가 없으면 active app 또는 로컬 활성 창으로 판정합니다. 미지원·모호한 앱은 거부하며 명시 activity는 시뮬레이션 override입니다. space·device는 추론하지 않는 스냅샷입니다.
- L-9: Windows 관측 모드는 몸짓 후 5초 안의 같은 앱 첫 허용 키만 연결합니다. 합성·반복·만료 입력은 제외합니다.
- L-10: `open_palm:none`은 승인/정답, `circle:clockwise`는 거절/오답 확인 몸짓이며 학습 후보가 아닙니다.

## 승인·기억 (FR-08, 09)

- M-1: 승인 전 자동 실행하지 않습니다. `ACTIVE + auto_execute=true`만 실행 후보입니다.
- M-2~3: `PENDING`만 1회 응답할 수 있습니다. 수정 Intent는 필수·허용·비중복이어야 합니다.
- M-4: 승인 시 임계 confidence를 보장하고 같은 몸짓·맥락의 다른 활성 기억을 강등합니다.
- M-5: 거절 시 confidence를 0.20 낮추며, 같은 Intent는 새 증거 3건 전까지 재제안하지 않습니다.
- M-6: `/memories`는 임계값 이상의 활성 기억만 반환합니다.

## 추론·실행 (FR-06, 10, 11)

- I-1~3: 같은 사용자·맥락의 활성 기억을 `confidence × (0.20×키 일치 + 0.80×max(코사인 유사도,0))`로 평가합니다. 유사도 0.85 미만, 상위 다른 Intent 점수 차 0.08 미만, 최종 점수 0.60 미만이면 실행하지 않습니다. 6차원 시뮬레이션과 11차원 실측 embedding은 서로 매칭하지 않습니다.
- I-3a: 볼륨·줌 Intent만 `1 + min(int(amplitude),4)`회 실행합니다. 나머지는 1회입니다.
- I-4~7: 모든 실행은 실제 반복 횟수와 `SIMULATED`·`SUCCEEDED`·`FAILED` 결과를 기록합니다. 기본은 `DRY_RUN`; OS 실행은 명시적으로 켜며 활성 창 불일치·미매핑·전송 실패를 `FAILED`로 기록합니다.

## 피드백 (FR-12, 13)

- F-1: 실행당 피드백은 한 건입니다.
- F-2: confidence 변화는 `CORRECT +0.03`, `WRONG_ACTION -0.15`, `IGNORE -0.05`이며 0~0.99로 제한합니다. `ACCIDENTAL_GESTURE`는 confidence를 바꾸지 않고 같은 맥락에서 유사도 0.95 이상인 모션을 5분간 억제합니다.
- F-3~4: 잘못된 행동은 허용된 Intent로 교정할 수 있습니다. confidence가 임계값 아래면 기억을 강등합니다.

## 데모·UI (FR-15, 16)

- D-1~3: `/demo/reset`은 demo-user만 단일 트랜잭션으로 초기화하고 Context·Observation·Action·Pattern·Suggestion·Execution·Feedback 삭제 건수를 반환합니다. 다른 사용자는 보존하고 실패는 롤백하며 데모 모드가 아니면 403입니다.
- U-1: 카메라는 사용자가 시작하고 중지·페이지 종료 시 해제합니다.
- U-2~3: UI는 학습된 기억과 confidence를 우선 표시하고 실행 실패 사유를 구분합니다.

## 완료 기준

- 개인정보, 승인 전 실행 금지, 활성 창 차단, 맥락 분기, 초기화·재학습 계약 통과
- 백엔드·프런트·SQL 검증 통과
- 핵심 데모 90초, 발표 3분 이내

테이블·제약은 [ERD](docs/erd.md)와 [schema.sql](backend/sql/schema.sql), API 스키마는 실행 서버의 `/docs`가 소유합니다.
