# WeatherCheck — 출근 비서 (ML → DL → LLM+RAG)

**목적**: 날씨+교통을 학습해 출근 전 행동 지침("우산·겉옷·10분 일찍")을 자동 알림. 상세: `docs/PRD_workload.md`, `docs/ML_DL_LLM_loardmap.md`
**마감**: 2026-07-07(월) 09:00 — 프로젝트 + 보고서 제출. 이 마감이 모든 판단의 기준.
**스택**: Python 3.11 · pandas/scikit-learn/xgboost(ML) · TensorFlow-Keras LSTM(DL) · Claude API + Chroma(RAG) · Streamlit(배포) · 디스코드 봇(알림)
**확정값**: 지역=서울 · 출퇴근 모드=대중교통 · 알림=디스코드
**데이터**: 기상청 CSV(data.kma.go.kr) → `data/raw/` (git 미추적). RAG 지식문서(생활기상지수 기준·옷차림 가이드·행동요령) → `data/knowledge/`

## 구조
- `notebooks/` 실험·EDA · `src/` 모듈 코드 · `app.py` Streamlit · `docs/` PRD·로드맵·STATUS·contract

## 병렬 트랙 (워크트리 2개)
- **Track A** = ML → DL (순차 — 같은 데이터 파이프라인, ML vs DL 비교가 산출물)
- **Track B** = RAG + 브리핑 + 디스코드 봇 (mock 예측으로 즉시 개발, 7/5 통합)
- 트랙 간 인터페이스는 `docs/contract.md`가 단일 진실 — 스키마 변경은 양 트랙 확인 후

## 스코프 컷 순서 (시간 부족 시 위에서부터 포기)
1. 교통 API → 2. 스케줄러 자동화(수동 실행 데모로 대체) → 3. 다일 예보(1일 예측만)
**컷 금지**: RAG 브리핑(근거 인용), ML vs DL 비교, 보고서

## 이 프로젝트에서 안 쓰는 것
- Paca 태스크 · A-B-C 풀 오케스트레이션 · 검증게이트 G1~G6 · 리뷰어 서브에이전트 루프
- 워크트리는 위 2트랙 분리에만 사용. 커밋 컨벤션·시크릿 스캔은 전역 규칙 그대로 적용.
