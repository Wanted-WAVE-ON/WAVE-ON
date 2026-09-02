# 데이터 안내

## 데이터 성격

SilentOrchestra 2.0 MVP는 외부 공개 데이터셋을 사용하지 않습니다. 서비스 실행 중 생성되는 개인 행동 이벤트가 학습 데이터입니다.

## 저장 데이터

- Gesture motion type
- Direction
- Duration
- 수치형 motion embedding
- Active app와 activity context
- 몸짓 직후 사용자 action
- Agent suggestion과 사용자 응답
- 실행 결과와 feedback

## 저장하지 않는 데이터

- 원본 카메라 이미지·영상
- 얼굴 이미지·얼굴 embedding
- 음성
- 위치 원시 데이터
- 클라우드 영상 URL

## 원본 보존 규칙

웹캠 프레임은 Optical Flow 계산을 위해 프로세스 메모리에만 존재하며 파일로 기록하지 않습니다. 따라서 `data/raw/`에는 영상 원본을 두지 않습니다.

## 샘플 데이터

`sql/seed.sql`의 데이터는 설명·검증 목적의 합성 데이터입니다.
