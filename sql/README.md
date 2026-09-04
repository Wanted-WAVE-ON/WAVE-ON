# SQLite 산출물

## 파일

- `schema.sql`: 8개 테이블, 8개 인덱스, Personal Gesture Memory view
- `seed.sql`: Presentation/Music 맥락별 동일 제스처 샘플
- `queries.sql`: Memory, Suggestion, Execution, Privacy 대표 조회
- `tests.sql`: 외래키, 테이블 수, 원본 프레임 0건, 맥락 분기 assertion
- `validation-report.json`: 메모리 DB에서 전체 실행한 결과

## 실행

```bash
python scripts/validate_sqlite.py --schema sql/schema.sql --seed sql/seed.sql --queries sql/queries.sql --tests sql/tests.sql --report sql/validation-report.json
```

현재 검증 결과: `passed`, 총 38 statements.
