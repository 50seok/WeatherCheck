from anthropic import Anthropic
from dotenv import load_dotenv

from src.rag import search

load_dotenv()

MODEL = "claude-sonnet-5"


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
    return " ".join(triggers) or "오늘 날씨 옷차림"


def generate_briefing(prediction: dict) -> str:
    hits = search(_build_query(prediction))
    context = "\n\n".join(f"[{doc_id}]\n{text}" for doc_id, text in hits)

    prompt = f"""오늘 서울 날씨 예측: 최고 {prediction['temp_max']}°C, 최저 {prediction['temp_min']}°C, 강수확률 {prediction['rain_prob'] * 100:.0f}%

참고 문서:
{context}

위 참고 문서 내용을 근거로 삼아 출근 전 챙길 것을 2~3문장의 자연스러운 한국어로 안내해줘. 이모지를 섞고, 근거로 삼은 문서는 대괄호로 표시해줘(예: [문서명])."""

    client = Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text


if __name__ == "__main__":
    from src.predictor import get_mock_prediction

    print(generate_briefing(get_mock_prediction()))
