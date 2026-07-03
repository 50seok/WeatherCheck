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
from src.predictor import get_prediction

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


def extract_time(text: str) -> str | None:
    """자연어 문장에서 24시간제 HH:MM 알림 시각 추출. 없으면 None."""
    resp = Anthropic().messages.create(
        model=TIME_MODEL,
        max_tokens=10,
        messages=[{
            "role": "user",
            "content": (
                "다음 문장에서 사용자가 원하는 하루 중 알림 시각을 24시간제 HH:MM 형식으로만 답해. "
                "시각 정보가 없으면 NONE만 답해. 다른 말은 절대 하지 마.\n\n"
                f"문장: {text}"
            ),
        }],
    )
    result = resp.content[0].text.strip()
    if len(result) != 5 or result[2] != ":":
        return None
    return result


@client.event
async def on_ready():
    print(f"logged in as {client.user}")
    check_schedule.start()


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    if "알림" in message.content:
        hhmm = extract_time(message.content)
        if hhmm:
            schedule = _load_schedule()
            schedule[str(message.channel.id)] = hhmm
            _save_schedule(schedule)
            await message.channel.send(f"✅ 매일 {hhmm}에 이 채널로 브리핑을 보내드릴게요.")
        else:
            await message.channel.send("몇 시에 보내드릴까요? 예: '알림 매일 아침 8시에 보내줘'")
        return

    if "날씨" in message.content:
        async with message.channel.typing():
            text = generate_briefing(get_prediction())
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
