"""self-check: predict_tomorrow이 docs/contract.md 스키마를 지키는지 확인.
실행: python tests/test_predict.py (project root에서)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ml.predict import predict_tomorrow, train_all


def demo():
    models = train_all()
    result = predict_tomorrow(models, temp_avg=15.0, temp_max=20.0, temp_min=10.0,
                               humidity=60, pressure=1013.0, wind_speed=2.5, precip_yesterday=0.0)

    assert set(result.keys()) == {"date", "temp_max", "temp_min", "rain_prob", "source"}
    assert isinstance(result["temp_max"], float) and isinstance(result["temp_min"], float)
    assert result["temp_max"] > result["temp_min"], "최고기온은 최저기온보다 커야 함"
    assert 0.0 <= result["rain_prob"] <= 1.0
    assert result["source"] in {"linearregression", "randomforest", "xgboost"}
    print("OK:", result)


if __name__ == "__main__":
    demo()
