# FR-17 웹캠 검증

상태: 자동 검증 완료, 실제 장비 검증 중.

## 구현

Python·브라우저 카메라는 `swipe:right/left`, `open_palm:none`, `circle:clockwise`를 로컬 분석합니다. 프레임 대신 motion type, direction, duration과 선택적 speed/amplitude만 `/observe`에 보냅니다. Windows 관측 모드는 활성 앱과 5초 안의 첫 허용 키를 연결합니다.

실행·진단 명령은 [운영 가이드](operations.md#웹캠)에 있습니다.

## 자동 검증

- Python: 방향·특징·payload·맥락·키 연결·카메라/API 실패 시 자원 해제
- Frontend: 좌우 이동, 정지 제외, 손바닥 재무장, 완전한 원형 궤적, Dashboard 회귀
- SQL/API: 특징 저장 계약과 개인정보 제약

## 현장 수용 기준

- [ ] 실제 카메라에서 네 가지 몸짓 Observation 생성
- [ ] 브라우저 장치 선택과 중지 시 MediaStream 해제
- [ ] 요청 캡처에서 이미지·프레임 데이터 0건
- [ ] Windows 실제 키 관측 → 제안 → 승인 → 재인식 E2E
- [ ] 발표 환경의 성공·오탐·미탐 기록

현재 LGE Camera는 첫 프레임을 반환하지 않았고 Mirametrix Virtual Camera만 DirectShow에서 640×480 프레임을 반환했습니다. LG Secure Mode·프라이버시 셔터·다른 앱 점유를 확인한 뒤 재검증합니다.
