from __future__ import annotations

import os
from datetime import datetime, timezone

import streamlit as st
import pandas as pd
import altair as alt

from weather_client import (
    OpenWeatherClient,
    get_icon_url,
    choose_units_for_country,
)

# 페이지 설정
st.set_page_config(page_title="날씨 웹", page_icon="🌤️", layout="centered")

st.title("🌤️ 간단 날씨 웹")
st.caption("OpenWeather API + Streamlit")


def _read_api_key() -> str:
    # 1) Streamlit secrets 우선 (top-level 또는 [general] 지원)
    api_key = None
    try:
        if "OPENWEATHER_API_KEY" in st.secrets:
            api_key = st.secrets["OPENWEATHER_API_KEY"]
        elif "general" in st.secrets and "OPENWEATHER_API_KEY" in st.secrets["general"]:
            api_key = st.secrets["general"]["OPENWEATHER_API_KEY"]
    except Exception:
        api_key = None

    # 2) 환경 변수로 대체
    if not api_key:
        api_key = os.getenv("OPENWEATHER_API_KEY")

    return api_key or ""


def icon_to_emoji(code: str | None) -> str:
    """OpenWeather 아이콘 코드를 이모지로 매핑합니다."""
    if not code:
        return ""
    prefix = code[:2]
    mapping = {
        "01": "☀️" if code.endswith("d") else "🌙",
        "02": "🌤️" if code.endswith("d") else "☁️",
        "03": "☁️",
        "04": "☁️",
        "09": "🌧️",
        "10": "🌧️",
        "11": "⛈️",
        "13": "❄️",
        "50": "🌫️",
    }
    return mapping.get(prefix, "")


@st.cache_data(ttl=300)
def fetch_current_weather(city: str, units: str, lang: str, api_key: str):
    """도시명을 지오코딩으로 좌표로 변환한 뒤, 좌표 기반으로 현재 날씨를 조회합니다.

    한국어/다국어 도시명도 안정적으로 처리됩니다.
    """
    client = OpenWeatherClient(api_key=api_key)
    loc = client.resolve_city_to_coords(city=city, lang=lang)
    if loc and "lat" in loc and "lon" in loc:
        data = client.get_current_weather_by_coords(
            lat=loc["lat"], lon=loc["lon"], units=units, lang=lang
        )
        # 조회된 공식 도시/국가명을 덮어써서 표시를 개선
        if "name" in loc:
            data["name"] = loc.get("local_names", {}).get(lang, loc["name"]) or loc["name"]
        if "country" in loc:
            data.setdefault("sys", {})["country"] = loc["country"]
        return data
    # 지오코딩 실패 시 기존 q 파라미터 방식으로 폴백
    return OpenWeatherClient(api_key=api_key).get_current_weather(
        city=city, units=units, lang=lang
    )


@st.cache_data(ttl=86400)
def resolve_loc(city: str, lang: str, api_key: str):
    client = OpenWeatherClient(api_key=api_key)
    return client.resolve_city_to_coords(city=city, lang=lang)


with st.sidebar:
    st.subheader("설정")
    city = st.text_input("도시 이름", value="Seoul", placeholder="예: Seoul, Busan, Tokyo, New York")

    unit_pref = st.selectbox(
        "온도 단위",
        options=["자동(위치 기준)", "섭씨 (°C)", "화씨 (°F)"],
        index=0,
        help="자동: 국가코드에 따라 US/LR/MM은 화씨, 나머지는 섭씨",
    )

    lang_label = st.selectbox("언어", options=["한국어", "English"], index=0)
    lang = "kr" if lang_label == "한국어" else "en"

    st.markdown("---")
    st.caption("API 키는 Secrets 또는 환경변수에서 자동으로 읽습니다.")


api_key = _read_api_key()
if not api_key:
    st.warning(
        "API 키가 설정되어 있지 않습니다. .streamlit/secrets.toml 또는 환경변수 OPENWEATHER_API_KEY를 설정하세요.",
        icon="⚠️",
    )

colL, colR = st.columns([1, 1])
with colL:
    st.write("도시:", f"**{city or '—'}**")
with colR:
    st.write("단위 설정:", f"**{unit_pref}** / 언어: **{lang_label}**")

st.markdown("---")

