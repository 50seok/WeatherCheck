"""시연용 더미 피드백 생성 — 실제 사용 며칠로는 개인 체감 학습 효과를 보여주기 힘들어서,
"실제 기온보다 춥게 느끼는 사람" 시나리오로 과거 피드백을 미리 채워 넣음(PRD 예시 그대로).
사용: python -m src.seed_feedback <channel_id>
"""
import sys

from src.feedback import FEEDBACK_PATH, _load, _save  # noqa: F401 (내부 저장 포맷 그대로 재사용)

DUMMY_ENTRIES = [
    {"date": "2026-06-25", "temp_max": 22.0, "feedback": "cold"},
    {"date": "2026-06-26", "temp_max": 25.0, "feedback": "cold"},
    {"date": "2026-06-27", "temp_max": 18.0, "feedback": "cold"},
    {"date": "2026-06-28", "temp_max": 28.0, "feedback": "good"},
    {"date": "2026-06-29", "temp_max": 20.0, "feedback": "cold"},
    {"date": "2026-06-30", "temp_max": 26.0, "feedback": "cold"},
    {"date": "2026-07-01", "temp_max": 24.0, "feedback": "cold"},
    {"date": "2026-07-02", "temp_max": 29.0, "feedback": "good"},
    {"date": "2026-07-03", "temp_max": 19.0, "feedback": "cold"},
    {"date": "2026-07-04", "temp_max": 27.0, "feedback": "cold"},
]


def seed(channel_id: str) -> None:
    data = _load(FEEDBACK_PATH)
    data[channel_id] = DUMMY_ENTRIES
    _save(FEEDBACK_PATH, data)
    print(f"{channel_id}에 더미 피드백 {len(DUMMY_ENTRIES)}건 저장 완료 (평균 보정치 확인: python -m src.feedback 대신 get_personal_offset 호출)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("사용: python -m src.seed_feedback <channel_id>")
        sys.exit(1)
    seed(sys.argv[1])
