"""Streamlit 데모: 슬라이더 입력 -> 내일 날씨 예측 (Phase 1 ML) + LSTM 비교 (Phase 2 DL)."""
import streamlit as st

from src.briefing import generate_briefing
from src.dl.predict import load_models as load_dl_models
from src.dl.predict import predict_tomorrow as predict_dl
from src.feedback import LABEL_OFFSET, get_personal_offset
from src.ml.predict import predict_tomorrow, train_all
from src.seed_feedback import DUMMY_ENTRIES

st.set_page_config(page_title="출근 비서 — 내일 날씨 예측", page_icon="🌤️")
st.title("🌤️ 출근 비서 — 내일 날씨 예측 (Phase 1 ML → Phase 2 DL → Phase 3 LLM+RAG)")
st.caption("오늘 날씨를 입력하면 LinearRegression/RandomForest/XGBoost 중 가장 성능 좋은 모델로 내일을 예측합니다.")


@st.cache_resource
def get_models():
    return train_all()


@st.cache_resource
def get_dl_models():
    return load_dl_models()


models = get_models()

with st.sidebar:
    st.header("오늘 날씨 입력")
    with st.form("weather_input"):
        temp_avg = st.slider("평균 기온(°C)", -15.0, 35.0, 15.0, 0.5)
        temp_max = st.slider("최고 기온(°C)", -10.0, 40.0, 20.0, 0.5)
        temp_min = st.slider("최저 기온(°C)", -20.0, 30.0, 10.0, 0.5)
        humidity = st.slider("습도(%)", 0, 100, 60)
        pressure = st.slider("기압(hPa)", 990.0, 1035.0, 1013.0, 0.5)
        wind_speed = st.slider("풍속(m/s)", 0.0, 15.0, 2.5, 0.5)
        precip_yesterday = st.slider("어제 강수량(mm)", 0.0, 100.0, 0.0, 0.5)
        st.form_submit_button("🔍 예측하기", use_container_width=True)

result = predict_tomorrow(
    models, temp_avg, temp_max, temp_min, humidity, pressure, wind_speed, precip_yesterday
)

col1, col2, col3 = st.columns(3)
col1.metric("내일 최고기온", f"{result['temp_max']}°C")
col2.metric("내일 최저기온", f"{result['temp_min']}°C")
col3.metric("강수 확률", f"{result['rain_prob'] * 100:.0f}%")
st.caption(f"예측일: {result['date']} · 모델: {result['source']}")

st.divider()
st.subheader("모델 성능 비교 (ML 3종)")
c1, c2 = st.columns(2)
with c1:
    st.write("**회귀 (내일 최고기온 MAE, °C)**")
    st.bar_chart(models["reg_scores"])
with c2:
    st.write("**분류 (내일 비 여부 Accuracy)**")
    st.bar_chart(models["clf_scores"])

st.divider()
st.subheader("🧠 Phase 2: LSTM 예측")
st.caption("ML은 위 슬라이더 입력을 쓰지만, LSTM은 최근 7일 데이터의 시계열 패턴으로 예측합니다(입력 불필요).")
dl_result = predict_dl(get_dl_models())
d1, d2, d3 = st.columns(3)
d1.metric("내일 최고기온 (LSTM)", f"{dl_result['temp_max']}°C")
d2.metric("내일 최저기온 (LSTM)", f"{dl_result['temp_min']}°C")
d3.metric("강수 확률 (LSTM)", f"{dl_result['rain_prob'] * 100:.0f}%")

st.write("**ML vs DL — 내일 최고기온 MAE 비교 (낮을수록 좋음)**")
st.image("notebooks/figures/ml_vs_dl.png")

st.divider()
st.subheader("🤖 Phase 3: LLM+RAG 브리핑 · 개인 체감 피드백 (프로젝트 시그니처)")
st.caption(
    "실제 서비스는 디스코드 봇으로 매일 아침 자동 발송됩니다(로컬 Ollama+RAG 필요). "
    "여기서는 그 파이프라인의 실제 산출물을 보여드립니다."
)

DEMO_CHANNEL_ID = "1522486289356689474"

personal_offset = get_personal_offset(DEMO_CHANNEL_ID)
if personal_offset is not None:
    offset_note = "실제 디스코드 채널 누적 피드백 기준"
else:
    # ponytail: data/feedback.json은 gitignore돼서 Cloud엔 없음 -> 로직은 동일하게 재사용, 데모용 더미로만 대체
    personal_offset = round(sum(LABEL_OFFSET[e["feedback"]] for e in DUMMY_ENTRIES) / len(DUMMY_ENTRIES), 1)
    offset_note = f"seed_feedback.py 더미 시나리오 {len(DUMMY_ENTRIES)}건 기준 (로컬 실사용 데이터 없음)"

try:
    briefing_text = generate_briefing(dl_result, personal_offset=personal_offset)
    briefing_note = "위 LSTM 예측값으로 지금 막 생성한 실시간 브리핑"
except Exception:
    # ponytail: Streamlit Cloud엔 Ollama가 없어 실시간 생성이 안 됨 -> 로컬에서 미리 캡처한 실제 산출물로 대체
    briefing_text = (
        "내일 서울의 날씨는 최고 28.7°C로 덥지만, 최저 20.5°C로 낮아지면서 체감온도 차이가 크겠네요. "
        "[일교차_옷차림지수]에 따르면, 일교차가 8~10도로 겉옷 하나는 꼭 챙기세요. 특히 체감온도가 약 1.5°C 더 "
        "낮게 느껴지시는 편이라면, 얇은 가디건이나 바람막이를 추가로 준비하시는 게 좋을 것 같아요 💪✨. "
        "자외선 지수도 보통 수준이므로 낮 시간 외출 시에는 자외선 차단제를 챙기는 것도 잊지 마세요! 🌞😎"
    )
    briefing_note = "로컬 Ollama+RAG로 생성했던 실제 산출물 캡처본 (Cloud엔 Ollama 미실행이라 실시간 생성 대신 표시)"

st.info(briefing_text)
st.caption(f"근거 문서는 [대괄호]로 인용 · {briefing_note}")
st.write(f"**개인 체감 보정치**: {personal_offset:+.1f}°C · {offset_note}")
