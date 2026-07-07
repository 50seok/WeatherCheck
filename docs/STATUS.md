# STATUS — WeatherCheck

> 갱신: 2026-07-07(발표 완료 후) · **마감: 2026-07-07(월) 09:00 제출(프로젝트+보고서)** — 제출·발표 완료
> GitHub: https://github.com/50seok/WeatherCheck (private)

## 진행 체크리스트
- [x] 골격 초기화 (git·디렉토리·CLAUDE.md·contract.md) — 7/3
- [x] GitHub 레포 생성·푸시, Track B 워크트리 생성 — 7/3
- [x] **Phase 1 ML** (7/3): EDA → 모델 3개 비교(LR/RF/XGB) → Streamlit v1 완료 (실데이터로 교체, 아래 이슈 참고)
- [x] **Phase 2 DL** (7/3): LSTM 학습 → ML vs DL 비교 그래프 → Streamlit v2 완료
- [x] **Phase 3 LLM+RAG 골격** (7/3, Track B): knowledge 문서 6개 → Chroma 인덱싱 → mock 기반 근거 인용 브리핑 함수 → 디스코드 웹훅(실동작 검증 완료)
- [x] **Phase 3 통합** (7/3): Track A 실제 예측 함수(LSTM)로 mock 교체, 디스코드 자동 발송 확인 완료
- [x] **발표자료** (7/3): `docs/WeatherCheck_발표자료.pptx` — 개요 + Phase 1/2/3 단계별 5장 + 마무리, 총 18장
- [ ] **Streamlit Cloud 배포** — 사용자가 진행 중(GitHub 계정 연동 필요). 두 가지 이슈 발견·해결:
  1. Cloud 기본 Python 3.14에 tensorflow wheel 없어 설치 실패 → `.python-version`으로 3.13 고정 (7/4)
  2. 모델·데이터 파일 gitignore돼서 배포 때마다 LSTM 재학습 발생 → 로딩 지연 원인. 용량이 450KB 미만이라 그냥 git에 커밋(`data/raw/seoul_weather.csv`, `src/dl/models/lstm_model.keras`, `notebooks/figures/*.png`)해서 재학습 자체를 없앰 (7/4)
- 데모 영상: 생략 결정 (7/3)
- **PRD 차별화 우선순위 진행** (7/4): 1순위 교통 결합 → 2순위 출근지 설정 → 3순위 니치 타겟(자전거 통근) → 4순위 개인 체감 피드백까지 **전부 구현 완료**.
  1. 교통 결합: TMAP(자차 경로)·ODsay(대중교통 경로) API 연동, 디스코드 채팅으로 출발지/도착지 매번 입력받는 방식(`src/traffic.py`)
  2. 출근지 설정: 출발지/도착지를 한 번 등록해두면 이후 알림에 날씨+출퇴근 소요시간을 같이 보내줌(`data/commute.json`, gitignore)
  3. 니치 타겟: PRD가 예시로 든 자전거 통근족 하나만 우선 구현(1인 비서 취지상 다중 니치 불필요 판단) — 니치 전용 지식 문서(`data/knowledge/niche/자전거통근_노면가이드.md`) 추가, 디스코드 채팅 또는 버튼으로 "자전거"/"자동차·대중교통(기본)" 토글(`data/niche.json`, gitignore)
  - 참고: 1/2순위는 API 값을 그대로 전달하는 구조라 LLM/RAG와는 무관 — RAG가 실제로 개입하는 건 날씨 브리핑(`generate_briefing`)과 3순위 니치 조언(`generate_niche_briefing`)뿐.
