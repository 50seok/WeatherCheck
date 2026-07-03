"""Track B가 호출할 단일 진입점. docs/contract.md 스키마로 예측 dict 반환.

data/raw/seoul_weather.csv가 없으면(예: Streamlit Cloud 배포, git 미추적) 합성 데이터를
그 자리에서 생성해 학습한다 — 실데이터 확보 시 CSV만 교체하면 자동으로 그걸 사용.
"""
import datetime as dt
import os

import pandas as pd
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier, XGBRegressor

from src.ml.generate_data import generate

DATA_PATH = "data/raw/seoul_weather.csv"
FEATURES = ["temp_avg", "temp_max", "temp_min", "humidity", "pressure", "wind_speed", "precip_yesterday"]

REG_MODELS = {
    "LinearRegression": LinearRegression,
    "RandomForest": lambda: RandomForestRegressor(n_estimators=200, random_state=42),
    "XGBoost": lambda: XGBRegressor(n_estimators=200, random_state=42),
}
CLF_MODELS = {
    "LogisticRegression": lambda: LogisticRegression(max_iter=1000),
    "RandomForest": lambda: RandomForestClassifier(n_estimators=200, random_state=42),
    "XGBoost": lambda: XGBClassifier(n_estimators=200, random_state=42, eval_metric="logloss"),
}


def load_data() -> pd.DataFrame:
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH, parse_dates=["date"])
    return generate()


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.sort_values("date").reset_index(drop=True)
    df["precip_yesterday"] = df["precip"].shift(1)
    df["temp_max_tomorrow"] = df["temp_max"].shift(-1)
    df["temp_min_tomorrow"] = df["temp_min"].shift(-1)
    df["rain_tomorrow"] = (df["precip"].shift(-1) > 0).astype(int)
    return df.dropna().reset_index(drop=True)


def train_all(df: pd.DataFrame | None = None) -> dict:
    """모델 3개 비교 후 최고 모델로 재학습. 회귀(MAE)/분류(Accuracy) 비교표 + 학습된 모델 반환."""
    df = build_features(df if df is not None else load_data())
    X = df[FEATURES]
    X_train, X_test, idx_train, idx_test = train_test_split(
        X, df.index, test_size=0.2, random_state=42, shuffle=False
    )
    y_max_train, y_max_test = df["temp_max_tomorrow"].loc[idx_train], df["temp_max_tomorrow"].loc[idx_test]
    y_min_train = df["temp_min_tomorrow"].loc[idx_train]
    y_clf_train, y_clf_test = df["rain_tomorrow"].loc[idx_train], df["rain_tomorrow"].loc[idx_test]

    reg_scores, best_reg_name, best_mae = {}, None, float("inf")
    for name, make in REG_MODELS.items():
        model = make()
        model.fit(X_train, y_max_train)
        mae = mean_absolute_error(y_max_test, model.predict(X_test))
        reg_scores[name] = mae
        if mae < best_mae:
            best_reg_name, best_mae = name, mae

    clf_scores, best_clf_name, best_acc = {}, None, -1.0
    for name, make in CLF_MODELS.items():
        model = make()
        model.fit(X_train, y_clf_train)
        acc = accuracy_score(y_clf_test, model.predict(X_test))
        clf_scores[name] = acc
        if acc > best_acc:
            best_clf_name, best_acc = name, acc

    # 최고 성능 모델 종류로 전체 데이터 재학습(배포용 최종 모델)
    reg_max = REG_MODELS[best_reg_name]().fit(X, df["temp_max_tomorrow"])
    reg_min = REG_MODELS[best_reg_name]().fit(X, df["temp_min_tomorrow"])
    clf = CLF_MODELS[best_clf_name]().fit(X, df["rain_tomorrow"])

    return {
        "reg_scores": reg_scores,
        "clf_scores": clf_scores,
        "best_reg_name": best_reg_name,
        "best_mae": best_mae,
        "best_clf_name": best_clf_name,
        "best_acc": best_acc,
        "reg_max": reg_max,
        "reg_min": reg_min,
        "clf": clf,
        "source": best_reg_name.lower(),
    }


def predict_tomorrow(
    models: dict,
    temp_avg: float,
    temp_max: float,
    temp_min: float,
    humidity: float,
    pressure: float,
    wind_speed: float,
    precip_yesterday: float,
    target_date: str | None = None,
) -> dict:
    """docs/contract.md 스키마({date, temp_max, temp_min, rain_prob, source})로 반환."""
    x = pd.DataFrame([{
        "temp_avg": temp_avg, "temp_max": temp_max, "temp_min": temp_min,
        "humidity": humidity, "pressure": pressure, "wind_speed": wind_speed,
        "precip_yesterday": precip_yesterday,
    }])[FEATURES]

    pred_max = float(models["reg_max"].predict(x)[0])
    pred_min = float(models["reg_min"].predict(x)[0])
    rain_prob = float(models["clf"].predict_proba(x)[0][1])
    date = target_date or (dt.date.today() + dt.timedelta(days=1)).isoformat()

    return {
        "date": date,
        "temp_max": round(pred_max, 1),
        "temp_min": round(pred_min, 1),
        "rain_prob": round(rain_prob, 2),
        "source": models["source"],
    }
