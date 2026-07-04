# STATUS — WeatherCheck

> 갱신: 2026-07-04 · **마감: 2026-07-07(월) 09:00 제출(프로젝트+보고서)**
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
- **PRD 차별화 우선순위 진행** (7/4): 1순위 교통 결합 → 2순위 출근지 설정 → 3순위 니치 타겟(자전거 통근) 순으로 구현 완료. 4순위(개인 체감 피드백)는 미시작.
  1. 교통 결합: TMAP(자차 경로)·ODsay(대중교통 경로) API 연동, 디스코드 채팅으로 출발지/도착지 매번 입력받는 방식(`src/traffic.py`)
  2. 출근지 설정: 출발지/도착지를 한 번 등록해두면 이후 알림에 날씨+출퇴근 소요시간을 같이 보내줌(`data/commute.json`, gitignore)
  3. 니치 타겟: PRD가 예시로 든 자전거 통근족 하나만 우선 구현(1인 비서 취지상 다중 니치 불필요 판단) — 니치 전용 지식 문서(`data/knowledge/자전거통근_노면가이드.md`) 추가 후 RAG 검색·브리핑 프롬프트에 반영(`src/briefing.py`의 `generate_briefing(prediction, niche)`), 디스코드 채팅으로 "자전거로 통근한다고 설정해줘"/"니치 해제해줘"로 토글(`data/niche.json`, gitignore)
  - 참고: 1/2순위는 API 값을 그대로 전달하는 구조라 LLM/RAG와는 무관 — RAG가 실제로 개입하는 건 날씨 브리핑(`generate_briefing`)과 3순위 니치 조언뿐.

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
- `data/knowledge/*.md` (7개): 우산·일교차 옷차림·폭염·한파·미세먼지·자외선 가이드(기상청 생활기상지수 공개자료 요약) + 자전거통근 노면가이드(니치 타겟용, 7/4 추가)
- `src/predictor.py`: `get_prediction()` — `src.dl.predict`(LSTM, MAE 2.41°C로 ML 대비 최고 성능) 호출, contract.md 스키마 그대로 반환(`source: "lstm"`). mock(`get_mock_prediction`)은 Track A 통합 완료로 제거.
- `data/raw/seoul_weather.csv`, `src/dl/models/lstm_model.keras`, `notebooks/figures/*.png`: 원래 gitignore 대상이었으나 배포 시 매번 재학습돼 로딩이 느려지는 문제 발견(7/4) → 용량이 450KB 미만이라 `.gitignore`에 예외 추가 후 git에 커밋. `src/dl/predict.py`의 "파일 없으면 재학습" 폴백은 유지(로컬에서 파일 지우고 실험할 때나 향후 재학습 시 대비용).
- `src/rag.py`: Chroma(`chroma_db/`, gitignore됨)로 인덱싱. 임베딩은 Chroma 기본 ONNX 모델(79MB 다운로드) 대신 **TF-IDF(sklearn)** 사용 — 이 네트워크에서 ONNX 모델 다운로드가 반복적으로 timeout돼서 판단 후 교체. 문서 6~10개 규모라 매 검색마다 컬렉션 재구축해도 즉시 처리됨
- `src/briefing.py`: `generate_briefing(prediction)` — RAG 검색 결과를 근거로 Claude API(`claude-haiku-4-5-20251001`)가 한국어 브리핑 생성. 단순 요약·생성 작업이라 sonnet 5는 과함 판단 후 haiku로 교체. `ANTHROPIC_API_KEY` 필요(.env)
- `src/discord_bot.py`: `send_briefing(text)` — 디스코드 웹훅으로 텍스트 전송(stdlib urllib만 사용, 최소 기능). `DISCORD_WEBHOOK_URL` 필요(.env)
- `src/discord_chat_bot.py` (7/4 추가): 대화형 봇. 키워드 매칭 대신 Claude(haiku)가 매 메시지 의도를 분류. `DISCORD_BOT_TOKEN` 필요(.env), Developer Portal에서 "Message Content Intent" 켜야 함. 계속 실행 상태 유지 필요(`python -m src.discord_chat_bot`).
  - 오늘/내일 날씨 질문 → RAG 브리핑 답장(오늘=실측값, 내일=LSTM 예측, 그 이상은 "미지원" 안내)
  - 자연어로 알림 시각 설정("매일 아침 8시에 알려줘") → `data/schedule.json`(gitignore)에 저장, 매분 체크해서 자동 발송
  - 채팅 정리("메시지 정리해줘", 기본 50개) → `channel.purge()`, 봇에 "메시지 관리" 권한 필요
  - 도움말("뭐 할 수 있어?") → 기능 안내(`HELP_TEXT`)
  - 출퇴근 소요시간("강남역에서 서울역까지 얼마나 걸려?") → `src/traffic.py`가 TMAP(자차)·ODsay(대중교통) 조회, 매번 채팅으로 출발지/도착지 입력
  - 출근지 설정("출근지 강남역에서 서울역으로 설정해줘") → `data/commute.json`(gitignore)에 저장, 이후 알림 보낼 때마다 날씨+출퇴근 소요시간을 구분된 섹션으로 같이 발송(`_build_daily_message`)
  - 니치 타겟(자전거 통근, "자전거로 통근한다고 설정해줘"/"니치 해제해줘") → `data/niche.json`(gitignore)에 저장, `generate_briefing(prediction, niche)`이 니치 전용 지식 문서(`data/knowledge/자전거통근_노면가이드.md`)를 RAG로 검색해 노면·윈드칠·미세먼지 조언을 브리핑에 반영
- `.env.example` 추가 — `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`, `DISCORD_BOT_TOKEN`, `TMAP_APP_KEY`, `ODSAY_API_KEY`
- 검증: `python -m src.predictor`, `python -m src.rag`, `python -m src.briefing`, `python -m src.discord_bot` 전부 실행 확인·통과(7/3). Claude API 브리핑 생성 + 디스코드 웹훅 전송 실동작 확인 완료

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
