# SilentOrchestra 2.0

몸짓 뒤의 행동을 활동별로 학습하고, 사용자가 승인한 연결만 실행하는 로컬 우선 Spatial AI Agent 데모입니다.

## 기술 스택

Python 3.11+ · FastAPI · SQLAlchemy · SQLite/PostgreSQL · Vanilla HTML/CSS/JS · 선택적 OpenCV/PyAutoGUI

## 시작하기

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
python -m pip install -e ./backend
python run_demo.py
```

브라우저에서 <http://127.0.0.1:8000>을 엽니다.

기본 DB는 로컬 SQLite입니다. 배포 환경은 `SO_DATABASE_URL`로 PostgreSQL을 지정하며 루트 `main.py`가 Vercel 진입점입니다.

## 사용 방법

- 기본: 웹 UI 버튼·라벨 시뮬레이션과 `DRY_RUN`
- 브라우저 카메라: 사용자가 시작하며 네 가지 몸짓을 로컬 분석
- Windows 웹캠: 활성 앱과 실제 후속 키 조작 관측
- 실제 OS 제어: 별도 설정 필요

웹캠·OS 실행은 [운영 가이드](docs/operations.md), 발표 순서는 [데모 대본](docs/demo-script.md), API는 실행 서버의 [/docs](http://127.0.0.1:8000/docs)를 참고합니다.

## 테스트

```bash
python -m pip install -e "./backend[dev]"
python -m pytest backend/tests -q
node --test frontend/tests/app.test.cjs
python backend/scripts/validate_sqlite.py --schema backend/sql/schema.sql --seed backend/sql/seed.sql --queries backend/sql/queries.sql --tests backend/sql/tests.sql --report /tmp/sqlite-validation.json
```

CI는 [.github/workflows/ci.yml](.github/workflows/ci.yml), 현재 상태는 [tasks.md](tasks.md)가 관리합니다.

## 관련 문서

- [요구사항](spec.md) · [구현 계획](plan.md) · [작업 상태](tasks.md)
- [아키텍처](docs/architecture.md) · [데이터 설계](docs/erd.md) · [디자인](docs/design.md)
- [제품 범위](docs/brief.md) · [결정 로그](docs/decision-log.md) · [Q&A](docs/qna.md)
- [FR-14](docs/fr-14-validation.md) · [FR-15](docs/fr-15-validation.md) · [FR-16](docs/fr-16-validation.md) · [FR-17 검증](docs/fr-17-validation.md)