- **사용성 개선 후속 작업** (7/4 오후, 사용자 피드백 기반):
  1. 출근지 해제 기능 부재로 "출근지 설정 해제해줘"가 니치 해제로 잘못 분류되던 버그 수정 → `UNCOMMUTE` 인텐트 분리 추가
  2. 자전거 니치일 땐 자차/대중교통 시간이 무의미해서 자동 알림에서 그 섹션 생략(니치 해제 시 복원, `commute.json` 데이터 자체는 안 지워짐)
  3. 니치 조언이 날씨 문장 끝에 묻혀 안 보이던 문제 → 🚲 전용 섹션으로 분리. 겸사겸사 발견: 니치 문서가 일반 지식 폴더에 같이 있어 TF-IDF 검색(문서 수 적어 top-3 오검색)이 니치 미설정 사용자에게도 자전거 조언을 섞어 넣던 버그 → `data/knowledge/niche/`로 분리, 니치 조언은 검색 없이 문서 1:1 직접 읽기로 변경
  4. 알림 시각을 "1324"처럼 콜론 없는 24시간제 4자리 숫자로도 설정 가능하게 파싱 보강
  5. 니치 설정(자전거/기본)·채팅 정리를 자연어 대신 버튼(discord.ui.View)으로도 가능하게 추가 — Claude 분류 호출 없이 즉시 처리. 도움말 요청 시 버튼 패널을 채널에 자동 핀 고정(채팅 정리해도 안 지워짐)
  - 초대 링크: `https://discord.com/oauth2/authorize?client_id=1522624990674026656&permissions=75776&scope=bot` (Send Messages+Manage Messages+Read Message History, 토큰과 client_id 일치 확인 완료)
  6. 정각 3분 전 미리 만든(prep-cache) 브리핑이 그 사이 니치/출근지 설정 변경을 못 반영하던 버그 수정 — 준비 시점 설정을 스냅샷으로 저장해두고 발송 시점에 바뀌었으면 캐시 버리고 재생성
  7. 알림 발송 시 사용자를 `@멘션`으로 태그 — 일반 메시지는 디스코드 알림 설정(멘션만 등)에 따라 푸시알림이 안 올 수 있어서. `schedule.json`에 `user_id` 같이 저장(예전 문자열 포맷도 호환)
  8. 채팅 정리 버튼이 `purge()` 3초 넘게 걸리면 인터랙션 토큰 만료로 조용히 실패(`Unknown interaction` 404)하던 버그 수정 — `defer()` 먼저 하고 `followup.send()`로 응답
- **LLM 백엔드를 Claude API → 로컬 Ollama sLLM(EXAONE 3.5 7.8B)로 완전 교체** (7/4 오후, 선생님 과제 취지가 외부 API보다 sLLM 직접 운용 학습이라 결정):
  - 사전 검증: `gemma4:e2b`는 한국어 입력 자체를 이해 못 함(탈락) → LG `exaone3.5:7.8b`(4.8GB, 한국어 특화)로 교체 후 RAG 근거 인용 브리핑 품질 확인, GPU(RTX 4060 8GB)에서 8~12초 응답
  - 발견한 문제: 의도 분류 프롬프트가 기본 temperature에서 같은 입력에도 답이 오락가락함(비결정적) → `temperature=0`으로 고정하니 완전히 일치 → 분류(`classify_message`)는 항상 temperature=0, 생성(브리핑)은 기본값 사용
  - `src/llm.py` 신규: Ollama `/api/chat` 호출 공용 헬퍼(`chat(prompt, temperature)`), `keep_alive: "30m"`으로 모델을 계속 로드 상태 유지(재로딩 시 수십 초 지연 방지)
  - `src/briefing.py`, `src/discord_chat_bot.py`에서 `anthropic` import 전부 제거하고 `src.llm.chat`으로 교체. `requirements.txt`에서 `anthropic` 제거, `.env.example`에서 `ANTHROPIC_API_KEY` 제거
  - 프롬프트 보강 필요했던 부분: HELP 인식이 "도움말" 같은 직접적 표현엔 반응하지만 "뭐 할 수 있어?" 같은 간접 표현을 놓침 → 예시 추가로 해결. 장소명 추출 시 "강남역"을 "강남"으로 줄여 쓰는 오류 → "원문 글자 그대로 옮겨 적어" 지시 추가로 해결
  - **실행 전제조건 추가**: Ollama가 로컬에서 실행 중이어야 함(`ollama serve`, 보통 설치 시 자동 상시 실행) + `ollama pull exaone3.5:7.8b` 필요. Streamlit 배포(`app.py`, Track A 전용)는 이 봇과 무관해서 영향 없음
  - 전환 직후 회귀 2건 추가 발견·수정: (a) "기능"/"명령어"처럼 완전한 문장이 아닌 단어 하나만 쳤을 때 HELP를 못 알아채 봇이 무응답이던 문제 → 단어 하나여도 HELP로 처리하라는 규칙 추가 (b) "매일"이란 단어가 없으면 "15시18분에 알려줘"류 요청을 SCHEDULE로 인식 못 하던 문제(Claude는 됐었음) → "매일 없어도 시각+알림 요청이면 SCHEDULE" 규칙 추가. 기존 15개 인텐트 케이스 전부 재검증 통과
