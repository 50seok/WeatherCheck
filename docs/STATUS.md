# STATUS — WeatherCheck

> 갱신: 2026-07-03 · **마감: 2026-07-07(월) 09:00 제출(프로젝트+보고서)**

## 진행 체크리스트
- [x] 골격 초기화 (git·디렉토리·CLAUDE.md·contract.md) — 7/3
- [ ] **Phase 1 ML** (7/3): 기상청 CSV 다운 → EDA → 모델 3개 비교(LR/RF/XGB) → Streamlit v1
- [ ] **Phase 2 DL** (7/4): LSTM 학습 → ML vs DL 비교 그래프 → Streamlit v2
- [ ] **Phase 3 LLM+RAG** (7/5): knowledge 문서 → Chroma 인덱싱 → 근거 인용 브리핑 → 디스코드 봇 → Track A/B 통합
- [ ] **마무리** (7/6): Streamlit Cloud 배포 → 보고서·발표자료(단계별 5장) → 데모 영상 → 버퍼

## 트랙 현황
| 트랙 | 범위 | 상태 | 워크트리 |
|---|---|---|---|
| A | ML → DL | 미착수 | (생성 시 기입) |
| B | RAG·브리핑·봇 | 미착수 (mock으로 병렬 가능) | (생성 시 기입) |

## 알려진 이슈
- 없음

## 다음 세션 시작 멘트 예시
- Track A: "docs/STATUS.md 읽고 Track A(Phase 1 ML)만 진행해. docs/contract.md 스키마 준수."
- Track B: "docs/STATUS.md 읽고 Track B(RAG·브리핑·봇)만 진행해. 예측은 mock 사용, docs/contract.md 준수."
