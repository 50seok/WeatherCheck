# STATUS — WeatherCheck

> 갱신: 2026-07-03 · **마감: 2026-07-07(월) 09:00 제출(프로젝트+보고서)**
> GitHub: https://github.com/50seok/WeatherCheck (private)

## 진행 체크리스트
- [x] 골격 초기화 (git·디렉토리·CLAUDE.md·contract.md) — 7/3
- [x] GitHub 레포 생성·푸시, Track B 워크트리 생성 — 7/3
- [x] **Phase 1 ML** (7/3): EDA → 모델 3개 비교(LR/RF/XGB) → Streamlit v1 완료 (데이터는 합성, 아래 이슈 참고)
- [ ] **Phase 2 DL** (7/4): LSTM 학습 → ML vs DL 비교 그래프 → Streamlit v2
- [ ] **Phase 3 LLM+RAG** (7/5): knowledge 문서 → Chroma 인덱싱 → 근거 인용 브리핑 → 디스코드 봇 → Track A/B 통합
- [ ] **마무리** (7/6): Streamlit Cloud 배포 → 보고서·발표자료(단계별 5장) → 데모 영상 → 버퍼

## 트랙 현황
| 트랙 | 범위 | 상태 | 폴더 | 브랜치 |
|---|---|---|---|---|
| A | ML → DL | 미착수 | `C:\Mark42\WeatherCheck` (main) | main |
| B | RAG·브리핑·봇 | 미착수 (mock으로 병렬 가능) | `C:\Mark42\WeatherCheck-rag` | feature/rag-briefing |

## 알려진 이슈
- ~~Phase 1 데이터는 합성 데이터~~ → **해결 (7/3)**: data.kma.go.kr ASOS 일자료(서울/108, 2024-01-01~2026-07-02, 914일) 수동 다운로드 → `src/ml/import_kma.py`로 EUC-KR CSV를 스키마(date/temp_avg/temp_max/temp_min/humidity/pressure/wind_speed/precip) 변환해 `data/raw/seoul_weather.csv`에 저장(git 미추적, 결측 3건은 보간).
- `src/ml/generate_data.py`(합성 데이터)는 `predict.py`가 `data/raw/seoul_weather.csv`를 못 찾을 때(예: Streamlit Cloud처럼 raw CSV 미포함 배포 환경)의 폴백으로만 유지 — CSV 있으면 자동으로 실데이터 사용.

## Phase 1 산출물
- `src/ml/import_kma.py` — KMA ASOS CSV(EUC-KR) → `data/raw/seoul_weather.csv` 변환 (`python src/ml/import_kma.py <kma_csv_경로>`)
- `src/ml/generate_data.py` — 합성 데이터 생성(raw CSV 없을 때 폴백) (`python src/ml/generate_data.py`)
- `src/ml/eda.py` — 결측치/분포/상관관계 EDA, `notebooks/figures/`에 그래프 저장 (`python src/ml/eda.py`)
- `src/ml/predict.py` — 피처 구성 + 모델 3개 비교 + `predict_tomorrow()` (contract.md 스키마 반환, Track B가 호출할 함수)
- `src/ml/train.py` — CLI 리포트 + pkl 저장 (`python -m src.ml.train`)
- `app.py` — Streamlit 데모 (슬라이더 입력 → 내일 최고/최저기온·강수확률 + 모델 비교 차트)
- `tests/test_predict.py` — contract 스키마 self-check (`python tests/test_predict.py`)
- 결과(실데이터 기준, 7/3 재측정): 회귀 최고=LinearRegression(MAE≈2.63°C), 분류 최고=LogisticRegression(Acc≈0.78).

## 세션 자동저장 설정 (완료, 7/3)
- **양쪽 트랙 모두** `.claude/settings.local.json`에 `SessionEnd` 훅 설정됨(gitignore됨, 폴더별 개별 설정 — git worktree라 폴더가 다르면 Claude Code가 각각 별개 프로젝트로 인식하기 때문에 양쪽에 각각 걸어야 함).
- 터미널 종료 시 자동으로 `claude -p --model haiku`가 최근 git log/diff만 보고 그 폴더의 `docs/STATUS.md`만 갱신 → 커밋+푸시. 다른 파일은 안 건드림. 실패해도 세션 종료는 안 막힘.
- 무한루프 방지용 env 가드(`WEATHERCHECK_STATUS_HOOK_RUNNING`) 걸려있음.
- **불안하면 끄기 전에 직접**: "커밋하고 STATUS.md 갱신해줘" 한 줄 치면 확실함. 파일(코드/노트북)은 훅과 무관하게 항상 디스크에 저장돼 있으니 훅 실패해도 작업 유실은 없음.

## 병합 시 예상 이슈 (7/5 Track A/B 통합 때 참고)
- `docs/STATUS.md`: 양쪽 브랜치가 각자 갱신해서 거의 100% 충돌남 → **최신 걸로 덮어쓰기만 하면 됨**(코드처럼 정교하게 합칠 필요 없음).
- `app.py`: Track A(Phase1/2 데모)와 Track B(Phase3 대시보드)가 겹칠 수 있음 → **Track B는 `app.py` 직접 수정 금지**, 별도 파일로 만들거나 통합 시점에 A 완성 후 연결(docs/contract.md 참고).
- 나머지(`src/`, `notebooks/`, `knowledge/`)는 트랙별 폴더가 갈려 있어 충돌 거의 없음.

## 다음 세션 시작 멘트 (그대로 붙여넣기용)

**Track A** (`C:\Mark42\WeatherCheck`에서 `claude` 실행):
```
docs/STATUS.md 읽고 Track A(Phase 1 ML)만 진행해. docs/contract.md 스키마 준수.
```

**Track B** (`C:\Mark42\WeatherCheck-rag`에서 `claude` 실행):
```

```
## 목표

- docs/STATUS.md 읽고 Track A(Phase 1 ML)만 진행해. Track B(RAG·브리핑·봇) 코드는 건드리지 마.
- 기상청 과거 날씨 데이터로 내일 기온/강수 예측 모델 만들고 Streamlit 데모까지.

진행 할 일:
1. data.kma.go.kr(기상자료개방포털)에서 서울 지역 과거 날씨 CSV 다운로드 (기온·습도·기압·풍속·강수량, 최소 1~2년치) → data/raw/
2. EDA: 결측치·이상치 확인, 시계열 분포·상관관계 시각화(heatmap 등)
3. 피처 구성: 오늘 기온/습도/기압/어제 강수량 등 → 정답: 내일 기온(회귀)/비 여부(분류)
4. 모델 3개 비교: LinearRegression → RandomForest → XGBoost, train_test_split으로 평가(MAE/Accuracy)
5. app.py에 Streamlit 데모 작성 — 슬라이더로 기온·습도 입력하면 내일 날씨 예측 출력
6. 예측 함수는 docs/contract.md 스키마(date/temp_max/temp_min/rain_prob/source)로 반환하도록 구현 — Track B가 나중에 이 함수를 호출함
7. 진행하면서 docs/STATUS.md 체크리스트 업데이트, 완료되는 대로 커밋
주의: Paca 태스크 안 씀. A-B-C 풀 프로세스(리뷰어·게이트)도 생략, 진행상황만 STATUS.md에 남겨. app.py는 Track A 전용이니 자유롭게 작업해도 되지만 Track B가 나중에 여기 이어붙일 거라 구조 너무 복잡하게 짜지 마.
```
