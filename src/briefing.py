from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

from src.rag import search

load_dotenv()

MODEL = "claude-haiku-4-5-20251001"

NICHE_DIR = Path(__file__).resolve().parent.parent / "data" / "knowledge" / "niche"
NICHE_LABELS = {"bike": "자전거 통근"}
NICHE_DOCS = {"bike": "자전거통근_노면가이드"}


def _build_query(prediction: dict) -> str:
    triggers = []
    if prediction["rain_prob"] >= 0.4:
        triggers.append("우산 강수확률")
    if prediction["temp_max"] - prediction["temp_min"] >= 8:
        triggers.append("일교차 옷차림")
    if prediction["temp_max"] >= 33:
        triggers.append("폭염")
    if prediction["temp_min"] <= 3:
        triggers.append("한파")
    return " ".join(triggers) or "내일 날씨 옷차림"


def _ask(prompt: str) -> str:
    client = Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


def generate_briefing(prediction: dict) -> str:
    hits = search(_build_query(prediction))
    context = "\n\n".join(f"[{doc_id}]\n{text}" for doc_id, text in hits)

    when = "오늘 서울 실측 날씨" if prediction.get("source") == "observed" else f"내일({prediction['date']}) 서울 날씨 예측"
    prompt = f"""{when}: 최고 {prediction['temp_max']}°C, 최저 {prediction['temp_min']}°C, 강수확률 {prediction['rain_prob'] * 100:.0f}%

참고 문서:
{context}

위 참고 문서 내용을 근거로 삼아 출근 전 챙길 것을 2~3문장의 자연스러운 한국어로 안내해줘. 이모지를 섞고, 근거로 삼은 문서는 대괄호로 표시해줘(예: [문서명])."""
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
