"""Track B/app.py가 호출할 LSTM 예측 진입점. docs/contract.md 스키마로 반환.

ML(src/ml/predict.py)과 구조를 맞춤: load_models() -> predict_tomorrow(models, ...).
ML은 오늘 하루치 슬라이더 입력을 받지만, LSTM은 최근 SEQ_LEN일 데이터 자체의
시계열 패턴으로 예측하므로 입력값이 필요 없다(데이터 파일의 최신 날짜 기준).
"""
import datetime as dt
import os

from tensorflow import keras

from src.dl.sequences import FEATURES, SEQ_LEN, build_sequences
from src.ml.predict import load_data

MODEL_PATH = "src/dl/models/lstm_model.keras"


def load_models() -> dict:
    df = load_data()
    _, _, _, scaler = build_sequences(df)  # 학습 때와 동일 방식으로 스케일러 재현
    if not os.path.exists(MODEL_PATH):
        from src.dl.train import run as train_lstm
        train_lstm()
    try:
        model = keras.models.load_model(MODEL_PATH)
    except Exception:
        # ponytail: 배포 환경 tensorflow/keras 버전이 로컬과 달라 저장된 .keras를 못 읽을 수 있음(Keras 3 저장 포맷은 마이너 버전 간에도 깨짐).
        # 그 자리에서 지금 설치된 버전으로 재학습하면 저장/로드가 같은 버전이라 항상 호환됨.
        from src.dl.train import run as train_lstm
        train_lstm()
        model = keras.models.load_model(MODEL_PATH)
    return {"model": model, "scaler": scaler, "df": df, "source": "lstm"}


def predict_tomorrow(models: dict, target_date: str | None = None) -> dict:
    """docs/contract.md 스키마({date, temp_max, temp_min, rain_prob, source})로 반환."""
    recent = models["df"].sort_values("date").tail(SEQ_LEN)[FEATURES]
    x = models["scaler"].transform(recent).reshape(1, SEQ_LEN, len(FEATURES))

    pred_reg, pred_rain = models["model"].predict(x, verbose=0)
    temp_max, temp_min = pred_reg[0]
    rain_prob = float(pred_rain[0][0])
    date = target_date or (dt.date.today() + dt.timedelta(days=1)).isoformat()

    return {
        "date": date,
        "temp_max": round(float(temp_max), 1),
        "temp_min": round(float(temp_min), 1),
        "rain_prob": round(rain_prob, 2),
        "source": models["source"],
    }
