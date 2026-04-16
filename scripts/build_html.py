"""
build_html.py - JSONデータをnote風HTMLビューアに変換するスクリプト
"""

import json
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "viewer.html"
DAILY_DIR = BASE_DIR / "output" / "daily"
HTML_DIR = BASE_DIR / "output" / "html"
ICLOUD_DIR = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs/健康Tips"


def load_tips(date: datetime.date) -> dict | None:
    path = DAILY_DIR / f"{date.isoformat()}.json"
    if not path.exists():
        print(f"Tipsデータが見つかりません: {path}")
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_template() -> str:
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"テンプレートが見つかりません: {TEMPLATE_PATH}")
    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        return f.read()


def render_html(template: str, data: dict) -> str:
    """テンプレートにTipsデータを流し込む"""
    tips = data["tips"]
    date_str = data["date"]

    # カード一覧HTML生成
    cards_html = ""
    for i, tip in enumerate(tips):
        stars = tip.get("stars", "★")
        cards_html += f"""
        <div class="tip-card" onclick="showDetail({i})">
          <div class="card-category">{tip.get('category', '')}</div>
          <div class="card-title">{tip.get('title', '')}</div>
          <div class="card-lead">{tip.get('core', '')[:60]}...</div>
          <div class="card-stars">{stars}</div>
        </div>"""

    # 詳細HTML生成
    details_html = ""
    for i, tip in enumerate(tips):
        tags_html = " ".join(tip.get("tags", []))
        post_text = tip.get("post", "").replace("\n", "\\n").replace('"', '\\"')
        details_html += f"""
        <div class="tip-detail" id="detail-{i}" style="display:none;">
          <div class="detail-category">{tip.get('category', '')}</div>
          <h2 class="detail-title">{tip.get('title', '')}</h2>
          <div class="detail-author">すえ / 理学療法士 / Fukui</div>

          <div class="detail-section core-section">
            <h3>📌 今日のTips</h3>
            <p>{tip.get('core', '')}</p>
          </div>

          <div class="detail-section">
            <h3>🔍 もう少し詳しく</h3>
            <p>{tip.get('detail', '')}</p>
          </div>

          <div class="detail-section pt-section">
            <h3>💬 PTすえのひとこと</h3>
            <p>{tip.get('pt', '')}</p>
          </div>

          <div class="detail-section post-section">
            <h3>📣 リベシティ投稿用</h3>
            <div class="post-text" id="post-{i}">{tip.get('post', '')}</div>
            <button class="copy-btn" onclick="copyPost({i})">コピー</button>
          </div>

          <div class="detail-meta">
            <span>情報源：{tip.get('source', '')}</span>
            <span>信頼度：{tip.get('stars', '')}（{tip.get('reliability', '')}）</span>
          </div>
          <div class="detail-tags">{tags_html}</div>

          <div class="detail-nav">
            {"" if i == 0 else f'<button onclick="showDetail({i-1})">← 前のTips</button>'}
            <button onclick="showList()">一覧に戻る</button>
            {"" if i >= len(tips)-1 else f'<button onclick="showDetail({i+1})">次のTips →</button>'}
          </div>
        </div>"""

    # テンプレートに置換
    html = template
    html = html.replace("{{DATE}}", date_str)
    html = html.replace("{{CARDS}}", cards_html)
    html = html.replace("{{DETAILS}}", details_html)
    html = html.replace("{{TIPS_JSON}}", json.dumps(tips, ensure_ascii=False))

    return html


def build(date: datetime.date) -> Path | None:
    data = load_tips(date)
    if data is None:
        return None

    template = load_template()
    html = render_html(template, data)

    filename = f"{date.isoformat()}.html"

    # output/html/ に保存
    HTML_DIR.mkdir(parents=True, exist_ok=True)
    out_path = HTML_DIR / filename
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML生成完了: {out_path}")

    # iCloud Drive / 健康Tips/ にも保存（iPhoneの「ファイル」アプリで開ける）
    try:
        ICLOUD_DIR.mkdir(parents=True, exist_ok=True)
        icloud_path = ICLOUD_DIR / filename
        with open(icloud_path, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"iCloud Drive保存完了: {icloud_path}")
    except Exception as e:
        print(f"iCloud Drive保存スキップ: {e}")

    return out_path


def main():
    today = datetime.date.today()
    print(f"HTML生成開始: {today}")
    build(today)


if __name__ == "__main__":
    main()
