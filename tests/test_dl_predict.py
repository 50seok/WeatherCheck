"""self-check: LSTM predict_tomorrow이 docs/contract.md 스키마를 지키는지 확인.
실행: python tests/test_dl_predict.py (project root에서, src/dl/train.py로 모델 학습 후)
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dl.predict import load_models, predict_tomorrow


def demo():
    models = load_models()
    result = predict_tomorrow(models)

    assert set(result.keys()) == {"date", "temp_max", "temp_min", "rain_prob", "source"}
    assert isinstance(result["temp_max"], float) and isinstance(result["temp_min"], float)
    assert result["temp_max"] > result["temp_min"], "최고기온은 최저기온보다 커야 함"
    assert 0.0 <= result["rain_prob"] <= 1.0
    assert result["source"] == "lstm"
    print("OK:", result)


if __name__ == "__main__":
    demo()
