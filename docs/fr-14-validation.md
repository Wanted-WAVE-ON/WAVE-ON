# FR-14 영상·개인정보

상태: 자동 검증 완료, 실제 카메라 네트워크 캡처 미완료.

## 확인됨

- API의 미정의 영상 필드 거부
- `frame_stored=0` DB CHECK와 이미지/BLOB 컬럼 부재
- 프레임 저장·업로드·얼굴 인식 코드 부재
- 모션 특징만 포함한 Observation 계약

근거: `schemas.py`, `models.py`, `schema.sql`, `webcam_gesture_client.py`, `test_api.py`.

## 남은 검증

- [ ] 실제 카메라 실행 중 네트워크 요청을 캡처해 raw frame 전송 0건 확인

정책 API나 UI 문구는 네트워크 측정의 대체 근거로 사용하지 않습니다.
