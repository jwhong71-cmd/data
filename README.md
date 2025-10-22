# Streamlit 날씨 웹 (OpenWeather)

간단한 스트림릿 기반 날씨 웹 앱입니다. OpenWeather API를 사용해 도시의 현재 날씨를 보여줍니다.

## 준비 사항

- Python 3.9 이상
- OpenWeather API 키 (예: https://openweathermap.org/ 에서 발급)

## 설치

1) 패키지 설치

```
pip install -r requirements.txt
```

2) API 키 설정 (둘 중 하나를 선택)

- 방법 A: Streamlit Secrets 사용 권장
	- `.streamlit/secrets.toml` 파일을 만들고 아래와 같이 작성
	- 절대 깃에 커밋하지 마세요. 이 레포에는 `.gitignore`로 제외되어 있습니다.

```
[general]
OPENWEATHER_API_KEY = "여기에_발급_키를_입력"
```

- 방법 B: 환경 변수 사용
	- Windows PowerShell (세션 한정):

```
$env:OPENWEATHER_API_KEY = "여기에_발급_키를_입력"
```

## 실행

```
streamlit run streamlit_app.py
```

브라우저가 열리면 도시, 단위(섭씨/화씨), 언어(한국어/영어)를 선택해 조회할 수 있습니다.

## 구조

- `streamlit_app.py` — Streamlit UI 및 앱 엔트리포인트
- `weather_client.py` — OpenWeather API 클라이언트 래퍼
- `.streamlit/secrets.toml.example` — Secrets 예시 파일 (실제 키는 `secrets.toml`에 설정)
- `requirements.txt` — 의존성 목록
- `.gitignore` — 비밀/캐시 파일 제외 설정

## 참고

- 제공하신 API 키는 코드에 하드코딩하지 않고 Secrets/환경변수로 읽습니다.
- API 사용량(쿼ota)을 고려해 캐시가 적용됩니다(기본 5분).