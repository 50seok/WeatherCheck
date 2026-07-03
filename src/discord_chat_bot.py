"""디스코드 대화형 봇: 채팅으로 "날씨" 물어보면 RAG 브리핑 답장, "알림"으로 자연어 시간 설정.
send_briefing(웹훅, 단방향)과 별개 — 이건 실시간으로 메시지를 들어야 해서 계속 실행 상태 유지 필요.
실행: python -m src.discord_chat_bot
"""
import datetime as dt
import json
import os

import discord
from anthropic import Anthropic
from discord.ext import tasks
from dotenv import load_dotenv

from src.briefing import generate_briefing
from src.predictor import get_prediction, get_today_observed

load_dotenv()

SCHEDULE_PATH = "data/schedule.json"
TIME_MODEL = "claude-haiku-4-5-20251001"

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
_sent_today: dict[str, str] = {}


def _load_schedule() -> dict:
    if os.path.exists(SCHEDULE_PATH):
        with open(SCHEDULE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_schedule(schedule: dict) -> None:
    os.makedirs(os.path.dirname(SCHEDULE_PATH), exist_ok=True)
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)


def classify_message(text: str) -> tuple[str, str | None]:
    """메시지 의도를 분류. 키워드 매칭 대신 자연스러운 표현도 인식하도록 Claude에게 위임.

    반환: (intent, detail)
    intent: "weather_today" | "weather_tomorrow" | "weather_other" | "schedule" | "none"
    detail: schedule일 때만 HH:MM(또는 None), 그 외엔 None.
    """
    resp = Anthropic().messages.create(
        model=TIME_MODEL,
        max_tokens=20,
        messages=[{
            "role": "user",
            "content": (
                "디스코드 채널의 메시지 하나를 아래 중 정확히 하나로 분류해서, "
                "반드시 지정된 라벨로만 답해(다른 말 절대 하지 마):\n"
                "- 오늘 날씨/우산/옷차림을 묻거나, 날짜 언급 없이 그냥 날씨를 물으면 -> WEATHER_TODAY\n"
                "- 내일 날씨를 물으면 -> WEATHER_TOMORROW\n"
                "- 오늘·내일이 아닌 다른 날(특정 요일, 모레, 며칠 뒤 등)의 날씨를 물으면 -> WEATHER_OTHER\n"
                "- 매일 정해진 시각에 브리핑을 자동으로 받고 싶다는 요청 -> SCHEDULE HH:MM"
                "(24시간제. 시각이 명시 안 됐으면 HH:MM 자리에 NONE)\n"
                "- 그 외 날씨/알림과 무관한 잡담 -> NONE\n\n"
                f"메시지: {text}"
            ),
        }],
    )
    result = resp.content[0].text.strip()
    if result.startswith("SCHEDULE"):
        parts = result.split()
        hhmm = parts[1] if len(parts) > 1 else "NONE"
        return "schedule", (hhmm if len(hhmm) == 5 and hhmm[2] == ":" else None)
    if result in ("WEATHER_TODAY", "WEATHER_TOMORROW", "WEATHER_OTHER"):
        return result.lower(), None
    return "none", None


@client.event
async def on_ready():
    print(f"logged in as {client.user}")
    check_schedule.start()


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    intent, hhmm = classify_message(message.content)

    if intent == "schedule":
        if hhmm:
            schedule = _load_schedule()
            schedule[str(message.channel.id)] = hhmm
            _save_schedule(schedule)
            await message.channel.send(f"✅ 매일 {hhmm}에 이 채널로 브리핑을 보내드릴게요.")
        else:
            await message.channel.send("몇 시에 보내드릴까요? 예: '아침 8시에 알려줘'")
        return

    if intent == "weather_other":
        await message.channel.send("죄송해요, 지금은 오늘·내일 날씨만 예측할 수 있어요. 더 먼 미래는 아직 지원하지 않아요 🙏")
        return

    if intent in ("weather_today", "weather_tomorrow"):
        async with message.channel.typing():
            pred = get_today_observed() if intent == "weather_today" else get_prediction()
            text = generate_briefing(pred)
        await message.channel.send(text)


@tasks.loop(minutes=1)
async def check_schedule():
    now = dt.datetime.now()
    hhmm = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    for channel_id, target in _load_schedule().items():
        if target == hhmm and _sent_today.get(channel_id) != today:
            channel = client.get_channel(int(channel_id))
            if channel:
                text = generate_briefing(get_prediction())
                await channel.send(text)
                _sent_today[channel_id] = today


if __name__ == "__main__":
    client.run(os.environ["DISCORD_BOT_TOKEN"])
