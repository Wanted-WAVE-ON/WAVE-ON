# 디자인 규칙

토큰 값은 [tokens.css](../frontend/tokens.css), 교환 형식은 [design-tokens.json](../design/design-tokens.json)이 소유합니다. 이 문서는 사용 규칙만 정의합니다.

## 구조

- 데스크톱: 맥락 레일 · 중앙 작업 · 기억 레일
- 모바일: 중앙 작업을 먼저 배치
- 단일 레이어와 얇은 구분선을 사용
- 장식 구체·동심원·그라데이션·홍보 문구 금지
- Agent Orb는 상태 옆의 작은 표시로 제한

## 의미

- cyan: 주 동작, 화면의 5% 미만
- violet: 학습·제안 상태만
- error: 오류 텍스트와 상태
- 색만으로 상태를 전달하지 않음

## 타입·동작

- Display: IBM Plex Sans KR 700
- Body: Pretendard Variable 400–600
- Mono: wordmark·실시간 지표만
- 모션: 버튼 press와 상태 crossfade만, reduced motion은 opacity 120ms 이하
- 포커스 표시와 44px 이상 터치 영역 유지

## 컨트롤

- Primary: solid cyan, 구체적인 한국어 동사
- Secondary: 어두운 표면과 선
- Destructive: 채우지 않고 error 색 텍스트
- 성공 토스트는 생략하고 오류·화면 밖 비동기 결과만 고정 안내
