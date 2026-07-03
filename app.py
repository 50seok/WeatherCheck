"""Phase 1 Streamlit 데모: 슬라이더 입력 -> 내일 날씨 예측."""
import streamlit as st

from src.ml.predict import predict_tomorrow, train_all

st.set_page_config(page_title="출근 비서 — 내일 날씨 예측", page_icon="🌤️")
st.title("🌤️ 출근 비서 — 내일 날씨 예측 (Phase 1: ML)")
st.caption("오늘 날씨를 입력하면 LinearRegression/RandomForest/XGBoost 중 가장 성능 좋은 모델로 내일을 예측합니다.")


@st.cache_resource
def get_models():
    return train_all()


models = get_models()

with st.sidebar:
    st.header("오늘 날씨 입력")
    temp_avg = st.slider("평균 기온(°C)", -15.0, 35.0, 15.0, 0.5)
    temp_max = st.slider("최고 기온(°C)", -10.0, 40.0, 20.0, 0.5)
    temp_min = st.slider("최저 기온(°C)", -20.0, 30.0, 10.0, 0.5)
    humidity = st.slider("습도(%)", 0, 100, 60)
    pressure = st.slider("기압(hPa)", 990.0, 1035.0, 1013.0, 0.5)
    wind_speed = st.slider("풍속(m/s)", 0.0, 15.0, 2.5, 0.5)
    precip_yesterday = st.slider("어제 강수량(mm)", 0.0, 100.0, 0.0, 0.5)

result = predict_tomorrow(
    models, temp_avg, temp_max, temp_min, humidity, pressure, wind_speed, precip_yesterday
)

col1, col2, col3 = st.columns(3)
col1.metric("내일 최고기온", f"{result['temp_max']}°C")
col2.metric("내일 최저기온", f"{result['temp_min']}°C")
col3.metric("강수 확률", f"{result['rain_prob'] * 100:.0f}%")
st.caption(f"예측일: {result['date']} · 모델: {result['source']}")

st.divider()
st.subheader("모델 성능 비교")
c1, c2 = st.columns(2)
with c1:
    st.write("**회귀 (내일 최고기온 MAE, °C)**")
    st.bar_chart(models["reg_scores"])
with c2:
    st.write("**분류 (내일 비 여부 Accuracy)**")
    st.bar_chart(models["clf_scores"])
