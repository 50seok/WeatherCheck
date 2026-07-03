# STATUS — WeatherCheck

> 갱신: 2026-07-03 · **마감: 2026-07-07(월) 09:00 제출(프로젝트+보고서)**

## 진행 체크리스트
- [x] 골격 초기화 (git·디렉토리·CLAUDE.md·contract.md) — 7/3
- [ ] **Phase 1 ML** (7/3): 기상청 CSV 다운 → EDA → 모델 3개 비교(LR/RF/XGB) → Streamlit v1
- [ ] **Phase 2 DL** (7/4): LSTM 학습 → ML vs DL 비교 그래프 → Streamlit v2
- [x] **Phase 3 LLM+RAG 골격** (7/3, Track B): knowledge 문서 6개 → Chroma 인덱싱 → mock 기반 근거 인용 브리핑 함수 → 디스코드 웹훅 골격
- [ ] **Phase 3 통합** (7/5): Track A 실제 예측 함수로 mock 교체, 디스코드 자동 발송 확인
- [ ] **마무리** (7/6): Streamlit Cloud 배포 → 보고서·발표자료(단계별 5장) → 데모 영상 → 버퍼

## 트랙 현황
| 트랙 | 범위 | 상태 | 워크트리 |
|---|---|---|---|
| A | ML → DL | 미착수 | (생성 시 기입) |
| B | RAG·브리핑·봇 | mock 파이프라인 완성+실동작 검증 완료, Track A 통합 대기 | main (워크트리 미사용 — 단일 트랙 작업) |

## Track B 구현 메모
- `data/knowledge/*.md` (6개): 우산·일교차 옷차림·폭염·한파·미세먼지·자외선 가이드 — 기상청 생활기상지수 공개자료 요약
- `src/predictor.py`: `get_mock_prediction()` — contract.md 스키마, `source: "mock"`. **Track A 통합 시 이 함수 호출부만 실제 예측 함수로 교체**
- `src/rag.py`: Chroma(`chroma_db/`, gitignore됨)로 인덱싱. 임베딩은 Chroma 기본 ONNX 모델(79MB 다운로드) 대신 **TF-IDF(sklearn)** 사용 — 이 네트워크에서 ONNX 모델 다운로드가 반복적으로 timeout돼서 판단 후 교체. 문서 6~10개 규모라 매 검색마다 컬렉션 재구축해도 즉시 처리됨
- `src/briefing.py`: `generate_briefing(prediction)` — RAG 검색 결과를 근거로 Claude API(`claude-sonnet-5`)가 한국어 브리핑 생성. `ANTHROPIC_API_KEY` 필요(.env)
- `src/discord_bot.py`: `send_briefing(text)` — 디스코드 웹훅으로 텍스트 전송(stdlib urllib만 사용, 최소 기능). `DISCORD_WEBHOOK_URL` 필요(.env)
- `.env.example` 추가 — `ANTHROPIC_API_KEY`, `DISCORD_WEBHOOK_URL`
- 검증: `python -m src.predictor`, `python -m src.rag`, `python -m src.briefing`, `python -m src.discord_bot` 전부 실행 확인·통과(7/3). Claude API 브리핑 생성 + 디스코드 웹훅 전송 실동작 확인 완료

## 알려진 이슈
- ~~디스코드 웹훅 POST가 403 Forbidden~~ (해결, 7/3): Discord(Cloudflare)가 `urllib` 기본 User-Agent(`Python-urllib/x.x`)를 차단. `src/discord_bot.py` 요청 헤더에 `User-Agent: Mozilla/5.0` 추가로 해결

## 다음 세션 시작 멘트 예시
- Track A: "docs/STATUS.md 읽고 Track A(Phase 1 ML)만 진행해. docs/contract.md 스키마 준수."
- Track B: "docs/STATUS.md 읽고 Track B(RAG·브리핑·봇)만 진행해. 예측은 mock 사용, docs/contract.md 준수."

## 목표
- 기상 예측값(docs/contract.md 스키마)을 받아 "☔ 우산 챙기세요" 같은 자연어 출근 브리핑을 근거 문서 인용과 함께 생성하는 파이프라인.

진행 할 일:
1. knowledge/ 폴더에 생활기상지수 기준·옷차림 가이드·폭염한파 행동요령 등 조언 근거가 될 짧은 문서 5~10개 마크다운으로 작성(기상청 생활기상지수 공개자료 참고해서 요약)
2. Chroma로 벡터 인덱싱 (langchain 또는 openai/anthropic embedding 중 뭐가 더 쉬운지 판단해서 진행)
3. 예측 mock 데이터(docs/contract.md 스키마, source: "mock")를 입력받아 RAG로 근거 문서 검색 → Claude API로 브리핑 텍스트 생성하는 함수 작성
4. 디스코드 봇 골격(웹훅 또는 discord.py) — 브리핑 텍스트를 채널에 전송하는 최소 기능까지만
5. 진행하면서 docs/STATUS.md 체크리스트 업데이트, 완료되는 대로 커밋
주의: Track A가 아직 진짜 예측값을 안 주니까 mock으로 개발하고, 나중에(7/5) 통합할 때 mock 부분만 실제 함수 호출로 바꾸면 되게 구조 짜줘. Paca 태스크 안 씀. A-B-C 풀 프로세스(리뷰어·게이트)도 생략, 그냥 진행상황만 STATUS.md에 남겨.