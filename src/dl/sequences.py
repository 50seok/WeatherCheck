"""일별 시계열 -> LSTM 입력 시퀀스(최근 SEQ_LEN일 -> 다음날) 변환."""
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

SEQ_LEN = 7
FEATURES = ["temp_avg", "temp_max", "temp_min", "humidity", "pressure", "wind_speed", "precip"]


def build_sequences(df: pd.DataFrame, seq_len: int = SEQ_LEN):
    """반환: X(샘플,seq_len,피처), y_reg(샘플,[temp_max,temp_min]), y_rain(샘플,), scaler.

    ponytail: 스케일러를 전체 데이터에 fit(약한 leakage) — 데이터가 914행뿐이라
    train/test 분리 fit까지는 과함. 데이터 대폭 늘면 train만으로 fit하도록 분리.
    """
    df = df.sort_values("date").reset_index(drop=True)
    scaler = MinMaxScaler()
    scaled = scaler.fit_transform(df[FEATURES])

    X, y_reg, y_rain = [], [], []
    for i in range(len(df) - seq_len):
        X.append(scaled[i:i + seq_len])
        y_reg.append(df.loc[i + seq_len, ["temp_max", "temp_min"]].to_numpy(dtype=float))
        y_rain.append(float(df.loc[i + seq_len, "precip"] > 0))

    return np.array(X), np.array(y_reg), np.array(y_rain), scaler
