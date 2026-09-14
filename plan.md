# PLAN — SilentOrchestra 2.0

## 구현 방향

- 루트의 `backend/`에 Python 패키지·테스트·SQL·스크립트를, `frontend/`에 HTML·CSS·JS를 둔다. FastAPI가 프론트 정적 파일을 제공하며 별도 빌드 도구는 사용하지 않는다. 공통 문서·`.env`·`data/`와 실행 진입점 `run_demo.py`는 루트에 유지한다.

- FastAPI(도메인 엔드포인트 8개 + demo/health), 단일 페이지 워크벤치, 로컬 SQLite를 사용한다. 구조·코드 지도는 [architecture](docs/architecture.md), 설정은 [config.py](backend/src/silent_orchestra/config.py)(`SO_DATABASE_URL` 기본 로컬 SQLite, `SO_ALLOWED_ORIGINS` 기본 로컬 2개).
- 기본 시연은 버튼 기반 Stable Simulation + DRY_RUN. 기능 추가보다 정합성·검증을 우선한다.
- 웹캠 실기 경로는 활성 앱으로 맥락을 판정하고, Windows에서는 실제 앱 조작을 관측한다. `--learn`으로 추론을 끄고 재학습할 수 있다. 라벨 Simulation과 실기 관측을 UI·CLI·발표에서 구분한다. swipe 외에 open_palm(정지한 전경 지속)·circle(전경 중심점 누적 회전각)도 이미 계산 중인 MOG2 전경 마스크로 감지하며, 웹 UI와 같은 네 가지 몸짓 어휘를 공유한다.
- 웹캠 시작은 실제 첫 프레임 수신으로 검증한다. Windows에서는 DirectShow와 Media Foundation을 순서대로 시도하고, 실패한 캡처는 해제한 뒤 다음 방식으로 전환한다. 장치 번호·캡처 방식 수동 선택과 API·키 훅 없이 실행하는 카메라 점검을 지원한다. 장치 오류와 API 오류를 분리하며 프레임은 저장하지 않는다.
- 웹 UI는 사용자가 시작한 브라우저 카메라 미리보기와 로컬 모션 분석을 지원한다. 권한을 얻은 뒤 실제 비디오 입력 장치를 선택할 수 있으며, 프레임은 `<video>`와 메모리 캔버스에서만 처리하고 API에는 기존 계약의 motion_type·direction·duration_ms·speed·amplitude만 보낸다. swipe·원형 움직임은 로컬 궤적에서, 손바닥 펼치기는 지수평균 배경 대비 정지한 큰 전경 영역의 지속으로 감지하고(speed·amplitude는 swipe·원형에만 동반 — 원형은 반지름·회전속도로 개인차를 반영, 손바닥은 정적 동작이라 미동반), 중지·페이지 종료 시 MediaStream 트랙을 해제한다.
- 모션 구간의 시작과 끝에서 실측 시간·ROI 기준 속도·진폭을 산출한다. 서버는 실측 embedding을 만들고 최근 승자 관찰의 평균을 기억한다. DB 컬럼 추가 없이 기존 JSON embedding과 feedback/suggestion 시각을 활용한다.
- 학습 창은 30일·20건으로 제한하고, 승자 변경·거절 후 새 증거·감지 오류 억제를 회귀 테스트한다. 승자 선택 자체가 `recency_half_life_days` 가중합이라(SPEC L-3), raw count가 더 많아도 오래된 습관이 최근 새 습관에게 밀릴 수 있다 — 증거 총량(observation_count)·threshold 게이트는 raw count 그대로다. 유사도 점수는 SPEC I-2를 따르며 같은 키라도 개인 모션이 다르면 실행을 보류한다.
- 의도적 단순화: [app.js](frontend/app.js)는 SSE 대신 3초 폴링, 실행 오버레이 자동 닫힘 없음; [action_executor.py](backend/src/silent_orchestra/services/action_executor.py)는 활성 창 이름 부분 문자열 매칭·리눅스 활성 창 미지원; [models.py](backend/src/silent_orchestra/models.py)의 `Annotated` 컬럼 별칭은 유지한다.

## 단계별 계획

1. 발표자가 [대본](docs/demo-script.md)을 소리 내어 읽으며 타이밍을 측정한다. UI 조작 외 내레이션은 사람의 리허설로 검증한다.
2. 선택 경로를 시연할 때만 [운영 가이드](docs/operations.md)에 따라 발표 PC의 OS 실행을 확인하거나 웹캠 인식 품질을 확인한다.
3. 조건을 충족할 때만 확장한다.

| 확장 | 착수 조건 / 로드맵 |
|---|---|
| 동적 학습 임계값 | 실사용 로그로 오작동 비용 측정 가능 |
| 학습형 embedding·유사도 | 개인 편차에서 단순 코사인 오분류 발생 / V1 |
| browser·kitchen 등 맥락 추가 | 두 맥락 데모 검증 후, SPEC의 카탈로그·CHECK 변경 준수 / V2 |
| LLM Intent, 인증·다중 사용자 | 규칙 카탈로그로 요구 표현 불가, 또는 demo-user 단일 사용자 전제 변경 / V3 |
| SSE·WebSocket | 사용자·탭 증가로 3초 폴링 부족 |
| PostgreSQL | 단일 PC 데모 범위 초과 |
| 오버레이 자동 닫힘 | 데모에서 상시 사용으로 전환 |
| 활성 창 판정 고도화 | 앱 이름 중복 오탐 또는 리눅스 OS 실행 필요 |

## 검증 전략

- [test_api.py](backend/tests/test_api.py)의 프레임 거부, 학습→승인→실행, 맥락 분기, 비활성 창 차단, 초기화→재학습 테스트로 [완료 기준](spec.md#완료-기준)을 확인한다.
- [README 테스트](README.md#테스트)의 명령으로 [CI](.github/workflows/ci.yml)와 같은 검증을 수행하고, 결과는 TASKS에 기록한다.

- 초기화 후 [발표 대본](docs/demo-script.md)의 조작·내레이션을 리허설한다.

## 리스크 및 미결정

- 웹캠 품질은 조명·배경·프레임률에 좌우된다. 기본 시뮬레이션 경로를 유지한다.
- OS 실행은 발표 PC의 권한·활성 창 확인 지원에 좌우된다. 환경별 제약과 대응은 [운영 가이드](docs/operations.md#권한과-활성-창-확인)에서 관리한다.
- 실측 embedding은 고정 특징 인코더이며 신경망 학습·신원 인식이 아니다. 좌우 swipe 어휘, 초기 반복 비용, 승인·피드백 조작은 남는다. 개인차 분류 성능과 실제 키 훅은 하드웨어 검증이 필요하다.
