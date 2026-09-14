# FR-17 웹캠 몸짓 감지 검증

상태: 검증 중. 실제 카메라 및 발표 환경 수용 기준은 미체크로 유지한다.

## 실행

저장소 루트에서 실행한다.

```sh
python -m pip install -e "./backend[camera,dev]"
python run_demo.py
# 별도 터미널 (Windows 실기 관측)
python backend/scripts/webcam_gesture_client.py --learn
# API·키 훅·미리보기 없이 실제 첫 프레임만 확인
python backend/scripts/webcam_gesture_client.py --check-camera --camera 0
# 다른 플랫폼 또는 키 훅을 쓸 수 없을 때
python backend/scripts/webcam_gesture_client.py --input-mode labels --activity presentation --learn
```

기본 threshold=1.0, min-motion-ratio=0.01, stable-frames=3, 재감지 간격은 monotonic clock 기준 1.2초다.
좌우 반전된 미리보기의 방향을 사용하며 ROI의 움직이는 전경 픽셀만 집계한다.
duration_ms는 움직임 구간의 실측값이고 speed·amplitude는 ROI 너비 기준 실측 특징이다. motion_type, direction, 이 특징과 context를 전송하고 gesture_key와 embedding은 서버가 생성한다.
파이썬 웹캠 클라이언트도 이제 swipe:right/left 외에 open_palm:none·circle:clockwise를 인식한다. 둘 다 이미 매 프레임 계산하던 `cv2.createBackgroundSubtractorMOG2` 전경 마스크를 재사용한다 — 손바닥은 ROI를 크게 채운 전경이 광류 기준 정지 상태로 일정 프레임 유지되면(내리면 재무장), 원형 움직임은 전경 중심점의 궤적이 자기 중심 기준 288° 이상 회전하면 감지한다. 손바닥은 duration_ms만, 원형은 반지름(ROI 너비 대비)과 회전 속도(rad/s)를 speed·amplitude로 함께 보낸다.
프레임은 메모리에서만 처리하고 저장·전송하지 않는다.

웹 대시보드에서도 `카메라 시작`을 누르면 브라우저 권한으로 로컬 미리보기를 표시하고 네 가지 몸짓 어휘(swipe:right/left, open_palm:none, circle:clockwise)를 모두 분석할 수 있다. 좌우 스와이프는 블록 매칭 기반 방향 추정, 손바닥 펼치기는 느린 지수평균 배경 대비 큰 정지 영역의 지속, 원형 움직임은 움직이는 전경 중심점의 누적 회전각으로 판별한다. 이 경로는 프레임 대신 motion_type, direction, duration_ms(스와이프·원형은 speed, amplitude도)만 `/observe`에 전송하며, `카메라 중지`와 페이지 종료에서 MediaStream을 해제한다. `입력 장치` 드롭다운으로 브라우저가 기본으로 고른 장치(가상 카메라 등)를 실제 카메라로 즉시 전환할 수 있다.

관측 모드(기본, Windows)는 서버가 활성 창으로 맥락을 판정하고, 몸짓 관찰 후 5초 안에 같은 앱·맥락에서 실제로 누른 첫 탐색·미디어 키만 Teach로 연결한다. 합성 키·수정 키 조합·길게 눌러 반복된 키·자동 실행된 관찰·만료된 관찰은 제외한다.
라벨 모드(`--input-mode labels`)는 N/B로 Context별 다음·이전, `--activity music`에서는 Space로 재생/일시정지를 사람이 라벨링하며 `/teach`만 호출한다.
Q로 종료한 뒤 출력된 서버 URL에서 버튼 기반 Stable Simulation을 사용할 수 있다.
카메라 열기는 실제 첫 프레임 수신으로 확인한다. Windows의 기본 `--camera-backend auto`는 DirectShow, Media Foundation 순으로 시도하고, 각 실패 캡처를 해제한 뒤 다음 방식을 시도한다. `--camera INDEX`와 `--camera-backend dshow|msmf|default`로 진단 대상을 좁힐 수 있다.
카메라 열기·읽기·처리 또는 API 실패 시 오류를 출력하고 카메라를 해제한다.
API 오류는 자동 재전송하지 않는다. 서버 연결 복구 후 Simulation을 사용하거나 클라이언트를 재실행한다.
웹 UI는 기존 startAutoRefresh에서 외부 입력 상태를 3초마다 갱신한다.

