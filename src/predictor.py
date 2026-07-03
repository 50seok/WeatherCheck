from src.dl.predict import load_models, predict_tomorrow


def get_prediction() -> dict:
    """Track A(LSTM, MAE 2.41°C — ML 대비 최고 성능) 실제 예측. contract.md 스키마 반환."""
    return predict_tomorrow(load_models())


if __name__ == "__main__":
    pred = get_prediction()
    assert pred["source"] == "lstm"
    assert 0 <= pred["rain_prob"] <= 1
    assert pred["temp_max"] >= pred["temp_min"]
    print(pred)
