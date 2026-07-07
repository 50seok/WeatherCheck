import datetime as dt
from pathlib import Path

from src.llm import chat as llm_chat
from src.rag import search

NICHE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge" / "niche"
NICHE_LABELS = {"bike": "자전거 통근"}
NICHE_DOCS = {"bike": "자전거통근_노면가이드"}


def _build_query(prediction: dict) -> str:
    triggers = []
    if prediction["rain_prob"] >= 0.4:
        # ponytail: 기온 0도 이하면 강수가 눈/진눈깨비일 가능성이 높음 -> 우산보다 노면 결빙 쪽으로 검색 유도
        if prediction["temp_min"] <= 0:
            triggers.append("노면 결빙 빙판길")
        else:
            triggers.append("우산 강수확률")
    if prediction["temp_max"] - prediction["temp_min"] >= 8:
        triggers.append("일교차 옷차림")
    if prediction["temp_max"] >= 33:
        triggers.append("폭염")
    if prediction["temp_min"] <= 3:
        triggers.append("한파")
    return " ".join(triggers) or "내일 날씨 옷차림"


def _ask(prompt: str) -> str:
    return llm_chat(prompt)


# [일교차_옷차림지수] 문서의 "기본 옷차림" 표(평균기온 기준)를 그대로 옮긴 것 — 코드가 임의로 정한 값이 아니라
# 사용자에게도 그대로 인용되는 그 문서의 표를 계산만 대신 해주는 것.
_CLOTHING_TABLE = [
    (28, float("inf"), "반팔"),
    (20, 28, "얇은 셔츠"),
    (12, 20, "니트+재킷"),
    (5, 12, "코트"),
    (float("-inf"), 5, "패딩급 방한복"),
]


def _fixed_clothing_line(prediction: dict, personal_offset: float | None = None) -> str:
    """[일교차_옷차림지수] 문서의 평균기온 표+일교차 추가겉옷 규칙을 코드로 그대로 계산해서 확정.
    로컬 sLLM(7.8B)한테 같은 문서를 주고 판단을 맡기면 5번 중 1~2번꼴로 표 기준을 무시하고
    엉뚱한 결론(예: 20도가 넘는데도 가디건 필수)을 냄(확인됨, sLLM 한계라 프롬프트 튜닝으로는 100% 못 잡음).
    임의의 숫자를 코드에 박아넣는 게 아니라, 이미 인용되는 문서의 표를 그대로 계산만 이쪽에서 맡는 것."""
    offset = personal_offset if personal_offset and personal_offset > 0 else 0
    avg_temp = (prediction["temp_max"] + prediction["temp_min"]) / 2 - offset
    item = next(line for low, high, line in _CLOTHING_TABLE if low <= avg_temp < high)

    diurnal = prediction["temp_max"] - prediction["temp_min"]
    if diurnal >= 10:
        extra = " 아침저녁엔 가디건·바람막이 같은 겉옷도 하나 챙기세요."
    elif diurnal >= 8:
        extra = " 아침저녁용으로 얇은 겉옷 하나 정도 챙기면 좋아요."
    else:
        extra = ""
    return f"👕 [일교차_옷차림지수] 기준 오늘 옷차림은 {item} 정도가 적당해요.{extra}"


def generate_briefing(prediction: dict, personal_offset: float | None = None) -> str:
    hits = search(_build_query(prediction))
    # ponytail: 옷차림 관련 결론은 _fixed_clothing_line이 이미 확정해서 앞에 붙이는데, 이 문서를 자유서술
    # 프롬프트에도 넣으면 로컬 sLLM이 실제 일교차 수치를 확인 안 하고 "일교차가 크다"처럼 데이터와 모순되는
    # 말을 지어내는 경우가 확인됨 -> 옷차림은 이미 다뤘으니 자유서술 컨텍스트에서는 이 문서를 아예 제외.
    hits = [(doc_id, text) for doc_id, text in hits if doc_id != "일교차_옷차림지수"]
    context = "\n\n".join(f"[{doc_id}]\n{text}" for doc_id, text in hits)

    today = dt.date.today()
    d = dt.datetime.strptime(prediction["date"], "%Y-%m-%d").date()
    if d == today:
        when = "오늘 서울 실측 날씨" if prediction.get("source") == "observed" else f"오늘({prediction['date']}) 서울 날씨 예측(전날 생성)"
    elif d == today + dt.timedelta(days=1):
        when = f"내일({prediction['date']}) 서울 날씨 예측"
    else:
        when = f"{prediction['date']} 서울 실측 날씨(데이터 수집 지연으로 최근값)"  # ponytail: KMA 수집이 밀려서 관측 폴백이 오늘도 내일도 아닐 때
    snow_note = ""
    if prediction["rain_prob"] >= 0.4 and prediction["temp_min"] <= 0:
        snow_note = "\n참고: 이 기온대의 강수는 눈·진눈깨비일 가능성이 높아. 우산보다 노면 결빙(빙판길) 주의와 방한을 우선으로 안내해줘."

    clothing_line = _fixed_clothing_line(prediction, personal_offset)
    prompt = f"""{when}: 최고 {prediction['temp_max']}°C, 최저 {prediction['temp_min']}°C, 강수확률 {prediction['rain_prob'] * 100:.0f}%

참고 문서:
{context}

옷차림은 이미 안내했으니 다시 언급하지 말고, 위 참고 문서를 근거로 강수·자외선 등 옷차림 이외에 출근 전 챙길 것을 1~2문장의 자연스러운 한국어로 안내해줘. 이모지를 섞고, 근거로 삼은 문서는 대괄호로 표시해줘(예: [문서명]).{snow_note}"""
    return f"{clothing_line} {_ask(prompt)}"


def generate_niche_briefing(prediction: dict, niche: str) -> str:
    """날씨 브리핑과 분리된 니치 전용 조언 — 눈에 띄게 별도 섹션으로 표시하기 위해 따로 생성.
    니치당 문서 1개로 1:1 대응이라 검색 없이 바로 읽음(일반 검색 풀과 섞여 오염되는 것도 방지)."""
    doc_id = NICHE_DOCS[niche]
    text = (NICHE_DIR / f"{doc_id}.md").read_text(encoding="utf-8")

    prompt = f"""오늘/내일 날씨: 최고 {prediction['temp_max']}°C, 최저 {prediction['temp_min']}°C, 강수확률 {prediction['rain_prob'] * 100:.0f}%

참고 문서:
[{doc_id}]
{text}

사용자는 {NICHE_LABELS[niche]}이야. 위 참고 문서를 근거로 이 날씨에서 특히 챙길 점을 1~2문장으로 안내해줘. 이모지를 섞고, 근거로 삼은 문서는 대괄호로 표시해줘(예: [문서명])."""
    return _ask(prompt)


if __name__ == "__main__":
    from src.predictor import get_prediction

    pred = get_prediction()
    print(generate_briefing(pred))
    print(generate_niche_briefing(pred, "bike"))
