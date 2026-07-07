import datetime as dt
import json
import os
import time

from src.dl.predict import load_models, predict_tomorrow
from src.ml.predict import load_data

PREDICTION_CACHE_PATH = "data/prediction_cache.json"


def get_prediction() -> dict:
    """Track A(LSTM, MAE 2.41°C — ML 대비 최고 성능) 내일 예측. contract.md 스키마 반환."""
    pred = predict_tomorrow(load_models())
    _cache_prediction(pred)
    return pred


def _read_cache() -> dict:
    """_cache_prediction()의 os.replace와 겹치면 Windows에서 일시적으로 PermissionError가 날 수 있어 잠깐 재시도."""
    for attempt in range(5):
        try:
            with open(PREDICTION_CACHE_PATH, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except (PermissionError, json.JSONDecodeError):
            if attempt == 4:
                raise
            time.sleep(0.02)


def _cache_prediction(pred: dict) -> None:
    """"내일" 예측을 날짜별로 저장해두면, 그 날짜가 "오늘"이 됐을 때 get_today_observed()가 재사용할 수 있음
    (KMA 일자료는 하루가 끝나야 확정되는 통계라 진행 중인 오늘치 관측값은 원천적으로 존재하지 않음)."""
    os.makedirs(os.path.dirname(PREDICTION_CACHE_PATH), exist_ok=True)
    cache = _read_cache()
    cache[pred["date"]] = pred
    tmp_path = PREDICTION_CACHE_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)
    # ponytail: 원자적 교체라 읽는 쪽은 절반짜리 파일을 볼 일이 없지만, Windows는 그 순간 파일이 열려 있으면
    # replace 자체가 PermissionError(공유 위반)를 낼 수 있어 짧게 재시도.
    for attempt in range(5):
        try:
            os.replace(tmp_path, PREDICTION_CACHE_PATH)
            return
        except PermissionError:
            if attempt == 4:
                raise
            time.sleep(0.02)


def get_today_observed() -> dict:
    """오늘 날씨: 어제 캐시해둔 "오늘자" 예측이 있으면 그걸 쓰고, 없으면 차선으로 가장 최근 실측치를 근사해서 반환."""
    today = dt.date.today().isoformat()
    cached = _read_cache().get(today)
    if cached:
        return cached

    row = load_data().sort_values("date").iloc[-1]
    return {
        "date": today,  # ponytail: KMA 일자료가 며칠 밀려도 "오늘 날씨"로 보여줄 거라 실제 관측 날짜 대신 오늘 날짜로 표시
        "temp_max": round(float(row["temp_max"]), 1),
        "temp_min": round(float(row["temp_min"]), 1),
        "rain_prob": 1.0 if row["precip"] > 0 else 0.0,
        "source": "observed",
    }


if __name__ == "__main__":
    pred = get_prediction()
    assert pred["source"] == "lstm"
    assert 0 <= pred["rain_prob"] <= 1
    assert pred["temp_max"] >= pred["temp_min"]
    assert _read_cache()[pred["date"]] == pred  # 캐시 기록 확인

    # 예약 알림 준비(쓰기)와 채팅 "오늘 날씨" 조회(읽기)가 겹치는 상황 재현 — 읽는 쪽이 예외를 보면 안 됨
    import threading

    stop = False

    def _writer():
        while not stop:
            _cache_prediction(pred)

    t = threading.Thread(target=_writer, daemon=True)
    t.start()
    for _ in range(200):
        _read_cache()  # 여기서 예외 나면 레이스 컨디션 재발
    stop = True
    t.join()
    print("concurrency check OK")
    print(pred)
