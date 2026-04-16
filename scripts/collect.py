"""
collect.py - 健康Tips収集スクリプト
sources.yaml に従い各ソースからRaw情報を取得し output/daily/ に保存する
"""

import os
import json
import datetime
import feedparser
import requests
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
CONFIG_PATH = BASE_DIR / "config" / "sources.yaml"
OUTPUT_DIR = BASE_DIR / "output" / "daily"

_raw_pubmed_key = os.getenv("PUBMED_API_KEY", "")
PUBMED_API_KEY = _raw_pubmed_key if _raw_pubmed_key and _raw_pubmed_key != "your_key_here" else ""

WEEKDAY_MAP = {
    0: "monday",
    1: "tuesday",
    2: "wednesday",
    3: "thursday",
    4: "friday",
    5: "saturday",
    6: "sunday",
}

CATEGORY_SEARCH_TERMS = {
    "食事・栄養": "nutrition diet health",
    "運動・リハビリ": "exercise rehabilitation physical therapy",
    "睡眠・休養": "sleep rest recovery",
    "メンタル・ストレス": "mental health stress",
    "メンタル": "mental health stress",
    "睡眠": "sleep quality insomnia",
    "運動": "exercise physical activity",
    "予防・生活習慣": "disease prevention lifestyle",
    "骨・関節・筋肉": "bone joint muscle musculoskeletal",
    "食事": "nutrition healthy eating",
    "自由テーマ": "health wellness tips",
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


HEALTH_KEYWORDS = [
    "健康", "医療", "病気", "症状", "治療", "予防", "栄養", "食事", "運動", "睡眠",
    "リハビリ", "筋肉", "骨", "関節", "血圧", "血糖", "心臓", "脳", "がん", "癌",
    "ストレス", "メンタル", "免疫", "体重", "肥満", "糖尿病", "高血圧", "認知症",
    "転倒", "骨折", "筋力", "体力", "ウォーキング", "サプリ", "ビタミン",
    "health", "medical", "exercise", "nutrition", "sleep", "diet",
]


def is_health_related(entry: dict) -> bool:
    """記事が健康・医療関連かどうかを判定する"""
    text = (entry.get("title", "") + " " + entry.get("summary", "")).lower()
    return any(kw.lower() in text for kw in HEALTH_KEYWORDS)


def fetch_rss(source: dict) -> list[dict]:
    """RSSフィードから健康関連記事を取得する"""
    try:
        feed = feedparser.parse(source["url"])
        articles = []
        for entry in feed.entries[:20]:  # 多めに取得してフィルタリング
            if not is_health_related(entry):
                continue
            articles.append({
                "title": entry.get("title", ""),
                "summary": entry.get("summary", ""),
                "link": entry.get("link", ""),
                "source": source["name"],
                "reliability": source["reliability"],
            })
            if len(articles) >= 5:
                break
        print(f"  {source['name']}: {len(articles)} 件（健康関連）")
        return articles
    except Exception as e:
        print(f"RSS取得エラー ({source['name']}): {e}")
        return []


def fetch_pubmed(category: str, max_results: int = 3) -> list[dict]:
    """PubMed APIからeSummaryで論文タイトル・概要を取得する"""
    search_term = CATEGORY_SEARCH_TERMS.get(category, "health")
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    def add_key(params):
        if PUBMED_API_KEY:
            params["api_key"] = PUBMED_API_KEY
        return params

    try:
        # Step1: IDリスト取得
        search_res = requests.get(
            base_url + "esearch.fcgi",
            params=add_key({"db": "pubmed", "term": search_term, "retmax": max_results,
                             "sort": "relevance", "retmode": "json"}),
            timeout=10,
        )
        ids = search_res.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            print(f"  PubMed ({category}): 0 件")
            return []

        # Step2: eSummaryでタイトル・著者・掲載誌を取得
        summary_res = requests.get(
            base_url + "esummary.fcgi",
            params=add_key({"db": "pubmed", "id": ",".join(ids), "retmode": "json"}),
            timeout=10,
        )
        result = summary_res.json().get("result", {})

        articles = []
        for uid in ids:
            item = result.get(uid, {})
            title = item.get("title", "").rstrip(".")
            source_name = item.get("source", "PubMed")  # 掲載誌名
            pub_date = item.get("pubdate", "")
            # 著者リスト（最大3名）
            authors = item.get("authors", [])
            author_str = "、".join([a.get("name", "") for a in authors[:3]])
            summary = f"掲載誌：{source_name}（{pub_date}）"
            if author_str:
                summary += f" / 著者：{author_str}"

            articles.append({
                "title": title,
                "summary": summary,
                "link": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
                "source": f"PubMed / {source_name}",
                "reliability": "★★★",
            })

        print(f"  PubMed ({category}): {len(articles)} 件")
        return articles
    except Exception as e:
        print(f"PubMed取得エラー ({category}): {e}")
        return []


def collect_for_date(date: datetime.date) -> dict:
    """指定日のTips候補を収集する"""
    config = load_config()
    weekday = WEEKDAY_MAP[date.weekday()]
    categories = config["categories"][weekday]

    raw_data = {
        "date": date.isoformat(),
        "weekday": weekday,
        "categories": categories,
        "candidates": [],
    }

    # RSSソースから収集
    for source in config["sources"]["rss"]:
        articles = fetch_rss(source)
        for article in articles:
            article["fetch_type"] = "rss"
            raw_data["candidates"].append(article)

    # PubMedから各カテゴリ分収集
    for category in categories:
        articles = fetch_pubmed(category, max_results=2)
        for article in articles:
            article["fetch_type"] = "pubmed"
            article["target_category"] = category
            raw_data["candidates"].append(article)

    return raw_data


def save_raw(data: dict, date: datetime.date):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = OUTPUT_DIR / f"{date.isoformat()}_raw.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"保存完了: {raw_path}")
    return raw_path


def main():
    today = datetime.date.today()
    print(f"収集開始: {today}")
    data = collect_for_date(today)
    path = save_raw(data, today)
    print(f"候補数: {len(data['candidates'])} 件")
    return path


if __name__ == "__main__":
    main()
