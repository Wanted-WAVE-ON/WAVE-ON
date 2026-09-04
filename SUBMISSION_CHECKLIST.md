# SilentOrchestra 2.0 제출 체크리스트

## 제출 파일

- `README.md`
- `docs/` 기획, 아키텍처, API, 데모 스크립트, Q&A
- `design/` 사용자 흐름, 디자인 토큰, Figma 핸드오프
- `sql/` schema, seed, queries, tests, validation report
- `src/silent_orchestra/` FastAPI 백엔드와 웹 UI
- `tests/` API 테스트
- `scripts/` SQLite 검증과 선택형 웹캠 클라이언트
- 전체 실행 가능한 프로젝트 폴더

## 발표 직전 실행

### Windows

```powershell
start_demo.bat
```

### macOS / Linux

```bash
./start_demo.sh
```

브라우저: `http://127.0.0.1:8000`

## 90초 데모 순서

1. `Presentation` 맥락을 확인합니다.
2. 오른쪽 손짓을 누르고 후속 행동으로 `다음 슬라이드`를 선택합니다.
3. 같은 흐름을 총 3회 반복합니다.
4. Agent 제안 카드에서 `기억하기`를 누릅니다.
5. 다시 오른쪽 손짓을 눌러 자동 `NEXT_SLIDE` 실행을 보여줍니다.
6. `Music` 맥락으로 전환합니다.
7. 같은 오른쪽 손짓을 `NEXT_TRACK`으로 학습시켜 맥락별 의도 분기를 보여줍니다.

## 안전 장치

- 실제 키 입력 대신 기본 `DRY_RUN` 유지
- 웹캠이 불안정하면 Stable Simulation 버튼 사용
- 데모 시작 전 `Reset demo` 실행
- 원본 영상, 얼굴 인식, 클라우드 영상 업로드 없음

## 검증 완료

- Pytest: 16/16 통과
- SQLite 검증: 38 statements 통과
- Uvicorn 서버 데모 smoke 테스트 통과
- 웹 UI 학습/제안/자동실행 플로우 점검
- DOCX/PPTX 산출물 render QA 완료