- **개인 체감 피드백 학습 완료** (7/4 저녁, PRD 4순위·"프로젝트 시그니처"):
  - 매일 알림 메시지에 🥶 추웠어 / 👍 딱 좋았어 / 🥵 더웠어 버튼(`FeedbackView`) 부착 → 클릭 시 `data/feedback.json`(gitignore)에 그날 기온과 함께 기록
  - `src/feedback.py`: `get_personal_offset(channel_id)` — 누적 피드백의 라벨별 평균으로 개인 체감온도 보정치(°C) 계산. 표본 3개 미만이면 중립(보정 없음). ponytail 판단: 며칠짜리 데이터로 회귀모델 학습하면 과적합이라 오히려 신뢰성 저하 — 평균 보정치가 이 규모엔 더 정직한 방법
  - `generate_briefing(prediction, personal_offset)`에 보정치를 프롬프트로 주입해 옷차림 조언에 자연스럽게 반영(니치 조언과 같은 패턴)
  - `src/seed_feedback.py` 신규: 시연용 더미 피드백 10건 생성 스크립트(`python -m src.seed_feedback <channel_id>`) — 실사용 며칠로는 학습 효과를 보여주기 어려워서, "실제보다 추위를 잘 타는 사용자" 시나리오로 미리 채워둠(평균 보정치 +2.0°C로 검증 완료)
- **디스코드 봇 사용성 후속 수정 3건** (7/4 밤, 사용자 피드백 기반, `src/discord_chat_bot.py`만 수정):
  1. `HELP_TEXT` 가독성 개선 — 긴 서술형 불릿을 카테고리별 미니 헤더(📅⏰🚗🚲🧹) + `예시 명령어` → 결과 2줄 구조로 재작성. 봇 재시작해야 반영됨(Python 핫리로드 없음, PID 재시작으로 확인)
  2. 알림을 이미 지난 시각(예: 지금이 17:15인데 "1710"으로 설정)으로 설정하면 그 자리에서 `_build_daily_message()`(LSTM 예측+RAG 검색+LLM 생성, 실측 8.4초)를 즉시 만들어 보내던 로직 제거 — 응답 지연 체감 + 테스트할 때마다 채널에 브리핑이 중복으로 쌓이던 문제의 원인이었음. 이제는 "내일부터 매일 {시각}에 보내드릴게요" 안내만 하고 즉시발송 안 함
  3. 니치(자전거/자동차) 모드를 자연어로 전환하는 요청이 `classify_message` 프롬프트 예시 부족으로 오분류되던 버그 수정 — "자전거로 바꿔줘/변경해줘"가 거꾸로 NICHE OFF로 분류되거나, "자동차로 바꿔줘"가 NONE(무응답)으로 빠지던 문제. 프롬프트를 "자전거 언급=BIKE / 자동차·대중교통 언급=OFF" 방향 기준으로 재작성해 해결. 8개 표현 재분류 검증 + 기존 13개 인텐트(날씨/알림/교통/출근지/니치/도움말 등) 회귀 없음 확인 완료(로컬 스크립트로 `classify_message` 직접 호출해 검증, 별도 테스트 파일은 추가 안 함 — 대화형 봇 특성상 단위테스트 프레임워크보다 실제 문구 재현이 더 실질적 검증)
