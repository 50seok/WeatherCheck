"""공공데이터포털(data.go.kr) '기상청_지상(종관)일자료 조회서비스' API로 최신 일자료를 받아
data/raw/seoul_weather.csv에 이어붙임(append). import_kma.py(수동 CSV 변환)의 자동화 버전.

실행:
    python -m src.ml.fetch_kma                  # (기존 CSV 마지막 날짜+1일) ~ 어제까지 자동 수집·추가
    python -m src.ml.fetch_kma 2026-07-03 2026-07-05          # 기간 직접 지정해서 추가
    python -m src.ml.fetch_kma 2026-06-25 2026-07-02 --dry-run  # CSV에 이미 있는 기간으로 필드 매핑 검증만(안 씀)

주의: sumRn(강수량)·avgPa(평균현지기압) 등 API 필드명은 문서 기준으로 매핑한 것 — 처음 쓸 땐
반드시 --dry-run으로 기존 CSV와 겹치는 기간을 조회해 값이 얼추 맞는지 확인 후 실제 추가할 것.
"""
import datetime as dt
import os
import sys

import pandas as pd
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://apis.data.go.kr/1360000/AsosDalyInfoService/getWthrDataList"
OUT_PATH = "data/raw/seoul_weather.csv"
SEOUL_STN_ID = "108"


def fetch_range(start_date: str, end_date: str, service_key: str | None = None) -> pd.DataFrame:
    """start_date~end_date(YYYY-MM-DD, 포함) 서울(108) 일자료를 API로 받아 기존 스키마로 변환."""
    key = service_key or os.environ["KMA_SERVICE_KEY"]
    resp = requests.get(
        API_URL,
        params={
            "serviceKey": key,
            "pageNo": 1,
            "numOfRows": 999,
            "dataType": "JSON",
            "dataCd": "ASOS",
            "dateCd": "DAY",
            "startDt": start_date.replace("-", ""),
            "endDt": end_date.replace("-", ""),
            "stnIds": SEOUL_STN_ID,
        },
        timeout=10,
    )
    resp.raise_for_status()
    body = resp.json()["response"]["body"]
    items = body["items"]["item"] if body.get("totalCount", 0) else []
    if not items:
        return pd.DataFrame(columns=["date", "temp_avg", "temp_max", "temp_min", "humidity", "pressure", "wind_speed", "precip"])

    rows = [{
        "date": it["tm"],
        "temp_avg": float(it["avgTa"]),
        "temp_max": float(it["maxTa"]),
        "temp_min": float(it["minTa"]),
        "humidity": float(it["avgRhm"]),
        "pressure": float(it["avgPa"]),
        "wind_speed": float(it["avgWs"]),
        "precip": float(it["sumRn"]) if it.get("sumRn") not in (None, "") else 0.0,
    } for it in items]
    return pd.DataFrame(rows)


def append(new_rows: pd.DataFrame) -> pd.DataFrame:
    """기존 CSV + 신규 행을 날짜 기준 중복 제거(신규 우선) 후 저장."""
    existing = pd.read_csv(OUT_PATH, parse_dates=["date"]) if os.path.exists(OUT_PATH) else pd.DataFrame()
    new_rows = new_rows.copy()
    new_rows["date"] = pd.to_datetime(new_rows["date"])
    combined = pd.concat([existing, new_rows], ignore_index=True)
    combined = combined.drop_duplicates(subset="date", keep="last").sort_values("date").reset_index(drop=True)
    combined["date"] = combined["date"].dt.strftime("%Y-%m-%d")
    combined.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")
    return combined


def _default_range() -> tuple[str, str]:
    yesterday = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    if os.path.exists(OUT_PATH):
        last = pd.read_csv(OUT_PATH, usecols=["date"])["date"].max()
        start = (dt.date.fromisoformat(last) + dt.timedelta(days=1)).isoformat()
    else:
        start = yesterday
    return start, yesterday


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry_run = "--dry-run" in sys.argv
    start, end = (args[0], args[1]) if len(args) >= 2 else _default_range()

    if start > end:
        print(f"수집할 새 날짜 없음 (마지막 데이터가 이미 최신, start={start} > end={end})")
        sys.exit(0)

    print(f"조회: {start} ~ {end}")
    df = fetch_range(start, end)
    print(df.to_string(index=False))

    if dry_run:
        print("\n--dry-run이라 저장 안 함. 기존 CSV의 같은 기간 값과 비교해서 필드 매핑이 맞는지 확인하세요.")
    else:
        combined = append(df)
        print(f"\nsaved {len(df)} new rows -> {OUT_PATH} (total {len(combined)} rows, {combined['date'].min()} ~ {combined['date'].max()})")
