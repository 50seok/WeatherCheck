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


def generate_briefing(prediction: dict, personal_offset: float | None = None) -> str:
    hits = search(_build_query(prediction))
    context = "\n\n".join(f"[{doc_id}]\n{text}" for doc_id, text in hits)

    when = "오늘 서울 실측 날씨" if prediction.get("source") == "observed" else f"내일({prediction['date']}) 서울 날씨 예측"
    offset_note = ""
    if personal_offset:
        direction = "춥게" if personal_offset > 0 else "덥게"
        offset_note = f"\n참고: 이 사용자는 과거 피드백 기준 실제 기온보다 체감상 약 {abs(personal_offset)}°C 더 {direction} 느끼는 경향이 있어. 옷차림 조언을 이 경향에 맞게 조정해줘."
    snow_note = ""
    if prediction["rain_prob"] >= 0.4 and prediction["temp_min"] <= 0:
        snow_note = "\n참고: 이 기온대의 강수는 눈·진눈깨비일 가능성이 높아. 우산보다 노면 결빙(빙판길) 주의와 방한을 우선으로 안내해줘."
    prompt = f"""{when}: 최고 {prediction['temp_max']}°C, 최저 {prediction['temp_min']}°C, 강수확률 {prediction['rain_prob'] * 100:.0f}%

참고 문서:
{context}

위 참고 문서 내용을 근거로 삼아 출근 전 챙길 것을 2~3문장의 자연스러운 한국어로 안내해줘. 이모지를 섞고, 근거로 삼은 문서는 대괄호로 표시해줘(예: [문서명]).{offset_note}{snow_note}"""
    return _ask(prompt)


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