- **디스코드 봇 무응답 근본원인 수정 + 알림 시각 인식 개선** (7/4 밤, PR#3 머지, `src/discord_chat_bot.py`만 수정):
  1. "알림설정 2019"처럼 조사(에/로) 없이 명령어+시각이 붙은 압축 표현을 `classify_message`가 NONE으로 오분류하던 문제 → 프롬프트에 해당 표현 예시 추가로 해결
  2. 메시지 전체가 4자리 숫자뿐인 경우("2015" 등) LLM 판단이 애매(시각인지 그냥 숫자 언급인지)해서 시각 추출에 실패하던 문제 → LLM 호출 전에 결정적 정규식 체크로 먼저 처리(유효 시각 범위 0000~2359만 통과, 그 외엔 기존 LLM 분류로 폴백)
  3. **근본원인 발견**: 채널 최초 사용자를 위한 온보딩 패널 자동 전송 기능(이번에 신규 추가)이 봇 권한 부족 채널에서 403 Forbidden으로 실패할 때 예외 처리가 없어 `on_message` 이벤트 핸들러 전체가 중단됨 → 이 때문에 사용자가 보낸 실제 메시지(예: "2015")가 분류·응답 단계까지 아예 도달 못 하고 무응답으로 보이던 것이 실제 원인이었음. try/except로 감싸 온보딩 실패해도 이후 메시지 처리가 계속되도록 수정
  4. (신규) 채널에 봇이 핀 고정한 안내 패널이 없으면 사용자 첫 메시지 시 도움말+설정 버튼 패널을 자동으로 먼저 보여주는 온보딩 기능 추가(`_onboarded` 런타임 캐시, 프로세스 재시작 시 핀 존재 여부로 재판단하므로 중복 전송 없음)
  5. 진단용 로그 1줄 추가(`[on_message] '메시지' -> intent=... detail=...`) — 이후 유사 무응답 리포트 시 원인 파악 속도 개선
  6. `docs/CODE_ANALYSIS.txt` 신규: 전체 코드(app.py, src/, tests/) 함수/클래스 상세 분석 문서
- **Streamlit에 Phase 3 섹션 추가 + 탭 UI로 재구성** (7/5): `app.py`가 Phase1/2(ML/DL)만 보여줘서 배포 화면에서 프로젝트 시그니처(RAG 브리핑·개인 체감 피드백)를 전혀 확인할 수 없던 문제 발견 → Phase 3 섹션 추가. `generate_briefing()`을 실시간으로 먼저 시도하고(로컬 Ollama 있으면 실제 생성), Streamlit Cloud처럼 Ollama가 없는 환경이면 예외를 잡아 로컬에서 미리 캡처해둔 실제 산출물로 폴백. 개인 체감 보정치는 `get_personal_offset()`을 그대로 재사용하고 실데이터 없으면(Cloud는 `feedback.json` gitignore라 항상 없음) `seed_feedback.py` 더미로 계산(+2.0°C). 이후 섹션이 늘어 스크롤이 길어져 `st.tabs()`로 Phase 1/2/3 탭 분리
- **출근지가 서울 외 지역이면 날씨 예측이 무뎌지는 한계 발견 + 경고 문구 추가** (7/5): LSTM이 서울(기상청 108지점) 데이터로만 학습돼 있어서, 출근지가 수원처럼 다른 도시면 실제 날씨와 어긋날 수 있음(사용자 제보 사례: 7/1 서울은 비, 수원은 안 옴). 남은 기간상 지역별 재학습은 범위 밖으로 판단 → 출근 소요시간 조회 때 이미 계산되는 `distance_km`(TMAP)가 20km 넘으면 "날씨 예측은 서울 기준이라 목적지와 다를 수 있음" 경고를 출근길 섹션에 추가(`src/discord_chat_bot.py`, `COMMUTE_WEATHER_CAVEAT_KM`)
- **한파+강수 상황에서 브리핑이 부적절하던 문제 발견 + 수정** (7/5): 기상청 `precip` 데이터가 비/눈을 구분하지 않아서, 영하 기온에서도 강수확률만 높으면 무조건 "☔ 우산 챙기세요"가 나가던 문제 → 최저기온 0도 이하일 때는 RAG 검색어를 "우산 강수확률" 대신 "노면 결빙 빙판길"로 바꾸고, 프롬프트에도 눈·진눈깨비 가능성을 알려 안내가 상황에 맞게 나오도록 수정(`src/briefing.py`). 원래 자전거 니치 전용이었던 노면상태 로직(`data/knowledge/niche/자전거통근_노면가이드.md`)을 일반 사용자 브리핑에도 반영한 것 — 실제 생성 검증 완료("눈이나 진눈깨비가 예상되니 빙판길에 주의하며..." 문구 확인)
- **디스코드 봇 중복 실행 사고 + 트러블슈팅 문서화** (7/5): 봇을 백그라운드로 재시작하는 과정에서 이전 프로세스가 안 죽은 걸 놓치고 두 번째 인스턴스를 또 띄워 메시지 하나에 응답이 2번씩 나가는 사고 발생 → 원인은 이 Windows/MSYS 환경에서 `ps aux`가 명령행 인자를 안 보여줘서 살아있는 프로세스를 죽은 걸로 오판했던 것(`ps -ef`로 확인해야 함). 중복 프로세스 종료 후 단일 인스턴스로 재시작해 해결. `docs/troubleshooting/` 폴더 신규 생성 — 이 건과 7/4 밤 온보딩 403 무응답 근본원인 건을 각각 별도 문서로 정리(재발방지 포함)
- **기상청 일자료 자동 수집 + 봇 비동기 블로킹 해소** (7/6~7/7, PR 머지): `src/ml/fetch_kma.py` 신규 — 매일 정해진 시각(`KMA_FETCH_TIMES`)에 KMA 최신 일자료를 자동으로 받아와 `seoul_weather.csv`에 이어붙임(`tasks.loop`, 실패해도 다음날 밀린 기간까지 자동으로 따라잡음). 옷차림 안내를 로컬 sLLM 판단 대신 코드 결정론 계산으로 변경(`_fixed_clothing_line`) — sLLM이 이따금 옷차림 표 기준을 무시하고 모순된 결론을 내는 문제 발견해 대응. 대중교통 API(TMAP/ODsay) 에러 로깅 추가.
- **"오늘 날씨" 조회 구조적 한계 발견 + 대응** (7/7): KMA 일자료는 하루가 끝나야 확정되는 통계라 "오늘"치 실측값이 원천적으로 존재하지 않는 한계 발견 → `src/predictor.py`에 `get_today_observed()` + 예측 캐시(`data/prediction_cache.json`) 추가: 전날 계산해둔 "내일" 예측을 캐시해뒀다가 그 날짜가 "오늘"이 되면 재사용(폴백 시에도 항상 오늘 날짜로 표시해 "내일" 문구 혼입 방지). 예약 알림(`_build_daily_message`)은 원래대로 `get_prediction()`(내일 예측)만 사용 — 채팅으로 직접 "오늘 날씨" 물어볼 때만 캐시 로직 적용. 채팅으로 오늘/내일 날씨 물어볼 때는 자전거 니치 섹션 제외(예약 브리핑 전용으로 유지).
  - **동시성 버그 발견+수정**: 예약 알림 준비(캐시 쓰기)와 채팅 "오늘 날씨" 조회(캐시 읽기)가 정확히 겹치면 Windows에서 양방향으로 `PermissionError`가 날 수 있음(원자적 교체(`os.replace`)만으론 부족) → 읽기·쓰기 양쪽에 짧은 재시도 로직 추가, 동시성 재현 테스트로 검증 완료.
- **발표 후속 정리 + 알려진 문제 2건 해결** (7/7 발표 후): `docs/archive/`로 이전 발표자료 초안 정리(`채비.pptx`를 최종본으로 확정), 중복 `pic/` 폴더 삭제.
  1. `check_schedule` 루프가 채널 발송 실패(예: 발송 순간 와이파이 순단)로 통째로 죽어 이후 모든 예약 알림이 멈추던 문제 → 채널별 처리를 try/except로 감싸 실패한 채널만 건너뛰고 다음 틱(1초 후)에 재시도하도록 수정.
  2. **"오늘 날씨" 캐시 워크어라운드를 실시간 API로 교체**: `src/ml/fetch_realtime.py` 신규 — 기상청 단기예보 조회서비스의 초단기예보(`getUltraSrtFcst`, 향후 약 6시간 시간별 기온·강수형태)로 오늘 최고/최저·강수여부를 근사. `predictor.get_today_observed()`가 이 실시간 API를 최우선으로 쓰고 실패하면 기존 캐시/최근실측 순으로 폴백. 예약 알림용 학습 데이터 수집(`fetch_kma.py`, 일자료)은 변경 없이 그대로 유지 — 채팅으로 "오늘 날씨" 물어볼 때만 실시간 API 적용.
     - **현재 미승인 상태**: 같은 `KMA_SERVICE_KEY`라도 이 API(단기예보 조회서비스)는 data.go.kr에서 별도 활용신청이 필요 — 테스트 결과 `500 Unexpected errors`로 확인(파라미터 문제 아니라 미승인으로 판단, 초단기실황 API도 동일 증상). **다음 세션 TODO**: data.go.kr에서 "기상청_단기예보 ((구)_동네예보) 조회서비스" 활용신청 승인 확인 → 승인되면 코드 변경 없이 자동으로 실시간 API가 켜짐(폴백 로직이라 지금도 정상 동작 중).

## Streamlit Cloud 배포 절차
1. https://share.streamlit.io 접속 → GitHub 계정으로 로그인
2. "New app" → 레포 `50seok/WeatherCheck`, 브랜치 `main`, 메인 파일 `app.py` 선택
3. Secrets 설정 불필요 — `app.py`는 Track A 전용이라 `ANTHROPIC_API_KEY`/`DISCORD_WEBHOOK_URL` 안 씀
4. Deploy 클릭. 학습된 모델·데이터·그래프가 이제 git에 커밋돼 있어 재학습 없이 바로 로드됨

## 트랙 현황
| 트랙 | 범위 | 상태 | 폴더 | 브랜치 |
|---|---|---|---|---|
| A | ML → DL | 완료 (Phase 1/2) | `C:\Mark42\WeatherCheck` (main) | main |
| B | RAG·브리핑·봇 | Track A(LSTM) 통합 완료, end-to-end 검증 완료 | `C:\Mark42\WeatherCheck-rag` | feature/rag-briefing |

## Track B 구현 메모
- `data/knowledge/*.md` (6개): 우산·일교차 옷차림·폭염·한파·미세먼지·자외선 가이드 — 기상청 생활기상지수 공개자료 요약
- `data/knowledge/niche/*.md` (니치 타겟 전용, 7/4 추가): 자전거통근 노면가이드. 일반 지식 풀과 섞이면 니치 미설정 사용자에게도 자전거 조언이 오염돼 섞여 나오는 버그가 있어(TF-IDF top-3 검색이 문서 수가 적어 오검색) 별도 하위 폴더로 분리, `generate_niche_briefing()`이 검색 없이 니치→문서 1:1로 직접 읽어 별도 섹션(🚲)으로 생성
- `src/predictor.py`: `get_prediction()` — `src.dl.predict`(LSTM, MAE 2.41°C로 ML 대비 최고 성능) 호출, contract.md 스키마 그대로 반환(`source: "lstm"`). mock(`get_mock_prediction`)은 Track A 통합 완료로 제거.
- `data/raw/seoul_weather.csv`, `src/dl/models/lstm_model.keras`, `notebooks/figures/*.png`: 원래 gitignore 대상이었으나 배포 시 매번 재학습돼 로딩이 느려지는 문제 발견(7/4) → 용량이 450KB 미만이라 `.gitignore`에 예외 추가 후 git에 커밋. `src/dl/predict.py`의 "파일 없으면 재학습" 폴백은 유지(로컬에서 파일 지우고 실험할 때나 향후 재학습 시 대비용).
- `src/rag.py`: Chroma(`chroma_db/`, gitignore됨)로 인덱싱. 임베딩은 Chroma 기본 ONNX 모델(79MB 다운로드) 대신 **TF-IDF(sklearn)** 사용 — 이 네트워크에서 ONNX 모델 다운로드가 반복적으로 timeout돼서 판단 후 교체. 문서 6~10개 규모라 매 검색마다 컬렉션 재구축해도 즉시 처리됨
- `src/llm.py` (7/4 추가): 로컬 Ollama(`exaone3.5:7.8b`) 호출 공용 헬퍼. `chat(prompt, temperature)` — 분류는 temperature=0(결정적), 생성은 기본값
- `src/briefing.py`: `generate_briefing(prediction)` — RAG 검색 결과를 근거로 `src.llm.chat`(로컬 EXAONE)이 한국어 브리핑 생성. API 키 불필요, Ollama가 로컬에서 실행 중이어야 함
- `src/discord_bot.py`: `send_briefing(text)` — 디스코드 웹훅으로 텍스트 전송(stdlib urllib만 사용, 최소 기능). `DISCORD_WEBHOOK_URL` 필요(.env)
- `src/discord_chat_bot.py` (7/4 추가): 대화형 봇. 키워드 매칭 대신 로컬 EXAONE이 매 메시지 의도를 분류(temperature=0). `DISCORD_BOT_TOKEN` 필요(.env), Developer Portal에서 "Message Content Intent" 켜야 함. Ollama도 같이 실행 중이어야 함. 계속 실행 상태 유지 필요(`python -m src.discord_chat_bot`).
  - 오늘/내일 날씨 질문 → RAG 브리핑 답장(오늘=실측값, 내일=LSTM 예측, 그 이상은 "미지원" 안내)
  - 자연어로 알림 시각 설정("매일 아침 8시에 알려줘") → `data/schedule.json`(gitignore)에 저장, 매분 체크해서 자동 발송
  - 채팅 정리("메시지 정리해줘", 기본 50개, 또는 버튼) → `channel.purge(check=lambda m: not m.pinned)`, 봇에 "메시지 관리" 권한 필요. 핀 고정된 설정 패널은 보존
  - 도움말("뭐 할 수 있어?") → `HELP_TEXT` + 설정 버튼 패널(`SettingsView`) 전송, 채널에 처음 한 번 자동 핀 고정
  - 출퇴근 소요시간("강남역에서 서울역까지 얼마나 걸려?") → `src/traffic.py`가 TMAP(자차)·ODsay(대중교통) 조회, 매번 채팅으로 출발지/도착지 입력
  - 출근지 설정("출근지 강남역에서 서울역으로 설정해줘") / 해제("출근지 해제해줘" → `UNCOMMUTE` 인텐트) → `data/commute.json`(gitignore)에 저장, 이후 알림 보낼 때마다 날씨+출퇴근 소요시간을 구분된 섹션으로 같이 발송(`_build_daily_message`). 자전거 니치일 땐 이 섹션 생략(데이터는 유지, 니치 해제하면 복원)
  - 니치 타겟(자전거 통근) — 채팅("자전거로 통근한다고 설정해줘"/"니치 해제해줘") 또는 버튼(🚲/🚗)으로 토글, `data/niche.json`(gitignore)에 저장. `generate_niche_briefing()`이 `data/knowledge/niche/자전거통근_노면가이드.md`를 검색 없이 직접 읽어 날씨 섹션과 분리된 별도 섹션(🚲)으로 생성
  - 개인 체감 피드백 — 매일 알림에 붙는 🥶/👍/🥵 버튼(`FeedbackView`) 클릭 시 `src/feedback.py`가 `data/feedback.json`(gitignore)에 기록, 누적되면 `get_personal_offset()`이 브리핑에 자동 반영
- `src/feedback.py` (7/4 추가): 개인 체감온도 보정치 계산(`get_personal_offset`), 발송 날씨 기록(`save_last_weather`), 피드백 기록(`record_feedback`)
- `src/seed_feedback.py` (7/4 추가): 시연용 더미 피드백 10건 생성 스크립트
- `.env.example` — `DISCORD_WEBHOOK_URL`, `DISCORD_BOT_TOKEN`, `TMAP_APP_KEY`, `ODSAY_API_KEY` (`ANTHROPIC_API_KEY`는 Ollama 전환으로 7/4 오후 제거)
- 검증: `python -m src.predictor`, `python -m src.rag`, `python -m src.briefing`, `python -m src.discord_bot` 전부 실행 확인·통과(7/3, 7/4 Ollama 전환 후 재검증 완료)

## 알려진 이슈
- ~~디스코드 웹훅 POST가 403 Forbidden~~ (해결, 7/3): Discord(Cloudflare)가 `urllib` 기본 User-Agent(`Python-urllib/x.x`)를 차단. `src/discord_bot.py` 요청 헤더에 `User-Agent: Mozilla/5.0` 추가로 해결
- ~~Phase 1 데이터는 합성 데이터~~ → **해결 (7/3)**: data.kma.go.kr ASOS 일자료(서울/108) 수동 다운로드 → `src/ml/import_kma.py`로 EUC-KR CSV를 스키마(date/temp_avg/temp_max/temp_min/humidity/pressure/wind_speed/precip) 변환해 `data/raw/seoul_weather.csv`에 저장(git 미추적). 1차 914일(2024-01~2026-07) → **2차 확장(7/3): 3,836일(2016-01-01~2026-07-02, 10.5년)**, 여러 파일(120개월 단위 조회 제한) 합쳐서 처리하도록 `import_kma.py`가 다중 경로 인자 지원.
- `src/ml/generate_data.py`(합성 데이터)는 `predict.py`가 `data/raw/seoul_weather.csv`를 못 찾을 때(예: Streamlit Cloud처럼 raw CSV 미포함 배포 환경)의 폴백으로만 유지 — CSV 있으면 자동으로 실데이터 사용.

## Phase 1 산출물 (Track A)
- `src/ml/import_kma.py` — KMA ASOS CSV(EUC-KR, 여러 파일 지원) → `data/raw/seoul_weather.csv` 변환 (`python src/ml/import_kma.py <경로1> [<경로2> ...]`)
- `src/ml/generate_data.py` — 합성 데이터 생성(raw CSV 없을 때 폴백) (`python src/ml/generate_data.py`)
- `src/ml/eda.py` — 결측치/분포/상관관계 EDA, `notebooks/figures/`에 그래프 저장 (`python src/ml/eda.py`)
- `src/ml/predict.py` — 피처 구성 + 모델 3개 비교 + `predict_tomorrow()` (contract.md 스키마 반환, Track B가 호출할 함수)
- `src/ml/train.py` — CLI 리포트 + pkl 저장 (`python -m src.ml.train`)
- `app.py` — Streamlit 데모 (슬라이더 입력 → 내일 최고/최저기온·강수확률 + 모델 비교 차트)
- `tests/test_predict.py` — contract 스키마 self-check (`python tests/test_predict.py`)
- 결과(10.5년 실데이터 기준, 7/3 재측정): 회귀 최고=LinearRegression(MAE≈2.50°C), 분류 최고=LogisticRegression(Acc≈0.71).

## Phase 2 산출물 (Track A)
- `src/dl/sequences.py` — 최근 7일 시퀀스(MinMaxScaler 정규화) 생성 (`SEQ_LEN=7`)
- `src/dl/train.py` — LSTM(32) 학습(회귀 2출력+분류 1출력 멀티헤드) + ML 대비 비교 그래프 저장 (`python -m src.dl.train`)
- `src/dl/predict.py` — `load_models()`/`predict_tomorrow()` (ML과 동일 인터페이스, contract.md 스키마, `source: "lstm"`)
- `tests/test_dl_predict.py` — contract 스키마 self-check
- `app.py`에 Phase 2 섹션 추가 — LSTM 예측 metric + `notebooks/figures/ml_vs_dl.png` 비교 차트
- 결과(10.5년 데이터, 7/3 재측정): **LSTM이 ML을 역전** — 회귀 MAE: LSTM 2.41°C vs ML(LinearRegression) 2.50°C. 분류 Accuracy: LSTM 0.706 vs ML(LogisticRegression) 0.714(거의 동률). 데이터 2.5년→10.5년 확장 후 LSTM이 우위 — "DL은 데이터 충분해야 진가 발휘" 보고서 스토리로 활용.

## 세션 자동저장 설정 (완료, 7/3)
- **양쪽 트랙 모두** `.claude/settings.local.json`에 `SessionEnd` 훅 설정됨(gitignore됨, 폴더별 개별 설정 — git worktree라 폴더가 다르면 Claude Code가 각각 별개 프로젝트로 인식하기 때문에 양쪽에 각각 걸어야 함).
- 터미널 종료 시 자동으로 `claude -p --model haiku`가 최근 git log/diff만 보고 그 폴더의 `docs/STATUS.md`만 갱신 → 커밋+푸시. 다른 파일은 안 건드림. 실패해도 세션 종료는 안 막힘.
- 무한루프 방지용 env 가드(`WEATHERCHECK_STATUS_HOOK_RUNNING`) 걸려있음.
- **불안하면 끄기 전에 직접**: "커밋하고 STATUS.md 갱신해줘" 한 줄 치면 확실함. 파일(코드/노트북)은 훅과 무관하게 항상 디스크에 저장돼 있으니 훅 실패해도 작업 유실은 없음.

## 병합 시 예상 이슈 (7/5 Track A/B 통합 때 참고) — 해결됨
- `docs/STATUS.md`: 양쪽 브랜치가 각자 갱신해서 충돌남 → 최신 사실 기준으로 이 파일에서 정리 완료.
- `app.py`: Track A(Phase1/2 데모)와 Track B(Phase3 대시보드)가 겹칠 수 있음 → **Track B는 `app.py` 직접 수정하지 않음**, `src/predictor.py`에서 Track A 함수를 호출하는 방식으로만 연결.
- 나머지(`src/`, `notebooks/`, `knowledge/`)는 트랙별 폴더가 갈려 있어 충돌 없음.

## 다음 세션 시작 멘트 (그대로 붙여넣기용)

**Track A** (`C:\Mark42\WeatherCheck`에서 `claude` 실행):
```
docs/STATUS.md 읽고 Track A(Phase 1 ML)만 진행해. docs/contract.md 스키마 준수.
```

**Track B** (`C:\Mark42\WeatherCheck-rag`에서 `claude` 실행):
```
docs/STATUS.md 읽고 Track B(RAG·브리핑·봇)만 진행해. docs/contract.md 준수.
```

## 목표
- 기상 예측값(docs/contract.md 스키마)을 받아 "☔ 우산 챙기세요" 같은 자연어 출근 브리핑을 근거 문서 인용과 함께 생성하는 파이프라인.
