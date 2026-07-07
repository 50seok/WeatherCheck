"""디스코드 대화형 봇: 날씨 질문에 RAG 브리핑 답장, 자연어로 알림 시간 설정, 채팅 정리, 도움말.
send_briefing(웹훅, 단방향)과 별개 — 이건 실시간으로 메시지를 들어야 해서 계속 실행 상태 유지 필요.
실행: python -m src.discord_chat_bot · 기능 목록은 HELP_TEXT 참고.
"""
import asyncio
import datetime as dt
import json
import os

import discord
from discord.ext import tasks
from dotenv import load_dotenv

from src.briefing import generate_briefing, generate_niche_briefing
from src.feedback import get_personal_offset, record_feedback, save_last_weather
from src.llm import chat as llm_chat
from src.ml import fetch_kma
from src.predictor import get_prediction, get_today_observed
from src.traffic import get_driving_eta, get_transit_eta

load_dotenv()

SCHEDULE_PATH = "data/schedule.json"
COMMUTE_PATH = "data/commute.json"
NICHE_PATH = "data/niche.json"
DEFAULT_CLEAR_COUNT = 50
PREP_MINUTES = 3  # 정각에 지연 없이 보내려고 이만큼 미리 브리핑을 만들어둠
COMMUTE_WEATHER_CAVEAT_KM = 20  # 서울-목적지 직선 아닌 실주행거리 근사치, 이 이상이면 타지역 가능성 경고
# ponytail: KMA ASOS 일자료(전날 확정 관측치)가 정확히 언제 배포되는지 검증된 출처가 없어서(예보 발표
# 시각 06/18시와는 다른 상품) 한 번의 추측 시각에 걸지 않고 하루 2번 체크. 재조회해도 날짜 기준 중복
# 제거(fetch_kma.append)라 여러 번 걸려도 부작용 없음 — 못 받았으면 다음 체크 때, 그래도 못 받았으면
# 다음날 자동으로 밀린 만큼 따라잡음(fetch_kma._default_range).
KMA_FETCH_TIMES = [dt.time(hour=6, minute=30), dt.time(hour=18, minute=30)]

HELP_TEXT = """🌤️ **출근 비서 봇 사용법**

**📅 날씨**
`오늘 날씨 어때?` · `내일 우산 필요해?`
→ 근거 문서 인용해서 답변 (오늘·내일만 가능)

**⏰ 알림**
`매일 아침 8시에 알려줘` · `1324로 설정해줘` (24시간제 4자리도 OK)
`알림 그만 받을래` → 알림 끄기

**🚗 출퇴근**
`강남역에서 서울역까지 얼마나 걸려?` → 소요시간 조회
`출근지 강남역에서 서울역으로 설정해줘` → 이후 알림에 자동 포함

**🚲 자전거 통근**
`자전거로 통근한다고 설정해줘` → 노면 상태·체감온도 반영, 자차/대중교통 시간은 생략
`니치 해제해줘` → 원래대로

**🧹 채팅 정리**
`메시지 정리해줘` (기본 50개) — 봇에 '메시지 관리' 권한 필요

**🥶👍🥵 체감 피드백**
알림 메시지 버튼 클릭 → 다음 브리핑부터 옷차림 조언에 반영

**❓ 도움말**
`뭐 할 수 있어?` · `명령어 알려줘`

👇 니치 설정·채팅 정리는 아래 버튼으로 바로 가능해요(채팅 안 쳐도 됨)."""

WEEKDAYS_KR = ["월", "화", "수", "목", "금", "토", "일"]


def format_header(prediction: dict) -> str:
    """디스코드 마크다운 헤더(#)로 날짜·요일을 크게 표시."""
    d = dt.datetime.strptime(prediction["date"], "%Y-%m-%d").date()
    today = dt.date.today()
    if d == today:
        label = "오늘"
    elif d == today + dt.timedelta(days=1):
        label = "내일"
    else:
        label = "최근 실측"  # ponytail: KMA 수집이 며칠 밀려서 관측 폴백이 오늘도 내일도 아닌 과거 날짜일 때
    return f"# {label} {d.isoformat()} ({WEEKDAYS_KR[d.weekday()]}요일)"


intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
_sent_today: dict[tuple[str, str], str] = {}  # (channel_id, target) -> date
_prepared: dict[tuple[str, str], tuple[str, tuple, str]] = {}  # (channel_id, target) -> (date, 준비 시점 설정 스냅샷, 미리 만들어둔 메시지)
_onboarded: set[str] = set()  # 채널별 최초 안내 패널 전송 여부(프로세스 생애주기 동안만 캐시 — 재시작 후 재검사되어도 핀이 이미 있으면 중복 전송 안 됨)


def _minus_minutes(hhmm: str, minutes: int) -> str:
    return (dt.datetime.strptime(hhmm, "%H:%M") - dt.timedelta(minutes=minutes)).strftime("%H:%M")


def _load_schedule() -> dict:
    """반환값: {channel_id: {"target": "HH:MM", "user_id": int|None}}.
    예전엔 값이 "HH:MM" 문자열이었어서(멘션 기능 추가 전) 그 포맷도 그대로 읽히게 변환."""
    if not os.path.exists(SCHEDULE_PATH):
        return {}
    with open(SCHEDULE_PATH, encoding="utf-8") as f:
        schedule = json.load(f)
    return {
        cid: (entry if isinstance(entry, dict) else {"target": entry, "user_id": None})
        for cid, entry in schedule.items()
    }


def _save_schedule(schedule: dict) -> None:
    os.makedirs(os.path.dirname(SCHEDULE_PATH), exist_ok=True)
    with open(SCHEDULE_PATH, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)


