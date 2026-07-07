"""공공데이터포털(data.go.kr) '기상청_단기예보 조회서비스'의 초단기예보(getUltraSrtFcst)로
"오늘 날씨" 채팅 질문에만 쓰는 실시간 근사치를 가져옴(예약 알림용 학습 데이터 수집은 fetch_kma.py가 그대로 담당).

초단기예보는 향후 약 6시간을 시간 단위로 주는 예보라 일 최고/최저기온이 따로 없음 -> 남은 시간대
예보의 최고/최저로 근사(진행 중인 오늘은 어차피 완전한 하루치 실측이 원천적으로 없어서 이게 최선).
같은 KMA_SERVICE_KEY를 쓰지만 data.go.kr에서 이 API(단기예보 조회서비스)도 별도로 활용신청돼 있어야 함.

실행:
    python -m src.ml.fetch_realtime
"""
import datetime as dt
import os

import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtFcst"
SEOUL_NX, SEOUL_NY = 60, 127  # 서울(중구 인근) 격자좌표


def _base_datetime(now: dt.datetime | None = None) -> tuple[str, str]:
    """초단기예보는 매시 30분에 생성되고 45분부터 조회 가능 -> 아직 안 나온 시각이면 한 시간 전 걸 씀."""
    now = now or dt.datetime.now()
    if now.minute < 45:
        now -= dt.timedelta(hours=1)
    base = now.replace(minute=30, second=0, microsecond=0)
    return base.strftime("%Y%m%d"), base.strftime("%H%M")


def get_today_forecast() -> dict:
    """contract.md 스키마({date, temp_max, temp_min, rain_prob, source})로 반환. 실패하면 예외를 그대로 던짐
    (호출부인 predictor.get_today_observed()가 캐시/실측 폴백으로 처리)."""
    base_date, base_time = _base_datetime()
    resp = requests.get(
        API_URL,
        params={
            "serviceKey": os.environ["KMA_SERVICE_KEY"],
            "pageNo": 1,
            "numOfRows": 200,
            "dataType": "JSON",
            "base_date": base_date,
            "base_time": base_time,
            "nx": SEOUL_NX,
            "ny": SEOUL_NY,
        },
        timeout=10,
    )
    resp.raise_for_status()
    body = resp.json()["response"]["body"]
    items = body["items"]["item"]

    temps = [float(it["fcstValue"]) for it in items if it["category"] == "T1H"]
    ptys = [it["fcstValue"] for it in items if it["category"] == "PTY"]
    if not temps:
        raise ValueError(f"T1H(기온) 항목 없음 — 응답: {items[:3]}")

    return {
        "date": dt.date.today().isoformat(),
        "temp_max": round(max(temps), 1),
        "temp_min": round(min(temps), 1),
        "rain_prob": 1.0 if any(v != "0" for v in ptys) else 0.0,  # PTY(강수형태)는 확률이 아니라 유무라 0/1로 근사
        "source": "kma_realtime",
    }


if __name__ == "__main__":
    # base_time 롤백 로직 확인(45분 이전엔 한 시간 전으로 물러남)
    d, t = _base_datetime(dt.datetime(2026, 7, 7, 6, 20))
    assert (d, t) == ("20260707", "0530"), (d, t)
    d, t = _base_datetime(dt.datetime(2026, 7, 7, 0, 10))
    assert (d, t) == ("20260706", "2330"), (d, t)

    pred = get_today_forecast()
    assert pred["source"] == "kma_realtime"
    assert 0 <= pred["rain_prob"] <= 1
    assert pred["temp_max"] >= pred["temp_min"]
    print(pred)
