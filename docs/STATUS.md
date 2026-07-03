# STATUS — WeatherCheck

> 갱신: 2026-07-03 · **마감: 2026-07-07(월) 09:00 제출(프로젝트+보고서)**
> GitHub: https://github.com/50seok/WeatherCheck (private)

## 진행 체크리스트
- [x] 골격 초기화 (git·디렉토리·CLAUDE.md·contract.md) — 7/3
- [x] GitHub 레포 생성·푸시, Track B 워크트리 생성 — 7/3
- [ ] **Phase 1 ML** (7/3): 기상청 CSV 다운 → EDA → 모델 3개 비교(LR/RF/XGB) → Streamlit v1
- [ ] **Phase 2 DL** (7/4): LSTM 학습 → ML vs DL 비교 그래프 → Streamlit v2
- [ ] **Phase 3 LLM+RAG** (7/5): knowledge 문서 → Chroma 인덱싱 → 근거 인용 브리핑 → 디스코드 봇 → Track A/B 통합
- [ ] **마무리** (7/6): Streamlit Cloud 배포 → 보고서·발표자료(단계별 5장) → 데모 영상 → 버퍼

## 트랙 현황
| 트랙 | 범위 | 상태 | 폴더 | 브랜치 |
|---|---|---|---|---|
| A | ML → DL | 미착수 | `C:\Mark42\WeatherCheck` (main) | main |
| B | RAG·브리핑·봇 | 미착수 (mock으로 병렬 가능) | `C:\Mark42\WeatherCheck-rag` | feature/rag-briefing |

## 알려진 이슈
- 없음

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
docs/STATUS.md 읽고 Track B(RAG·브리핑·봇)만 진행해. Track A(ML/DL) 코드는 건드리지 마.

목표: 기상 예측값(docs/contract.md 스키마)을 받아 "☔ 우산 챙기세요" 같은 자연어 출근 브리핑을 근거 문서 인용과 함께 생성하는 파이프라인.

오늘 할 일:
1. knowledge/ 폴더에 생활기상지수 기준·옷차림 가이드·폭염한파 행동요령 등 조언 근거가 될 짧은 문서 5~10개 마크다운으로 작성(기상청 생활기상지수 공개자료 참고해서 요약)
2. Chroma로 벡터 인덱싱 (langchain 또는 openai/anthropic embedding 중 뭐가 더 쉬운지 판단해서 진행)
3. 예측 mock 데이터(docs/contract.md 스키마, source: "mock")를 입력받아 RAG로 근거 문서 검색 → Claude API로 브리핑 텍스트 생성하는 함수 작성
4. 디스코드 봇 골격(웹훅 또는 discord.py) — 브리핑 텍스트를 채널에 전송하는 최소 기능까지만
5. 진행하면서 docs/STATUS.md 체크리스트 업데이트, 완료되는 대로 커밋

주의: Track A가 아직 진짜 예측값을 안 주니까 mock으로 개발하고, 나중에(7/5) 통합할 때 mock 부분만 실제 함수 호출로 바꾸면 되게 구조 짜줘. Paca 태스크 안 씀. A-B-C 풀 프로세스(리뷰어·게이트)도 생략, 그냥 진행상황만 STATUS.md에 남겨. app.py는 건드리지 마.
```