if city.strip() and api_key:
    try:
        # 1) 위치 해석 및 단위 결정
        loc = resolve_loc(city=city.strip(), lang=lang, api_key=api_key)
        if not loc:
            st.error("도시를 찾을 수 없습니다. 다른 표기(영문/현지어)로 시도해 보세요.")
            st.stop()

        auto_units = choose_units_for_country(loc.get("country"))
        units = (
            "metric" if "섭씨" in unit_pref else "imperial" if "화씨" in unit_pref else auto_units
        )

        # 2) 현재 날씨
        data = fetch_current_weather(city=city.strip(), units=units, lang=lang, api_key=api_key)

        # 기본 필드
        name = data.get("name", city)
        sys = data.get("sys", {})
        country = sys.get("country", "")
        weather_list = data.get("weather", [])
        main = data.get("main", {})
        wind = data.get("wind", {})

        # 헤더: 도시, 국가, 설명 + 아이콘
        description = weather_list[0].get("description") if weather_list else None
        icon = weather_list[0].get("icon") if weather_list else None

        header_cols = st.columns([1, 3])
        with header_cols[0]:
            if icon:
                st.image(get_icon_url(icon), width=100)
        with header_cols[1]:
            title_text = f"{name}{', ' + country if country else ''}"
            st.subheader(title_text)
            if description:
                st.write(description.capitalize())

        # 메트릭
        t = main.get("temp")
        feels = main.get("feels_like")
        hum = main.get("humidity")
        pres = main.get("pressure")
        ws = wind.get("speed")

        unit_symbol = "°C" if units == "metric" else "°F"
        wind_unit = "m/s" if units == "metric" else "mph"

        m1, m2, m3 = st.columns(3)
        m1.metric("현재 기온", f"{t:.1f}{unit_symbol}" if t is not None else "—")
        m2.metric("체감 온도", f"{feels:.1f}{unit_symbol}" if feels is not None else "—")
        m3.metric("습도", f"{hum}%" if hum is not None else "—")

        m4, m5 = st.columns(2)
        m4.metric("바람", f"{ws} {wind_unit}" if ws is not None else "—")
        m5.metric("기압", f"{pres} hPa" if pres is not None else "—")

        # 부가 정보: 일출/일몰
        sunrise = sys.get("sunrise")
        sunset = sys.get("sunset")
        tz = data.get("timezone", 0)  # seconds offset from UTC

        def fmt_ts(ts: int | None) -> str:
            if not ts:
                return "—"
            # OpenWeather는 UTC 타임스탬프 + timezone 오프셋 제공
            dt = datetime.fromtimestamp(ts + tz, tz=timezone.utc)
            return dt.strftime("%Y-%m-%d %H:%M")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.write("일출:", fmt_ts(sunrise))
        with c2:
            st.write("일몰:", fmt_ts(sunset))

        # 시간대별 예보 (3시간 간격)
        client = OpenWeatherClient(api_key=api_key)
        forecast = client.get_forecast_by_coords(
            lat=loc["lat"], lon=loc["lon"], units=units, lang=lang
        )
        f_list = forecast.get("list", [])
        city_meta = forecast.get("city", {})
        tz = city_meta.get("timezone", tz)

        rows = []
        for itm in f_list[:16]:  # 약 48시간(3h*16) 중 첫 16개
            dt_val = itm.get("dt")
            main_f = itm.get("main", {})
            wind_f = itm.get("wind", {})
            pop = itm.get("pop", 0)
            wlist = itm.get("weather", [])
            w0 = wlist[0] if wlist else {}
            icon_code = w0.get("icon")
            desc_f = w0.get("description")
            local_dt = datetime.fromtimestamp((dt_val or 0) + tz, tz=timezone.utc)
            rows.append(
                {
                    "시간": local_dt,
                    "기온": main_f.get("temp"),
                    "체감": main_f.get("feels_like"),
                    "습도%": main_f.get("humidity"),
                    "바람": wind_f.get("speed"),
                    "강수확률": pop * 100,
                    "아이콘": get_icon_url(icon_code) if icon_code else None,
                    "심볼": icon_to_emoji(icon_code),
                    "설명": desc_f,
                }
            )

        if rows:
            df = pd.DataFrame(rows).set_index("시간")
            st.subheader("시간대별 예보 (3시간 간격)")

            # Altair로 이모지 아이콘이 오버레이된 온도 라인 차트 생성
            df_reset = df.reset_index()
            base = alt.Chart(df_reset).encode(
                x=alt.X("시간:T", axis=alt.Axis(title=None)),
                tooltip=[
                    "시간:T",
                    alt.Tooltip("기온:Q", format=".1f"),
                    alt.Tooltip("체감:Q", format=".1f"),
                    "설명:N",
                ],
            )

            line_temp = base.mark_line(color="#4dabf7", strokeWidth=2).encode(
                y=alt.Y("기온:Q", axis=alt.Axis(title="온도"))
            )
            line_feels = (
                base.mark_line(color="#74c0fc", strokeDash=[4, 2], strokeWidth=1.5).encode(y="체감:Q")
            )
            # 이모지 텍스트를 온도 라인 위에 표시
            icons_text = base.mark_text(size=16, dy=-10).encode(y="기온:Q", text="심볼:N")
            chart = alt.layer(line_temp, line_feels, icons_text).resolve_scale(y="shared")
            st.altair_chart(chart, use_container_width=True)

            st.bar_chart(df[["강수확률"]])
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "아이콘": st.column_config.ImageColumn("아이콘", width="small"),
                },
            )

        # 원시 데이터 토글
        with st.expander("원시 데이터 보기"):
            st.write("현재 날씨")
            st.json(data)
            st.write("예보")
            st.json(forecast)

    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
elif not city.strip():
    st.info("도시 이름을 입력하세요.")

st.markdown("\n")
st.caption("© Streamlit Weather Demo. OpenWeather 데이터를 사용합니다.")
