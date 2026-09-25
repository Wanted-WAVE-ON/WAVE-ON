# FR-16 데모 초기화

상태: 구현·자동 검증 완료.

`POST /api/v1/demo/reset`은 demo-user의 Context, Observation, Action, Pattern, Suggestion, Execution, Feedback을 단일 트랜잭션으로 삭제하고 사용자를 재생성합니다. 삭제 건수를 반환하며 다른 사용자를 보존합니다. 실패는 롤백하고 `SO_DEMO_MODE=false`이면 403입니다.

검증 항목:

- [x] 7개 종속 테이블 삭제와 삭제 건수
- [x] 다른 사용자 보존
- [x] 재생성·commit 실패 롤백
- [x] 초기화 후 3회 학습과 재제안
- [x] UI Reset 후 초기 상태 복구

근거: `demo_service.py`, `routers/demo.py`, `test_api.py`.
