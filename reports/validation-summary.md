# 검증 요약

## API 및 학습 루프

```text
5 passed
```

검증 항목:

- Health/Privacy endpoint
- 3회 반복 → Suggestion → Accept → Auto execution
- 동일 `swipe:right`의 Presentation/Music Context 분기
- `WRONG_ACTION` feedback에 따른 confidence 감소
- Observation에 raw frame/image 필드가 없고 `frame_stored=false`

## SQLite

- 상태: `passed`
- 실행 statement: `38`
- 외래키 검증: 통과
- 원본 프레임 저장 0건: 통과
- 동일 Gesture의 Context별 2개 Intent: 통과
- Execution-Feedback 연결: 통과

## 서버 스모크 테스트

- Uvicorn 애플리케이션 시작: 통과
- `GET /health`: 통과
- `GET /` 웹 UI 제공: 통과
- `POST /api/v1/demo/bootstrap`: 통과

## UI 검증

- 실제 HTML/CSS/JavaScript를 사용한 브라우저 시뮬레이션: 통과
- 3회 학습 후 제안 노출: 통과
- 제안 승인 후 자동 실행 오버레이: 통과
- 결과 이미지: `reports/ui-preview-learning.png`, `reports/ui-preview-execution.png`

## 문서·발표자료 QA

- DOCX: 18페이지 렌더링 및 전체 페이지 이미지 확인
- PPTX: 13슬라이드 렌더링 및 몽타주 확인
- PPTX 오버플로 검사: 통과
- 발표자 노트와 `[Sources]` 블록: 13슬라이드 포함

## 환경 의존 미검증

- 실제 카메라 하드웨어에서의 모션 인식률
- 실제 PowerPoint/Spotify OS 키 전달
- 다중 사용자 동시성
- 장기간 개인 데이터에서의 embedding drift
