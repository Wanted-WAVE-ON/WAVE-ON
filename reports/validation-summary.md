# 검증 요약

## Pytest 및 학습 루프

```text
16 passed
```

검증 항목:

- Health/Privacy endpoint
- 3회 반복 → Suggestion → Accept → Auto execution
- 동일 `swipe:right`의 Presentation/Music Context 분기
- `WRONG_ACTION` feedback에 따른 confidence 감소
- 중복 Feedback 차단과 0.60 미만 Memory 자동 강등
- Observation의 raw frame/image 입력 거부와 `frame_stored=false`
- 지원 Context 검증과 Dashboard 현재 Context 반환
- Suggestion Intent 수정 후 승인
- 최빈 Action 동률 시 대기 제안 철회와 자동 실행 중단
- Context 밖 Intent와 중복 Memory 수정 거부
- 동일 Gesture·Context에서 활성 Memory 1개 유지
- Feedback 수정 Intent의 Context·중복 검증
- 기존 SQLite 스키마에 호환성 무결성 가드 설치
- 웹캠 키 입력의 Context별 Intent 검증

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
- 제안 Intent 수정 후 Memory 활성화: 통과
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
