"""개인 체감 피드백 학습 (PRD 4순위, 프로젝트 시그니처 기능).
알림 후 "추웠어/딱 좋았어/더웠어" 피드백을 쌓아서 개인별 체감온도 보정값을 계산.
표본이 적은(며칠짜리) 프로젝트 특성상 복잡한 회귀 대신 라벨별 평균 보정치로 계산
(ponytail: 데이터 몇 개로 회귀모델 학습하면 과적합이라 오히려 신뢰성이 떨어짐).
"""
import json
import os

FEEDBACK_PATH = "data/feedback.json"
LAST_WEATHER_PATH = "data/last_weather.json"
MIN_SAMPLES = 3  # 이 개수 미만이면 보정 없이 중립 취급
LABEL_OFFSET = {"cold": 2.5, "good": 0, "hot": -2.5}  # 체감 보정 방향(°C), 라벨당 가중치


def _load(path: str) -> dict:
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_last_weather(channel_id: str, prediction: dict) -> None:
    """피드백 버튼 클릭 시 어느 날씨에 대한 반응인지 알기 위해 마지막 발송 날씨를 기록."""
    data = _load(LAST_WEATHER_PATH)
    data[channel_id] = {"temp_max": prediction["temp_max"], "date": prediction["date"]}
    _save(LAST_WEATHER_PATH, data)


def record_feedback(channel_id: str, label: str) -> bool:
    """마지막 발송 날씨 기준으로 피드백 기록. 발송 기록이 없으면 False."""
    weather = _load(LAST_WEATHER_PATH).get(channel_id)
    if not weather:
        return False
    data = _load(FEEDBACK_PATH)
    entries = data.setdefault(channel_id, [])
    entries.append({"temp_max": weather["temp_max"], "date": weather["date"], "feedback": label})
    _save(FEEDBACK_PATH, data)
    return True


def get_personal_offset(channel_id: str) -> float | None:
    """누적 피드백 기반 개인 체감온도 보정값(°C). 표본 부족하면 None(중립, 보정 안 함)."""
    entries = _load(FEEDBACK_PATH).get(channel_id, [])
    if len(entries) < MIN_SAMPLES:
        return None
    avg = sum(LABEL_OFFSET[e["feedback"]] for e in entries) / len(entries)
    return round(avg, 1)


if __name__ == "__main__":
    print(get_personal_offset("test_channel"))
