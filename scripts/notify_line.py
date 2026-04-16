"""
notify_line.py - LINE Messaging APIで今日のTipsを自分のLINEに送信する
"""

import os
import json
import datetime
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
DAILY_DIR = BASE_DIR / "output" / "daily"

LINE_API_URL = "https://api.line.me/v2/bot/message/push"
CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "")
USER_ID = os.getenv("LINE_USER_ID", "")


def load_tips(date: datetime.date) -> dict | None:
    path = DAILY_DIR / f"{date.isoformat()}.json"
    if not path.exists():
        print(f"Tipsデータが見つかりません: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_message(data: dict) -> str:
    """LINEに送るテキストメッセージを組み立てる"""
    date_str = data["date"]
    lines = [f"🌿 今日の健康Tips（{date_str}）\n"]

    for i, tip in enumerate(data["tips"], 1):
        category = tip.get("category", "")
        title = tip.get("title", "")
        core = tip.get("core", "")
        stars = tip.get("stars", "")
        lines.append(f"【{i}】{category}")
        lines.append(f"📌 {title}")
        lines.append(f"{core}")
        lines.append(f"信頼度：{stars}\n")

    lines.append("──────────────")
    lines.append("📂 詳細・投稿用テキストはiCloudから：")
    lines.append(f"ファイル → iCloud Drive → 健康Tips → {date_str}.html")
    return "\n".join(lines)


def send_line(message: str) -> bool:
    if not CHANNEL_ACCESS_TOKEN or not USER_ID:
        print("エラー: LINE_CHANNEL_ACCESS_TOKEN または LINE_USER_ID が未設定です")
        return False

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CHANNEL_ACCESS_TOKEN}",
    }
    payload = {
        "to": USER_ID,
        "messages": [{"type": "text", "text": message}],
    }

    res = requests.post(LINE_API_URL, headers=headers, json=payload, timeout=10)
    if res.status_code == 200:
        print("LINE送信成功！")
        return True
    else:
        print(f"LINE送信失敗: {res.status_code} {res.text}")
        return False


def main():
    today = datetime.date.today()
    data = load_tips(today)
    if data is None:
        return

    message = build_message(data)
    print("送信内容プレビュー：")
    print("─" * 40)
    print(message)
    print("─" * 40)
    send_line(message)


if __name__ == "__main__":
    main()
