# 작업 핸드오프

## 목표

SilentOrchestra 2.0의 기획, DB, FastAPI 백엔드, 웹 데모, 테스트, 발표 자료를 하나의 실행 가능한 해커톤 패키지로 구성.

## 입력과 가정

- 입력: 사용자 제공 SilentOrchestra 2.0 마크다운 기획
- DB: 별도 지정이 없어 로컬 SQLite
- 학습 임계값: 기획의 데모 시나리오를 따라 3회
- 실제 OS 입력: 안전을 위해 기본 비활성
- 웹캠: Optical Flow 선택 기능

## 생성·수정한 파일

- `docs/`: 기획서, 아키텍처, ERD, API, 데모, Q&A
- `sql/`: DDL, 시드, 대표 쿼리, 테스트, 검증 보고서
- `src/silent_orchestra/`: FastAPI 백엔드와 웹 UI
- `scripts/webcam_gesture_client.py`: 실시간 모션 입력
- `tests/`: 핵심 학습 루프 테스트
- `presentation/`: PPTX 생성 소스 및 발표 자료

## 실행 방법

```bash
python -m pip install -r requirements.txt
python run_demo.py
```

## 검증 결과

- Pytest 8개 통과
- SQLite 38개 statement 통과
- 브라우저 UI는 정적 렌더·동작 시나리오 검증 예정/완료 보고서 참조
- PPTX·DOCX는 렌더링 후 시각 검수 보고서 참조

## 남은 위험 또는 차단 요인

- 실제 웹캠 인식 품질은 카메라·조명·배경에 따라 달라짐
- 실제 OS 키 입력은 운영체제 접근성 권한 필요
- 개인별 제스처 유사도는 MVP의 단순 embedding이므로 장기 데이터에서 고도화 필요
- 인증·다중 사용자 동기화는 미구현

## 다음 담당 역할과 첫 행동

프론트엔드/데모 담당: `start_demo.bat` 실행 후 데모 대본대로 Presentation 학습 루프를 리허설.
