# SilentOrchestra 2.0

사용자가 정해진 제스처를 외우는 대신, AI가 반복되는 몸짓과 현재 맥락을 관찰해 개인의 몸짓 언어를 학습하는 로컬 우선 Spatial AI Agent 데모입니다.

## 핵심 흐름

```text
Observation -> Pattern -> Suggestion -> Memory -> Execution -> Feedback
```

1. 사용자가 자연스러운 몸짓을 합니다.
2. 시스템은 원본 영상을 저장하지 않고 모션 특징과 현재 맥락만 기록합니다.
3. 몸짓 직후 사용자가 실제로 수행한 행동을 연결합니다.
4. 같은 맥락에서 같은 패턴이 3회 반복되면 Agent가 기억 여부를 제안합니다.
5. 사용자가 승인한 뒤에만 Personal Gesture Memory가 활성화됩니다.
6. 이후 같은 몸짓이 발생하면 맥락에 맞는 의도를 추론하고 동작을 실행합니다.
7. 맞음/아님 피드백으로 confidence를 갱신합니다.

같은 `swipe:right`도 맥락에 따라 다르게 학습됩니다.

```text
Presentation + swipe:right -> NEXT_SLIDE
Music        + swipe:right -> NEXT_TRACK
```

## 빠른 실행

### Windows

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python run_demo.py
```

또는:

```powershell
start_demo.bat
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python run_demo.py
```

브라우저에서 `http://127.0.0.1:8000`을 엽니다. API 문서는 `http://127.0.0.1:8000/docs`에서 확인할 수 있습니다.

## 90초 데모

1. `Presentation` 맥락을 확인합니다.
2. `오른쪽 손짓`을 누릅니다.
3. 후속 행동으로 `다음 슬라이드`를 선택합니다.
4. 같은 과정을 총 3회 반복합니다.
5. 오른쪽 제안 카드에서 `기억하기`를 누릅니다.
6. 다시 `오른쪽 손짓`을 누르면 `다음 슬라이드`가 자동 실행됩니다.
7. `Music`으로 전환한 뒤 같은 과정을 `다음 트랙`으로 반복해 맥락 분기를 보여줍니다.

기본값은 `DRY_RUN`이므로 실제 키 입력 대신 안전한 실행 결과만 표시합니다.

## 선택 기능: 실시간 웹캠 모션 감지

OpenCV Optical Flow 기반 클라이언트를 포함합니다. 원본 프레임은 저장하지 않습니다.

```bash
python -m pip install -r requirements-camera.txt
python scripts/webcam_gesture_client.py --activity presentation
```

키보드 보조 입력:

- `N`: 다음 행동 연결
- `B`: 이전 행동 연결
- `Space`: 재생/일시정지 연결
- `Q`: 종료

발표 현장에서는 하드웨어 변수 때문에 버튼 기반 Stable Simulation 경로를 권장합니다.

## 실제 OS 동작 실행

기본값은 안전한 시뮬레이션입니다. 실제 PowerPoint/미디어 키 입력을 보내려면 별도로 `pyautogui`를 설치하고 `.env`에서 다음 값을 설정합니다.

```env
SO_ENABLE_OS_ACTIONS=true
```

```bash
python -m pip install pyautogui
```

운영체제 접근성 권한이 필요할 수 있습니다.

## 검증

```bash
python -m pytest -q
python scripts/validate_sqlite.py --schema sql/schema.sql --seed sql/seed.sql --queries sql/queries.sql --tests sql/tests.sql --report sql/validation-report.json
```

현재 검증 상태:

- Pytest: 5개 테스트 통과
- SQLite: 38개 statement 검증 통과
- 원본 프레임 저장 0건 조건 통과
- 동일 제스처의 Presentation/Music 맥락 분기 통과

## API 요약

| Method | Endpoint | 역할 |
|---|---|---|
| `GET` | `/health` | 서버 상태 확인 |
| `POST` | `/api/v1/demo/bootstrap` | 데모 사용자 준비 |
| `POST` | `/api/v1/demo/reset` | 데모 데이터 초기화 |
| `POST` | `/api/v1/observe` | Context와 Gesture 관찰 및 Intent 추론 |
| `POST` | `/api/v1/teach` | 몸짓 직후 사용자 행동 연결 및 패턴 갱신 |
| `GET` | `/api/v1/suggestions` | Agent 제안 조회 |
| `POST` | `/api/v1/suggestions/{id}/respond` | 제안 승인/거절/수정 |
| `GET` | `/api/v1/memories` | 활성 Personal Gesture Memory 조회 |
| `POST` | `/api/v1/executions/{id}/feedback` | 실행 피드백 반영 |
| `GET` | `/api/v1/dashboard` | UI 통합 상태 조회 |
| `GET` | `/api/v1/demo/privacy` | Privacy 상태 조회 |

상세 계약은 [docs/api.md](docs/api.md)를 확인하세요.

## 프로젝트 구조

```text
silent-orchestra-2/
├─ docs/                     기획, 아키텍처, API, 데모, Q&A
├─ design/                   사용자 흐름, Figma 핸드오프, 디자인 토큰
├─ sql/                      schema, seed, queries, tests, 검증 보고서
├─ src/silent_orchestra/     FastAPI 백엔드와 웹 UI
├─ scripts/                  SQLite 검증, 웹캠 모션 클라이언트
├─ tests/                    핵심 학습 루프 API 테스트
├─ reports/                  검증 결과와 UI 미리보기
├─ presentation/             PPTX 생성 스크립트
├─ run_demo.py
├─ start_demo.bat
└─ requirements.txt
```

## 개인정보 보호 원칙

- 원본 카메라 영상 저장 금지
- 얼굴 인식 미사용
- 클라우드 영상 업로드 미사용
- 모션 특징 벡터와 맥락만 로컬 저장
- 자동 실행은 사용자 승인 이후에만 활성화
- 실행과 피드백은 감사 로그로 추적
