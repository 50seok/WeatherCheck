"""Phase 2: LSTM 학습 + ML 대비 비교 그래프. 실행: python -m src.dl.train (project root에서)"""
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, mean_absolute_error
from tensorflow import keras

from src.dl.sequences import FEATURES, SEQ_LEN, build_sequences
from src.ml.predict import load_data, train_all

matplotlib.rcParams["font.family"] = "Malgun Gothic"  # Windows 한글 폰트
matplotlib.rcParams["axes.unicode_minus"] = False

MODEL_DIR = "src/dl/models"
FIG_DIR = "notebooks/figures"


def build_model(seq_len: int, n_features: int) -> keras.Model:
    inputs = keras.Input(shape=(seq_len, n_features))
    x = keras.layers.LSTM(32)(inputs)
    x = keras.layers.Dense(16, activation="relu")(x)
    reg_out = keras.layers.Dense(2, name="temp")(x)
    rain_out = keras.layers.Dense(1, activation="sigmoid", name="rain")(x)
    model = keras.Model(inputs, [reg_out, rain_out])
    model.compile(optimizer="adam", loss={"temp": "mse", "rain": "binary_crossentropy"})
    return model


def run():
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    df = load_data()
    X, y_reg, y_rain, _ = build_sequences(df)

    split = int(len(X) * 0.8)
    X_train, X_test = X[:split], X[split:]
    y_reg_train, y_reg_test = y_reg[:split], y_reg[split:]
    y_rain_train, y_rain_test = y_rain[:split], y_rain[split:]

    model = build_model(SEQ_LEN, len(FEATURES))
    history = model.fit(
        X_train, {"temp": y_reg_train, "rain": y_rain_train},
        validation_split=0.1, epochs=50, batch_size=16, verbose=0,
        callbacks=[keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)],
    )
    model.save(f"{MODEL_DIR}/lstm_model.keras")

    pred_reg, pred_rain = model.predict(X_test, verbose=0)
    lstm_mae_max = mean_absolute_error(y_reg_test[:, 0], pred_reg[:, 0])
    lstm_mae_min = mean_absolute_error(y_reg_test[:, 1], pred_reg[:, 1])
    lstm_acc = accuracy_score(y_rain_test, (pred_rain.ravel() > 0.5).astype(int))

    ml = train_all(df)

    print("=== ML vs DL: 회귀 MAE (내일 최고기온, °C, 낮을수록 좋음) ===")
    print(f"ML 최고({ml['best_reg_name']}): {ml['best_mae']:.3f}")
    print(f"LSTM: {lstm_mae_max:.3f}  (참고: 최저기온 MAE={lstm_mae_min:.3f})")
    print("\n=== ML vs DL: 분류 Accuracy (내일 비 여부, 높을수록 좋음) ===")
    print(f"ML 최고({ml['best_clf_name']}): {ml['best_acc']:.3f}")
    print(f"LSTM: {lstm_acc:.3f}")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    axes[0].plot(history.history["loss"], label="train_loss")
    axes[0].plot(history.history["val_loss"], label="val_loss")
    axes[0].set_title("LSTM 학습곡선")
    axes[0].legend()

    labels = [ml["best_reg_name"], "LSTM"]
    axes[1].bar(labels, [ml["best_mae"], lstm_mae_max], color=["steelblue", "coral"])
    axes[1].set_title("ML vs DL — 내일 최고기온 MAE(°C)")
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/ml_vs_dl.png", dpi=100)
    plt.close()

    print(f"\n그래프 저장 -> {FIG_DIR}/ml_vs_dl.png, 모델 저장 -> {MODEL_DIR}/lstm_model.keras")
    return {"lstm_mae_max": lstm_mae_max, "lstm_acc": lstm_acc, "ml_mae": ml["best_mae"], "ml_acc": ml["best_acc"]}


if __name__ == "__main__":
    run()
