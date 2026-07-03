from src.dl.predict import load_models, predict_tomorrow
from src.ml.predict import load_data


def get_prediction() -> dict:
    """Track A(LSTM, MAE 2.41°C — ML 대비 최고 성능) 내일 예측. contract.md 스키마 반환."""
    return predict_tomorrow(load_models())


def get_today_observed() -> dict:
    """오늘(가장 최근 실측 데이터) — 예측이 아니라 관측값. LSTM은 1일 뒤(내일)만 예측 가능해서 별도 제공."""
    row = load_data().sort_values("date").iloc[-1]
    return {
        "date": str(row["date"])[:10],
        "temp_max": round(float(row["temp_max"]), 1),
        "temp_min": round(float(row["temp_min"]), 1),
        "rain_prob": 1.0 if row["precip"] > 0 else 0.0,
        "source": "observed",
    }


if __name__ == "__main__":
    pred = get_prediction()
    assert pred["source"] == "lstm"
    assert 0 <= pred["rain_prob"] <= 1
    assert pred["temp_max"] >= pred["temp_min"]
    print(pred)
