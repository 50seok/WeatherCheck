"""서울 과거 날씨 합성 데이터 생성.

ponytail: data.kma.go.kr는 로그인+수동 다운로드라 자동 수집 불가.
서울 기후 계절 패턴(월별 평균기온·강수확률) 기반 합성 데이터로 대체.
실데이터 확보 시 이 스크립트 대신 동일 컬럼 스키마의 CSV로 교체하면 됨.
"""
import numpy as np
import pandas as pd

OUT_PATH = "data/raw/seoul_weather.csv"

# 서울 월별 평균기온(°C)·일교차·강수확률 근사치 (기상청 평년값 참고)
MONTHLY_TEMP_AVG = [-1.9, 0.7, 6.0, 13.0, 18.6, 23.2, 26.4, 27.1, 22.2, 15.2, 7.5, 0.4]
MONTHLY_RANGE = [7.5, 8.0, 8.5, 9.0, 8.5, 7.0, 6.0, 6.5, 7.5, 8.5, 8.0, 7.5]
MONTHLY_RAIN_PROB = [0.15, 0.15, 0.2, 0.2, 0.25, 0.35, 0.55, 0.5, 0.3, 0.15, 0.15, 0.15]


def generate(start="2024-01-01", days=730, seed=42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range(start, periods=days, freq="D")
    months = dates.month - 1

    temp_avg = np.array([MONTHLY_TEMP_AVG[m] for m in months]) + rng.normal(0, 2.5, days)
    day_range = np.array([MONTHLY_RANGE[m] for m in months]) + rng.normal(0, 1.0, days)
    temp_max = temp_avg + day_range / 2
    temp_min = temp_avg - day_range / 2

    rain_prob = np.array([MONTHLY_RAIN_PROB[m] for m in months])
    rain = rng.random(days) < rain_prob
    precip = np.where(rain, rng.gamma(2.0, 8.0, days), 0.0).round(1)

    humidity = (55 + 20 * rain + rng.normal(0, 8, days)).clip(20, 100).round(1)
    pressure = (1015 - 0.15 * temp_avg + rng.normal(0, 4, days)).round(1)
    wind_speed = rng.gamma(2.0, 1.3, days).round(1)

    return pd.DataFrame({
        "date": dates.strftime("%Y-%m-%d"),
        "temp_avg": temp_avg.round(1),
        "temp_max": temp_max.round(1),
        "temp_min": temp_min.round(1),
        "humidity": humidity,
        "pressure": pressure,
        "wind_speed": wind_speed,
        "precip": precip,
    })


if __name__ == "__main__":
    df = generate()
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    print(f"saved {len(df)} rows -> {OUT_PATH}")
