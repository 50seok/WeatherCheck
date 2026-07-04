"""로컬 Ollama sLLM 호출. Claude 등 외부 API 대신 sLLM을 직접 운용해보는 게 과제 취지라 채택.
LG EXAONE 3.5(7.8B, 한국어 특화) 하나로 생성(브리핑)·분류(의도 파악) 둘 다 처리.
사전 확인: 같은 분류 프롬프트도 기본 temperature에선 답이 오락가락했는데 temperature=0으로 고정하니 안정적으로 일치함
-> 분류처럼 정확한 라벨이 필요한 곳은 반드시 temperature=0으로 호출.
"""
import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "exaone3.5:7.8b"


def chat(prompt: str, temperature: float = 0.7) -> str:
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "options": {"temperature": temperature},
            "keep_alive": "30m",  # 봇이 하루 종일 도는 동안 매 호출마다 모델 재로딩(수십 초)되는 것 방지
            "stream": False,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"]


if __name__ == "__main__":
    print(chat("테스트: 한국어로 짧게 인사해줘.", temperature=0))
