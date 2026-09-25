# PLAN — SilentOrchestra 2.0

## 구조

- `backend/`: FastAPI, SQLAlchemy 모델, 서비스, 테스트, SQL, 웹캠 스크립트
- `frontend/`: 빌드 없는 단일 페이지 HTML/CSS/JS
- 루트: 로컬 실행 진입점, Vercel 진입점, 설정, 데이터, 공통 문서
- 기본 데모: 버튼 시뮬레이션 + `DRY_RUN`
- 선택 경로: 브라우저 카메라, Windows OpenCV 관측, PyAutoGUI OS 실행

학습은 최근 30일·20건의 사용자 행동을 사용합니다. 웹캠은 `swipe:right/left`, `open_palm:none`, `circle:clockwise`를 감지하고 활성 앱으로 활동을 판정합니다. 프레임은 메모리에서만 처리하며 서버에는 모션 특징만 보냅니다. 상세 규칙은 [SPEC](spec.md), 흐름은 [아키텍처](docs/architecture.md)가 소유합니다.

## 검증

1. [README 테스트](README.md#테스트)를 실행합니다.
2. 선택 기능은 [운영 가이드](docs/operations.md)와 [FR-17 검증](docs/fr-17-validation.md)에 따라 실제 장비에서 확인합니다.
3. [데모 대본](docs/demo-script.md)을 3분 안에 리허설합니다.

## 제약

- 맥락은 발표·음악 두 개, 기억은 몸짓·맥락당 활성 Intent 한 개입니다.
- 고정 특징과 코사인 유사도를 사용하며 신경망·신원 인식은 없습니다.
- Linux 활성 창 확인은 지원하지 않습니다.
- 웹캠 품질과 실제 키 훅은 장비별 검증이 필요합니다.
- SSE, 추가 맥락, 학습형 임베딩, 인증·동기화는 현재 범위 밖입니다.
