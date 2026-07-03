import json
import os
import urllib.request

from dotenv import load_dotenv

load_dotenv()


def send_briefing(text: str) -> None:
    webhook_url = os.environ["DISCORD_WEBHOOK_URL"]
    body = json.dumps({"content": text}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    urllib.request.urlopen(req)


if __name__ == "__main__":
    send_briefing("[테스트] WeatherCheck 봇 연결 확인")