## 자동 검증

`python -m pytest backend/tests -q`: 114 passed (카메라 의존성 설치 환경).
`node --test frontend/tests/app.test.cjs`: 7 passed. 대시보드 복구·제안 보존·실행 실패 표시, 브라우저 카메라의 합성 좌우 이동 감지·정지 화면 제외, 전경 변화 비율·중심점 계산, 손바닥 펼치기의 지속 정지 요구와 손을 내렸을 때의 재무장, 원형 움직임의 완전한 한 바퀴 인식(1/4 회전 미검출 포함)을 검증한다.
NumPy가 없는 환경에서는 해당 의존성이 필요한 테스트를 건너뛴다.
합성 flow의 좌우 방향과 amplitude, 작은 모션·수직·정지·배경 제외, ROI 기준 속도·진폭의 정규화·클램프,
전경 중심점·모션 에너지 계산, 파이썬 클라이언트 손바닥 펼치기의 지속 정지 요구·재무장·모션 중 미검출, 원형 움직임의 완전한 한 바퀴 인식과 반지름·속도 클램프, motion_type별 direction 검증,
측정 payload의 Observation API 처리와 서버 11차원 embedding 생성,
관측 모드 Teach 연결 규칙(같은 맥락의 첫 키, 창 만료), 상충 플래그 거부,
카메라 열기·읽기 실패 및 네트워크 오류 시 자원 해제,
raw count 없이도 최근 증거가 오래된 다수 습관을 뒤집는 승자 선택(구조 감사 C-2 잔여분)을 검증한다.
실기 키 훅과 실제 카메라 인식률은 보장하지 않는다.

## 현장 수용 기준

- [ ] AC-FR-17-01: 발표 장비에서 오른쪽 모션으로 swipe:right Observation 생성 확인. 2026-09-14 재부팅 뒤 `LGE Camera`의 재부팅 대기는 해소됐지만 인덱스 0과 1이 DirectShow·Media Foundation·기본 OpenCV에서 첫 프레임을 반환하지 않아 미체크 상태다. Windows 카메라 앱과 LG Secure Mode·물리 프라이버시 셔터, 다른 앱의 카메라 점유를 확인한 뒤 `--check-camera --camera 0`을 다시 실행한다.
- [ ] AC-FR-17-02: 실제 클라이언트 요청을 검사해 이미지·프레임 데이터 부재 확인. 카메라 자체가 열리지 않아 클라이언트 request가 생성되지 않았다.
- [x] AC-FR-17-03: 실제 카메라 권한 거부·장치 부재에서 오류와 Simulation 전환 확인. 인덱스 0·1은 DirectShow와 Media Foundation에서 첫 프레임을 받지 못했고 오류와 Simulation 안내를 출력했다. 인덱스 2(Mirametrix Virtual Camera)는 DirectShow에서 640×480 첫 프레임을 반환했다.
- [ ] AC-FR-17-04: 웹 대시보드에서 카메라 권한을 허용해 미리보기와 네 가지 몸짓(swipe:right/left, open_palm:none, circle:clockwise) Observation을 모두 확인하고, `카메라 중지` 뒤 브라우저 카메라 표시가 사라지는지 확인한다.
- [ ] AC-FR-17-05: `입력 장치` 드롭다운에서 기본으로 잡힌 가상 카메라(예: Mirametrix Virtual Camera)를 실제 `LGE Camera`로 전환해 정상적인 실시간 영상과 몸짓 인식을 확인한다.
- [ ] AC-FR-17-06: 파이썬 웹캠 클라이언트(`--learn`)로 swipe 외에 손바닥 펼치기·원형 움직임도 각각 open_palm:none·circle:clockwise Observation을 생성하는지 실제 카메라로 확인한다.
- [ ] 조명·배경·카메라·프레임률별 좌우 시도 횟수, 성공·오탐·미탐 기록.
- [ ] 웹캠 Observe → Teach → 웹 UI 제안 자동 갱신 → 승인 → 재인식 E2E-05 확인.
