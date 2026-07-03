# ponytail: mock source, swap the return value for Track A's real predict() call at integration (docs/contract.md schema stays the same)
def get_mock_prediction() -> dict:
    return {
        "date": "2026-07-04",
        "temp_max": 25.3,
        "temp_min": 13.1,
        "rain_prob": 0.9,
        "source": "mock",
    }


if __name__ == "__main__":
    pred = get_mock_prediction()
    assert pred["source"] == "mock"
    assert 0 <= pred["rain_prob"] <= 1
    assert pred["temp_max"] >= pred["temp_min"]
    print(pred)
