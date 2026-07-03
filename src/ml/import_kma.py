"""KMA ASOS 일자료 CSV(EUC-KR, data.kma.go.kr 다운로드본) -> data/raw/seoul_weather.csv 변환.

python src/ml/import_kma.py <kma_csv_경로>
"""
import sys

import pandas as pd

OUT_PATH = "data/raw/seoul_weather.csv"
KMA_COLUMNS = [
    "station", "station_name", "date",
    "temp_avg", "temp_min", "temp_max",
    "precip", "wind_speed", "humidity", "pressure",
]


def convert(src_path: str) -> pd.DataFrame:
    df = pd.read_csv(src_path, encoding="euc-kr", names=KMA_COLUMNS, header=0)
    df["precip"] = df["precip"].fillna(0)  # 빈값=무강수
    df = df[["date", "temp_avg", "temp_max", "temp_min", "humidity", "pressure", "wind_speed", "precip"]]
    df.iloc[:, 1:] = df.iloc[:, 1:].interpolate(limit_direction="both")  # 관측 결측치(예: 풍속 3건)
    return df


if __name__ == "__main__":
    df = convert(sys.argv[1])
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"saved {len(df)} rows ({df['date'].min()} ~ {df['date'].max()}) -> {OUT_PATH}")
