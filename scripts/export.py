"""
export.py - 週次まとめMarkdownを生成し、ブログ投稿下書きを出力する（Phase 2以降）
"""

import json
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DAILY_DIR = BASE_DIR / "output" / "daily"
WEEKLY_DIR = BASE_DIR / "output" / "weekly"


def get_week_dates(sunday: datetime.date) -> list[datetime.date]:
    """日曜日を週末として、その週（月〜日）の日付リストを返す"""
    monday = sunday - datetime.timedelta(days=6)
    return [monday + datetime.timedelta(days=i) for i in range(7)]


def load_week_tips(sunday: datetime.date) -> list[dict]:
    """1週間分のTipsをロードする"""
    dates = get_week_dates(sunday)
    all_tips = []
    for date in dates:
        path = DAILY_DIR / f"{date.isoformat()}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for tip in data.get("tips", []):
                    tip["date"] = date.isoformat()
                    all_tips.append(tip)
    return all_tips


def generate_weekly_summary(tips: list[dict], week_str: str) -> str:
    """週次まとめMarkdownを生成する（テンプレートベース）"""
    lines = [f"## 週次まとめ {week_str}\n"]

    # カテゴリ別に整理
    by_category: dict[str, list[dict]] = {}
    for tip in tips:
        cat = tip.get("category", "その他")
        by_category.setdefault(cat, []).append(tip)

    lines.append("### 今週のTips一覧\n")
    for cat, cat_tips in by_category.items():
        lines.append(f"#### {cat}")
        for t in cat_tips:
            lines.append(f"- **[{t.get('date')}] {t.get('title', '')}**")
            lines.append(f"  {t.get('core', '')}")
        lines.append("")

    lines.append("### 今週のまとめ\n")
    lines.append("今週も毎日の健康Tipsをお届けしました。")
    lines.append("小さな習慣の積み重ねが、10年後の体を作ります。")
    lines.append("来週もよろしくお願いします！ — PTすえ\n")

    return "\n".join(lines)


def export_weekly(sunday: datetime.date | None = None):
    if sunday is None:
        today = datetime.date.today()
        days_since_sunday = (today.weekday() + 1) % 7
        sunday = today - datetime.timedelta(days=days_since_sunday)

    year, week_num, _ = sunday.isocalendar()
    week_str = f"{year}-W{week_num:02d}"
    print(f"週次まとめ生成: {week_str}")

    tips = load_week_tips(sunday)
    if not tips:
        print("Tipsデータがありません")
        return

    print(f"取得Tips数: {len(tips)} 件")
    summary = generate_weekly_summary(tips, week_str)

    WEEKLY_DIR.mkdir(parents=True, exist_ok=True)
    out_path = WEEKLY_DIR / f"{week_str}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# 週次まとめ {week_str}\n\n")
        f.write(summary)

    print(f"保存完了: {out_path}")
    return out_path


def main():
    export_weekly()


if __name__ == "__main__":
    main()
