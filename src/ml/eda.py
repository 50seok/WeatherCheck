"""EDA: 결측치·이상치·시계열 분포·상관관계 확인. 그래프는 notebooks/figures/에 저장."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

matplotlib.rcParams["font.family"] = "Malgun Gothic"  # Windows 한글 폰트
matplotlib.rcParams["axes.unicode_minus"] = False

DATA_PATH = "data/raw/seoul_weather.csv"
FIG_DIR = "notebooks/figures"


def run():
    import os
    os.makedirs(FIG_DIR, exist_ok=True)
    df = pd.read_csv(DATA_PATH, parse_dates=["date"])

    print("=== 결측치 ===")
    print(df.isna().sum())
    print("\n=== 기술통계 ===")
    print(df.describe())

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    axes[0].plot(df["date"], df["temp_avg"], label="temp_avg")
    axes[0].fill_between(df["date"], df["temp_min"], df["temp_max"], alpha=0.2)
    axes[0].set_title("서울 일별 기온 (2년)")
    axes[0].legend()
    axes[1].bar(df["date"], df["precip"], width=1.0, color="steelblue")
    axes[1].set_title("일별 강수량(mm)")
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/timeseries.png", dpi=100)
    plt.close()

    num_cols = ["temp_avg", "temp_max", "temp_min", "humidity", "pressure", "wind_speed", "precip"]
    plt.figure(figsize=(7, 6))
    sns.heatmap(df[num_cols].corr(), annot=True, fmt=".2f", cmap="coolwarm", center=0)
    plt.title("변수 간 상관관계")
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/correlation.png", dpi=100)
    plt.close()

    print(f"\n그래프 저장 완료 -> {FIG_DIR}/timeseries.png, {FIG_DIR}/correlation.png")


if __name__ == "__main__":
    run()
