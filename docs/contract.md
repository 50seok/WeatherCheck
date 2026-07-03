# 트랙 간 인터페이스 (단일 진실)

Track A(ML/DL 예측) → Track B(RAG 브리핑) 전달 형식. Track B는 통합 전까지 이 스키마의 mock을 사용한다.

## 예측 결과 JSON

```json
{
  "date": "2026-07-04",
  "temp_max": 25.3,
  "temp_min": 13.1,
  "rain_prob": 0.9,
  "source": "lstm"
}
```

| 필드 | 타입 | 설명 |
|---|---|---|
| `date` | str (YYYY-MM-DD) | 예측 대상 날짜 |
| `temp_max` / `temp_min` | float | 최고/최저 기온(°C) — 일교차 = max−min |
| `rain_prob` | float 0~1 | 강수 확률 |
| `source` | str | `xgboost` \| `lstm` \| `mock` |

## 규칙
- 필드 **추가**는 자유, 기존 필드 **변경·삭제**는 양 트랙 확인 후 이 문서부터 갱신
- Track A는 예측 함수가 이 dict를 반환하도록 구현 (`src/` 내 위치 자유)
- Track B의 mock도 `source: "mock"`으로 이 스키마 그대로

## 파일 소유권 (병합 충돌 방지)
- **`app.py`는 Track A 전용.** Track B는 이 파일을 직접 수정하지 않는다 — Phase3 대시보드가 필요하면 별도 파일(`app_briefing.py` 등)로 만들거나, 7/5 통합 시점에 Track A 완성본에 이어붙인다.
- 그 외 `src/ml/`, `src/dl/`, `notebooks/`(Track A) vs `src/rag/`, `knowledge/`, `src/bot/`(Track B)는 폴더가 갈려 있어 자유롭게 작업.
