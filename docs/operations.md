# 운영 가이드

기본 데모는 버튼 시뮬레이션과 `DRY_RUN`입니다. 선택 기능만 아래 절차를 사용합니다.

## 웹캠

```bash
python -m pip install -e "./backend[camera]"
python run_demo.py
# 별도 터미널: Windows 실제 키 관측 + 학습
python backend/scripts/webcam_gesture_client.py --learn
# 카메라 첫 프레임만 점검
python backend/scripts/webcam_gesture_client.py --check-camera --camera 0
```

기본값은 `--input-mode observe --activity auto`입니다. 활성 앱으로 활동을 판정하고 몸짓 후 5초 안의 같은 앱 첫 허용 키를 `/teach`에 연결합니다. 합성·수정키 조합·반복·만료 입력은 제외하며 원래 키 입력은 차단하지 않습니다.

| 앱 | 관측 키 | 행동 |
|---|---|---|
| PowerPoint Slide Show | Right, PageDown, N, Space | 다음 슬라이드 |
| PowerPoint Slide Show | Left, PageUp, P | 이전 슬라이드 |
| PowerPoint Slide Show | Escape | 발표 종료 |
| Spotify, VLC, iTunes, Music | Media Next/Previous/PlayPause | 트랙·재생 제어 |

지원하지 않거나 모호한 앱은 거부합니다. PowerPoint 편집 화면과 음악 앱의 일반 Space는 관측하지 않습니다.

카메라는 `swipe:right/left`, `open_palm:none`, `circle:clockwise`를 감지합니다. 프레임은 저장·전송하지 않습니다. 장치·백엔드는 `--camera INDEX`, `--camera-backend dshow|msmf|default`로 좁혀 진단합니다.

Windows 관측을 쓸 수 없으면 명시적 라벨 모드를 사용합니다.

```bash
python backend/scripts/webcam_gesture_client.py --input-mode labels --activity presentation --learn
```

N/B는 다음·이전, music의 Space는 재생·일시정지 라벨입니다. 실제 앱 조작을 관측하거나 수행하지 않습니다. 조정값과 현장 기준은 [FR-17 검증](fr-17-validation.md)에 있습니다.

## OS 실행

```bash
python -m pip install pyautogui
export SO_ENABLE_OS_ACTIONS=true      # PowerShell: $env:SO_ENABLE_OS_ACTIONS = "true"
python run_demo.py
```

설정은 서버 시작 시 읽습니다. `SO_REQUIRE_ACTIVE_WINDOW=true`가 기본이며 대상 앱이 활성 창이 아니거나 확인할 수 없으면 실행을 차단합니다.

- macOS: 접근성 권한 필요
- Windows: 활성 창 제목으로 판정
- Linux: 활성 창 확인 미지원, `DRY_RUN` 권장

`SIMULATED`는 DRY_RUN, `SUCCEEDED`는 키 전송 완료, `FAILED`는 활성 창·키 매핑·권한·전송 오류입니다. 현장에서 복구하지 못하면 OS 실행을 끄고 서버를 재시작합니다.