def _load_commute() -> dict:
    if os.path.exists(COMMUTE_PATH):
        with open(COMMUTE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_commute(commute: dict) -> None:
    os.makedirs(os.path.dirname(COMMUTE_PATH), exist_ok=True)
    with open(COMMUTE_PATH, "w", encoding="utf-8") as f:
        json.dump(commute, f, ensure_ascii=False, indent=2)


def _load_niche() -> dict:
    if os.path.exists(NICHE_PATH):
        with open(NICHE_PATH, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_niche(niche: dict) -> None:
    os.makedirs(os.path.dirname(NICHE_PATH), exist_ok=True)
    with open(NICHE_PATH, "w", encoding="utf-8") as f:
        json.dump(niche, f, ensure_ascii=False, indent=2)


def _settings_snapshot(channel_id: str) -> tuple:
    """니치/출근지 미리 만들어둔 브리핑이 발송 시점까지 유효한지 비교하기 위한 스냅샷.
    준비(정각 3분 전) 이후 설정이 바뀌면 캐시를 버리고 그 자리에서 다시 생성."""
    commute = _load_commute().get(channel_id)
    return (_load_niche().get(channel_id), commute["origin"] if commute else None, commute["destination"] if commute else None)


class SettingsView(discord.ui.View):
    """니치 설정·채팅 정리는 선택지가 정해져 있어 채팅 분류(Claude 호출) 대신 버튼으로 딸깍 처리.
    custom_id 고정 + timeout=None이라 봇 재시작 후에도(on_ready에서 add_view) 버튼이 계속 동작함."""

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🚲 자전거 통근", style=discord.ButtonStyle.primary, custom_id="niche_bike")
    async def set_bike(self, interaction: discord.Interaction, button: discord.ui.Button):
        niche = _load_niche()
        niche[str(interaction.channel_id)] = "bike"
        _save_niche(niche)
        await interaction.response.send_message(
            "🚲 자전거 통근으로 설정했어요. 노면 상태·체감온도까지 챙겨서 알려드려요.", ephemeral=True
        )

    @discord.ui.button(label="🚗 자동차·대중교통 (기본)", style=discord.ButtonStyle.secondary, custom_id="niche_default")
    async def set_default(self, interaction: discord.Interaction, button: discord.ui.Button):
        niche = _load_niche()
        channel_id = str(interaction.channel_id)
        if channel_id in niche:
            del niche[channel_id]
            _save_niche(niche)
        await interaction.response.send_message("🚗 자동차·대중교통 기본 모드로 설정했어요.", ephemeral=True)

    @discord.ui.button(label="🧹 채팅 정리", style=discord.ButtonStyle.danger, custom_id="clear_chat")
    async def clear_chat(self, interaction: discord.Interaction, button: discord.ui.Button):
        # ponytail: purge()가 3초 넘게 걸리면 응답 전 인터랙션 토큰이 만료돼 "Unknown interaction" 404가 남 -> 먼저 defer로 확인응답부터 하고 followup으로 결과 전송
        await interaction.response.defer(ephemeral=True)
        try:
            deleted = await interaction.channel.purge(limit=DEFAULT_CLEAR_COUNT, check=lambda m: not m.pinned)
            await interaction.followup.send(f"🧹 메시지 {len(deleted)}개 정리했어요.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send(
                "메시지를 지울 권한이 없어요. 봇 권한에 '메시지 관리(Manage Messages)'를 추가해주세요.", ephemeral=True
            )


class FeedbackView(discord.ui.View):
    """개인 체감 피드백 학습(PRD 4순위). 알림 뒤에 붙여서 클릭 한 번으로 그날 체감을 기록.
    쌓인 피드백은 src.feedback.get_personal_offset()으로 다음 브리핑 생성에 반영됨."""

    def __init__(self):
        super().__init__(timeout=None)

    async def _record(self, interaction: discord.Interaction, label: str):
        ok = record_feedback(str(interaction.channel_id), label)
        msg = "피드백 감사해요! 다음 브리핑부터 반영할게요 🙌" if ok else "이 채널엔 아직 발송된 브리핑이 없어서 기록 못 했어요."
        await interaction.response.send_message(msg, ephemeral=True)

    @discord.ui.button(label="🥶 추웠어", style=discord.ButtonStyle.primary, custom_id="feedback_cold")
    async def cold(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._record(interaction, "cold")

    @discord.ui.button(label="👍 딱 좋았어", style=discord.ButtonStyle.success, custom_id="feedback_good")
    async def good(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._record(interaction, "good")

    @discord.ui.button(label="🥵 더웠어", style=discord.ButtonStyle.danger, custom_id="feedback_hot")
    async def hot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._record(interaction, "hot")


async def _send_settings_panel(channel: discord.abc.Messageable) -> None:
    """도움말+설정 버튼 패널 전송. 채널에 이미 봇이 고정해둔 패널이 없으면 새로 핀 고정(채팅 정리해도 안 지워짐)."""
    sent = await channel.send(HELP_TEXT, view=SettingsView())
    try:
        already_pinned = False
        async for p in channel.pins():
            if p.author == client.user:
                already_pinned = True
                break
        if not already_pinned:
            await sent.pin()
    except discord.Forbidden:
        pass  # 핀 권한 없으면 그냥 일반 메시지로만 남음


def classify_message(text: str) -> tuple[str, str | None]:
    """메시지 의도를 분류. 키워드 매칭 대신 자연스러운 표현도 인식하도록 로컬 sLLM(EXAONE)에게 위임.

    반환: (intent, detail)
    intent: "weather_today" | "weather_tomorrow" | "weather_other" | "schedule" | "unschedule" | "traffic" | "commute" | "uncommute" | "niche" | "clear" | "help" | "none"
    detail: schedule일 땐 HH:MM(또는 None), clear일 땐 지울 개수(문자열 숫자, 없으면 None), niche일 땐 "BIKE"/"OFF", 그 외엔 None.
    """
    # ponytail: 메시지 전체가 숫자 4자리뿐이면("2015" 등) 시각인지 아닌지 LLM이 애매하게 판단할 수 있어
    # LLM 호출 전에 결정적으로 먼저 처리(속도도 빠르고 항상 일관됨).
    digits = text.strip().replace(":", "")
    if digits.isdigit() and len(digits) == 4:
        hh, mm = int(digits[:2]), int(digits[2:])
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return "schedule", f"{digits[:2]}:{digits[2:]}"

    prompt = (
        "디스코드 채널의 메시지 하나를 아래 중 정확히 하나로 분류해서, "
        "반드시 지정된 라벨로만 답해(다른 말 절대 하지 마):\n"
        "- 오늘 날씨/우산/옷차림을 묻거나, 날짜 언급 없이 그냥 날씨를 물으면 -> WEATHER_TODAY\n"
        "- 내일 날씨를 물으면 -> WEATHER_TOMORROW\n"
        "- 오늘·내일이 아닌 다른 날(특정 요일, 모레, 며칠 뒤 등)의 날씨를 물으면 -> WEATHER_OTHER\n"
        "- 정해진 시각에 알림/브리핑을 받고 싶다는 요청 -> SCHEDULE HH:MM"
        "(이 봇은 항상 '매일' 반복 알림만 지원하니, 메시지에 \"매일\"이라는 단어가 없어도 "
        "\"8시에 알려줘\", \"15시18분에 알려줘\", \"1518로 설정해줘\", \"알림설정 2019\", \"알람 0800\"처럼 "
        "조사(에/로) 없이 명령어와 시각이 붙어만 있어도 전부 SCHEDULE로 분류해. "
        "24시간제. \"1324\"처럼 콜론 없는 4자리 숫자로만 시각을 말해도 시각으로 인식해서 HH:MM으로 변환. "
        "시각이 명시 안 됐으면 HH:MM 자리에 NONE)\n"
        "- 매일 오던 알림을 그만 받고 싶다는 요청(취소/해지 등) -> UNSCHEDULE\n"
        "- 채팅/메시지를 정리·삭제해달라는 요청 -> CLEAR N"
        "(N은 지울 개수 숫자. 명시 안 됐으면 N 자리에 NONE)\n"
        "- 출발지에서 도착지까지 얼마나 걸리는지(자차/대중교통) 묻는 요청 -> TRAFFIC 출발지|도착지"
        "(장소명 두 개를 파이프(|)로 구분. 원문에 있는 글자를 하나도 빼거나 줄이지 말고 그대로 옮겨 적어(예: \"강남역\"이면 \"강남\"이 아니라 \"강남역\"). 둘 다 명시 안 됐으면 TRAFFIC NONE)\n"
        "- 본인 출근지(출발지-도착지)를 등록/설정해달라는 요청 -> COMMUTE 출발지|도착지"
        "(장소명 두 개를 파이프(|)로 구분. 원문에 있는 글자를 하나도 빼거나 줄이지 말고 그대로 옮겨 적어(예: \"강남역\"이면 \"강남\"이 아니라 \"강남역\"). 둘 다 명시 안 됐으면 COMMUTE NONE)\n"
        "- 등록해둔 출근지(출발지-도착지) 설정을 해제/취소하는 요청(\"출근지 해제\", \"출근지 설정 취소\" 등) -> UNCOMMUTE\n"
        "- '자전거'가 들어간 모드 설정/전환 요청 -> NICHE BIKE"
        "(\"자전거로 통근한다고 설정해줘\", \"자전거로 바꿔줘\", \"자전거로 변경해줘\", \"자전거 모드로 바꿔줘\" 등 표현과 무관하게 "
        "'자전거'만 언급되면 무조건 NICHE BIKE)\n"
        "- (출근지가 아니라) 니치 설정을 끄고 자동차·대중교통(기본) 모드로 되돌리는 요청 -> NICHE OFF"
        "(\"니치 해제\", \"자전거 통근 그만\" 뿐 아니라 \"자동차로 바꿔줘\", \"자동차 모드로 바꿔줘\", \"자동차로 변경해줘\", "
        "\"대중교통으로 바꿔줘\" 처럼 '자전거'가 아니라 '자동차'/'대중교통'/'기본'을 언급하며 모드 전환·변경을 요청해도 NICHE OFF)\n"
        "- 봇 사용법·도움말·명령어를 묻는 요청, 또는 봇이 뭘 할 수 있는지·무슨 기능이 있는지 묻는 요청 -> HELP"
        "(메시지가 \"기능\", \"명령어\", \"도움\", \"도움말\", \"help\", \"헬프\" 중 하나이거나 그 단어만 포함하면, "
        "다른 조건 다 무시하고 무조건 HELP로 답해. 예: \"뭐 할 수 있어?\"->HELP, \"기능 뭐 있어?\"->HELP, "
        "\"명령어 알려줘\"->HELP, \"기능\"->HELP, \"명령어\"->HELP, \"도움말\"->HELP)\n"
        "- 그 외 무관한 잡담 -> NONE\n\n"
        f"메시지: {text}"
    )
    result = llm_chat(prompt, temperature=0).strip()
    if result.startswith("SCHEDULE"):
        parts = result.split()
        hhmm = parts[1] if len(parts) > 1 else "NONE"
        digits = hhmm.replace(":", "")
        return "schedule", (f"{digits[:2]}:{digits[2:]}" if digits.isdigit() and len(digits) == 4 else None)
    if result.startswith("CLEAR"):
        parts = result.split()
        count = parts[1] if len(parts) > 1 else "NONE"
        return "clear", (count if count.isdigit() else None)
    if result.startswith("TRAFFIC"):
        rest = result[len("TRAFFIC"):].strip()
        return "traffic", (rest if "|" in rest else None)
    if result.startswith("COMMUTE"):
        rest = result[len("COMMUTE"):].strip()
        return "commute", (rest if "|" in rest else None)
    if result.startswith("NICHE"):
        rest = result[len("NICHE"):].strip()
        return "niche", ("BIKE" if rest == "BIKE" else "OFF")
    if result in ("WEATHER_TODAY", "WEATHER_TOMORROW", "WEATHER_OTHER", "HELP", "UNSCHEDULE", "UNCOMMUTE"):
        return result.lower(), None
    return "none", None


@tasks.loop(time=KMA_FETCH_TIMES)
async def fetch_daily_weather():
    """매일 정해진 시각에 KMA 최신 일자료를 받아 seoul_weather.csv에 이어붙임(재학습은 불필요, predictor가
    다음 호출부터 자동으로 최신 데이터를 씀). 실패해도 다음날 다시 시도하면서 밀린 기간까지 알아서 따라잡음."""
    try:
        start, end = fetch_kma._default_range()
        if start > end:
            return  # 이미 최신 상태
        df = await asyncio.to_thread(fetch_kma.fetch_range, start, end)
        if df.empty:
            print(f"[fetch_daily_weather] {start}~{end} 조회 결과 없음(아직 KMA 미배포 추정)", flush=True)
            return
        await asyncio.to_thread(fetch_kma.append, df)
        print(f"[fetch_daily_weather] appended {len(df)} rows ({start}~{end})", flush=True)
    except Exception as e:
        print(f"[fetch_daily_weather] failed: {e}", flush=True)


@client.event
async def on_ready():
    print(f"logged in as {client.user}")
    client.add_view(SettingsView())  # custom_id 고정 버튼이 재시작 후에도 계속 동작하도록 등록
    client.add_view(FeedbackView())
    check_schedule.start()
    fetch_daily_weather.start()


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return

    channel_id = str(message.channel.id)
    if channel_id not in _onboarded:
        _onboarded.add(channel_id)
        try:
            already_pinned = False
            async for p in message.channel.pins():
                if p.author == client.user:
                    already_pinned = True
                    break
            if not already_pinned:
                await _send_settings_panel(message.channel)
        except discord.Forbidden:
            pass  # 이 채널에서 메시지 전송/핀 권한이 없어도 아래 실제 메시지 처리는 계속 진행

    # ponytail: classify_message가 로컬 LLM을 동기 호출(수 초 소요) -> to_thread로 스레드에 위임해서
    # 그동안 이벤트 루프가 다른 메시지·하트비트 처리를 막지 않게 함
    intent, detail = await asyncio.to_thread(classify_message, message.content)
    print(f"[on_message] '{message.content}' -> intent={intent} detail={detail}", flush=True)

    if intent == "help":
        await _send_settings_panel(message.channel)
        return

    if intent == "clear":
        count = int(detail) if detail else DEFAULT_CLEAR_COUNT
        try:
            deleted = await message.channel.purge(limit=count + 1, check=lambda m: not m.pinned)  # +1: 요청 메시지 자신 포함, 핀 고정된 설정 패널은 보존
            notice = await message.channel.send(f"🧹 메시지 {len(deleted) - 1}개 정리했어요.")
            await notice.delete(delay=3)
        except discord.Forbidden:
            await message.channel.send("메시지를 지울 권한이 없어요. 봇 권한에 '메시지 관리(Manage Messages)'를 추가해주세요.")
        return

    if intent == "schedule":
        if detail:
            channel_id = str(message.channel.id)
            schedule = _load_schedule()
            schedule[channel_id] = {"target": detail, "user_id": message.author.id}
            _save_schedule(schedule)
            already_passed = dt.datetime.now().strftime("%H:%M") >= detail
            when = "내일부터 매일" if already_passed else "매일"
            await message.channel.send(f"✅ {when} {detail}에 이 채널로 브리핑을 보내드릴게요. (@{message.author.display_name}님께 알림 멘션도 같이 갈게요)")
        else:
            await message.channel.send("몇 시에 보내드릴까요? 예: '아침 8시에 알려줘'")
        return

    if intent == "unschedule":
        channel_id = str(message.channel.id)
        schedule = _load_schedule()
        if channel_id in schedule:
            del schedule[channel_id]
            _save_schedule(schedule)
            await message.channel.send("🔕 이 채널 알림을 껐어요.")
        else:
            await message.channel.send("이 채널엔 설정된 알림이 없어요.")
        return

    if intent == "commute":
        if not detail:
            await message.channel.send("출근 출발지랑 도착지를 알려주세요. 예: '출근지 강남역에서 서울역으로 설정해줘'")
            return
        origin, destination = detail.split("|", 1)
        commute = _load_commute()
        commute[str(message.channel.id)] = {"origin": origin, "destination": destination}
        _save_commute(commute)
        await message.channel.send(f"✅ 출근지를 **{origin} → {destination}**로 설정했어요. 이제 알림에 출퇴근 소요시간도 같이 보내드려요.")
        return

    if intent == "uncommute":
        channel_id = str(message.channel.id)
        commute = _load_commute()
        if channel_id in commute:
            del commute[channel_id]
            _save_commute(commute)
            await message.channel.send("🚗 출근지 설정을 해제했어요. 이제 알림에 출퇴근 소요시간은 안 보내드려요.")
        else:
            await message.channel.send("설정된 출근지가 없어요.")
        return

    if intent == "niche":
        channel_id = str(message.channel.id)
        niche = _load_niche()
        if detail == "BIKE":
            niche[channel_id] = "bike"
            _save_niche(niche)
            await message.channel.send("🚲 자전거 통근으로 설정했어요. 이제 노면 상태·체감온도까지 챙겨서 알려드려요.")
        else:
            if channel_id in niche:
                del niche[channel_id]
                _save_niche(niche)
            await message.channel.send("니치 설정을 해제했어요.")
        return

    if intent == "traffic":
        if not detail:
            await message.channel.send("출발지랑 도착지를 알려주세요. 예: '강남역에서 서울역까지 얼마나 걸려?'")
            return
        origin, destination = detail.split("|", 1)
        async with message.channel.typing():
            try:
                driving = await asyncio.to_thread(get_driving_eta, origin, destination)
                transit = await asyncio.to_thread(get_transit_eta, origin, destination)
            except Exception:
                await message.channel.send(f"'{origin}' 또는 '{destination}' 경로를 못 찾았어요. 정확한 장소명으로 다시 말씀해주세요.")
                return
        await message.channel.send(
            f"🚗 **{origin} → {destination}**\n"
            f"자차: 약 {driving['minutes']}분 ({driving['distance_km']}km)\n"
            f"대중교통: 약 {transit['minutes']}분 (환승 {transit['transfers']}회)"
            if transit.get("minutes") is not None
            else f"🚗 **{origin} → {destination}**\n자차: 약 {driving['minutes']}분 ({driving['distance_km']}km)\n대중교통: 경로를 찾지 못했어요."
        )
        return

    if intent == "weather_other":
        await message.channel.send("죄송해요, 지금은 오늘·내일 날씨만 예측할 수 있어요. 더 먼 미래는 아직 지원하지 않아요 🙏")
        return

    if intent in ("weather_today", "weather_tomorrow"):
        async with message.channel.typing():
            pred = await asyncio.to_thread(get_today_observed if intent == "weather_today" else get_prediction)
            briefing = await asyncio.to_thread(generate_briefing, pred)
            parts = [format_header(pred), f"🌤️ **날씨**\n{briefing}"]
        await message.channel.send("\n\n".join(parts))  # ponytail: 자전거/자동차 통근 정보는 예약 브리핑 전용 — 채팅 질문 응답엔 안 붙임


def _build_daily_message(channel_id: str) -> str:
    """날씨 브리핑 + (출근지 설정돼 있으면) 출퇴근 소요시간을 혼동 없이 구분된 섹션으로 합쳐서 반환.
    자전거 니치는 자차/대중교통 시간이 무의미해서 그 섹션은 생략(니치 해제 시 다시 표시)."""
    pred = get_prediction()  # 예약 알림은 항상 "내일" 예측(채팅으로 직접 "오늘 날씨" 물어볼 때만 get_today_observed 사용)
    save_last_weather(channel_id, pred)  # 피드백 버튼이 "그날 날씨"를 알 수 있도록 기록
    niche = _load_niche().get(channel_id)
    personal_offset = get_personal_offset(channel_id)
    parts = [format_header(pred), f"🌤️ **날씨**\n{generate_briefing(pred, personal_offset)}"]
    if niche:
        parts.append(f"🚲 **자전거 통근 체크**\n{generate_niche_briefing(pred, niche)}")

    commute = _load_commute().get(channel_id)
    if commute and niche != "bike":
        origin, destination = commute["origin"], commute["destination"]
        try:
            driving = get_driving_eta(origin, destination)
            transit = get_transit_eta(origin, destination)
            transit_line = (
                f"대중교통: 약 {transit['minutes']}분 (환승 {transit['transfers']}회)"
                if transit.get("minutes") is not None else "대중교통: 경로를 찾지 못했어요."
            )
            commute_text = (
                f"🚗 **출근길** ({origin} → {destination})\n"
                f"자차: 약 {driving['minutes']}분 ({driving['distance_km']}km)\n{transit_line}"
            )
            # ponytail: 서울 108지점 단일 모델의 한계 — 정확한 행정구역 판별 대신 거리로만 근사
            if driving["distance_km"] > COMMUTE_WEATHER_CAVEAT_KM:
                commute_text += (
                    f"\n⚠️ 날씨 예측은 서울(기상청 108지점) 기준이라 목적지({destination})의 "
                    "실제 날씨와 다를 수 있어요."
                )
            parts.append(commute_text)
        except Exception:
            parts.append(f"🚗 **출근길** ({origin} → {destination})\n조회 실패 — 장소명을 다시 확인해주세요.")

    return "\n\n".join(parts)


@tasks.loop(seconds=1)
async def check_schedule():
    now = dt.datetime.now()
    hhmm = now.strftime("%H:%M")
    today = now.strftime("%Y-%m-%d")
    for channel_id, entry in _load_schedule().items():
        target, user_id = entry["target"], entry["user_id"]
        key = (channel_id, target)
        if _sent_today.get(key) == today:
            continue

        # 정각 3분 전: 미리 브리핑을 만들어 캐시(정각에 지연 없이 보내기 위함)
        if hhmm == _minus_minutes(target, PREP_MINUTES) and _prepared.get(key, (None,))[0] != today:
            # ponytail: LSTM 추론+RAG+LLM 생성이 수 초~십수 초 걸려서(동기 호출) to_thread로 위임 안 하면
            # 이 채널 브리핑 만드는 동안 다른 채널 체크·메시지 응답이 전부 멈춤
            text = await asyncio.to_thread(_build_daily_message, channel_id)
            _prepared[key] = (today, _settings_snapshot(channel_id), text)
            print(f"[check_schedule] prepared for {key}", flush=True)

        if hhmm == target:
            channel = client.get_channel(int(channel_id))
            if channel is None:
                print(f"[check_schedule] channel {channel_id} not found in cache!", flush=True)
                continue
            cached_date, cached_snapshot, cached_text = _prepared.get(key, (None, None, None))
            # 준비 못 했거나, 준비 이후 니치/출근지 설정이 바뀌었으면 캐시를 버리고 그 자리에서 다시 생성
            if cached_date == today and cached_snapshot == _settings_snapshot(channel_id):
                text = cached_text
            else:
                text = await asyncio.to_thread(_build_daily_message, channel_id)
            mention = f"<@{user_id}>\n" if user_id else ""
            await channel.send(mention + text, view=FeedbackView())
            _sent_today[key] = today
            print(f"[check_schedule] sent to {key}", flush=True)


if __name__ == "__main__":
    client.run(os.environ["DISCORD_BOT_TOKEN"])
