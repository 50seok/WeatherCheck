"""디스코드 대화형 봇: 날씨 질문에 RAG 브리핑 답장, 자연어로 알림 시간 설정, 채팅 정리, 도움말.
send_briefing(웹훅, 단방향)과 별개 — 이건 실시간으로 메시지를 들어야 해서 계속 실행 상태 유지 필요.
실행: python -m src.discord_chat_bot · 기능 목록은 HELP_TEXT 참고.
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
DEFAULT_CLEAR_COUNT = 50
PREP_MINUTES = 3  # 정각에 지연 없이 보내려고 이만큼 미리 브리핑을 만들어둠

HELP_TEXT = """🌤️ **출근 비서 봇 사용법**
- **오늘/내일 날씨** — "오늘 날씨 어때?", "내일 우산 필요해?" 처럼 물어보면 근거 문서를 인용해 답해드려요. (오늘·내일만 가능, 그 이상은 아직 지원 안 해요)
- **알림 시간 설정** — "매일 아침 8시에 알려줘" 처럼 말하면 매일 그 시각에 이 채널로 브리핑을 자동으로 보내드려요.
- **채팅 정리** — "메시지 정리해줘" / "최근 100개 지워줘" 처럼 말하면 최근 메시지를 지워드려요(기본 50개). 봇에게 '메시지 관리' 권한이 있어야 해요.
- **도움말** — "뭐 할 수 있어?", "명령어 알려줘" 라고 물어보면 이 안내를 다시 보여드려요."""

WEEKDAYS_KR = ["월", "화", "수", "목", "금", "토", "일"]


def format_header(prediction: dict) -> str:
    """디스코드 마크다운 헤더(#)로 날짜·요일을 크게 표시."""
    d = dt.datetime.strptime(prediction["date"], "%Y-%m-%d").date()
    label = "오늘" if prediction.get("source") == "observed" else "내일"
    return f"# {label} {d.isoformat()} ({WEEKDAYS_KR[d.weekday()]}요일)"


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
_sent_today: dict[str, str] = {}
_prepared: dict[str, tuple[str, str]] = {}  # channel_id -> (date, 미리 만들어둔 메시지)


def _minus_minutes(hhmm: str, minutes: int) -> str:
    return (dt.datetime.strptime(hhmm, "%H:%M") - dt.timedelta(minutes=minutes)).strftime("%H:%M")


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
    intent: "weather_today" | "weather_tomorrow" | "weather_other" | "schedule" | "clear" | "help" | "none"
    detail: schedule일 땐 HH:MM(또는 None), clear일 땐 지울 개수(문자열 숫자, 없으면 None), 그 외엔 None.
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
                "- 채팅/메시지를 정리·삭제해달라는 요청 -> CLEAR N"
                "(N은 지울 개수 숫자. 명시 안 됐으면 N 자리에 NONE)\n"
                "- 봇 사용법·도움말·명령어를 묻는 요청 -> HELP\n"
                "- 그 외 무관한 잡담 -> NONE\n\n"
                f"메시지: {text}"
            ),
        }],
    )
    result = resp.content[0].text.strip()
    if result.startswith("SCHEDULE"):
        parts = result.split()
        hhmm = parts[1] if len(parts) > 1 else "NONE"
        return "schedule", (hhmm if len(hhmm) == 5 and hhmm[2] == ":" else None)
    if result.startswith("CLEAR"):
        parts = result.split()
        count = parts[1] if len(parts) > 1 else "NONE"
        return "clear", (count if count.isdigit() else None)
    if result in ("WEATHER_TODAY", "WEATHER_TOMORROW", "WEATHER_OTHER", "HELP"):
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

    intent, detail = classify_message(message.content)

    if intent == "help":
        await message.channel.send(HELP_TEXT)
        return

    if intent == "clear":
        count = int(detail) if detail else DEFAULT_CLEAR_COUNT
        try:
            deleted = await message.channel.purge(limit=count + 1)  # +1: 요청 메시지 자신 포함
            notice = await message.channel.send(f"🧹 메시지 {len(deleted) - 1}개 정리했어요.")
            await notice.delete(delay=3)
        except discord.Forbidden:
            await message.channel.send("메시지를 지울 권한이 없어요. 봇 권한에 '메시지 관리(Manage Messages)'를 추가해주세요.")
        return

    if intent == "schedule":
        if detail:
            channel_id = str(message.channel.id)
            schedule = _load_schedule()
            schedule[channel_id] = detail
            _save_schedule(schedule)
            await message.channel.send(f"✅ 매일 {detail}에 이 채널로 브리핑을 보내드릴게요.")
            now = dt.datetime.now()
            if now.strftime("%H:%M") >= detail:
                # ponytail: 등록 처리(Claude 분류 등)에 걸리는 시간 동안 목표 시각이 이미 지나가버리는 레이스 대응 -> 오늘자는 바로 발송
                await message.channel.send(_build_daily_message())
                _sent_today[channel_id] = now.strftime("%Y-%m-%d")
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
        await message.channel.send(f"{format_header(pred)}\n{text}")


def _build_daily_message() -> str:
    pred = get_prediction()
    return f"{format_header(pred)}\n{generate_briefing(pred)}"


@tasks.loop(seconds=1)
async def check_schedule():
    now = dt.datetime.now()
    hhmm = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    for channel_id, target in _load_schedule().items():
        if _sent_today.get(channel_id) == today:
            continue

        # 정각 3분 전: 미리 브리핑을 만들어 캐시(정각에 지연 없이 보내기 위함)
        if hhmm == _minus_minutes(target, PREP_MINUTES) and _prepared.get(channel_id, (None,))[0] != today:
            _prepared[channel_id] = (today, _build_daily_message())
            print(f"[check_schedule] prepared for {channel_id}", flush=True)

        if hhmm == target:
            channel = client.get_channel(int(channel_id))
            if channel is None:
                print(f"[check_schedule] channel {channel_id} not found in cache!", flush=True)
                continue
            cached_date, cached_text = _prepared.get(channel_id, (None, None))
            text = cached_text if cached_date == today else _build_daily_message()  # 준비 못 했으면 그 자리에서 생성
            await channel.send(text)
            _sent_today[channel_id] = today
            print(f"[check_schedule] sent to {channel_id}", flush=True)


if __name__ == "__main__":
    client.run(os.environ["DISCORD_BOT_TOKEN"])
