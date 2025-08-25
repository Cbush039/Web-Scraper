from __future__ import annotations
import argparse
import csv
import json
import re
import time
from dataclasses import dataclass, asdict
from typing import Iterable, List, Dict, Any, Optional

import requests

ITUNES_SEARCH = "https://itunes.apple.com/search"
ITUNES_LOOKUP = "https://itunes.apple.com/lookup"
REVIEWS_RSS   = "https://itunes.apple.com/rss/customerreviews/page={page}/id={id}/sortby=mostrecent/json"

UA = "Mozilla/5.0 (compatible; AppDiscovery/1.1; +https://example.com)"

@dataclass
class App:
    app_id: int
    name: str
    bundle_id: str
    seller_name: str
    url: str
    average_rating: float
    rating_count: int
    price: float
    currency: str
    primary_genre: str
    genres: List[str]


def _req(url: str, params: Optional[Dict[str, Any]] = None, sleep: float = 0.4) -> requests.Response:
    headers = {"User-Agent": UA}
    resp = requests.get(url, params=params, headers=headers, timeout=20)
    time.sleep(sleep)
    resp.raise_for_status()
    return resp


def search_apps_by_terms(terms: Iterable[str], country: str = "us", limit_per_term: int = 50) -> List[App]:
    results: Dict[int, App] = {}
    for raw_term in terms:
        term = raw_term.strip()
        if not term:
            continue
        params = {
            "term": term,
            "country": country,
            "entity": "software",
            "limit": limit_per_term,
        }
        r = _req(ITUNES_SEARCH, params)
        data = r.json()
        for it in data.get("results", []):
            if it.get("kind") != "software":
                continue
            app = App(
                app_id=it.get("trackId"),
                name=it.get("trackName", ""),
                bundle_id=it.get("bundleId", ""),
                seller_name=it.get("sellerName", ""),
                url=it.get("trackViewUrl", ""),
                average_rating=float(it.get("averageUserRating", it.get("averageUserRatingForCurrentVersion", 0)) or 0.0),
                rating_count=int(it.get("userRatingCount", it.get("userRatingCountForCurrentVersion", 0)) or 0),
                price=float(it.get("price", 0.0) or 0.0),
                currency=it.get("currency", "USD"),
                primary_genre=it.get("primaryGenreName", ""),
                genres=it.get("genres", []) or [],
            )
            if app.app_id:
                results[app.app_id] = app
    return list(results.values())


def lookup_app_by_bundle(bundle_id: str, country: str = "us") -> Optional[App]:
    params = {"bundleId": bundle_id, "country": country}
    r = _req(ITUNES_LOOKUP, params)
    data = r.json()
    for it in data.get("results", []):
        if it.get("kind") == "software":
            return App(
                app_id=it.get("trackId"),
                name=it.get("trackName", ""),
                bundle_id=it.get("bundleId", ""),
                seller_name=it.get("sellerName", ""),
                url=it.get("trackViewUrl", ""),
                average_rating=float(it.get("averageUserRating", it.get("averageUserRatingForCurrentVersion", 0)) or 0.0),
                rating_count=int(it.get("userRatingCount", it.get("userRatingCountForCurrentVersion", 0)) or 0),
                price=float(it.get("price", 0.0) or 0.0),
                currency=it.get("currency", "USD"),
                primary_genre=it.get("primaryGenreName", ""),
                genres=it.get("genres", []) or [],
            )
    return None


def fetch_reviews(app_id: int, country: str = "us", max_pages: int = 5) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for page in range(1, max_pages + 1):
        url = REVIEWS_RSS.format(page=page, id=app_id)
        r = _req(url, params={"cc": country})
        data = r.json()
        feed = data.get("feed", {})
        entries = feed.get("entry", [])
        if entries and isinstance(entries, list) and isinstance(entries[0], dict) and entries[0].get("im:name"):
            entries = entries[1:]
        if not entries:
            break
        for e in entries:
            out.append({
                "title": (e.get("title", {}) or {}).get("label", ""),
                "content": (e.get("content", {}) or {}).get("label", ""),
                "rating": int(((e.get("im:rating", {}) or {}).get("label", 0)) or 0),
                "author": ((e.get("author", {}) or {}).get("name", {}) or {}).get("label", ""),
                "updated": (e.get("updated", {}) or {}).get("label", ""),
            })
    return out


def phrases_match(text: str, phrases_any: List[str], phrases_all: List[str]) -> Dict[str, Any]:
    text_low = text.lower()
    matched_any = []
    for p in phrases_any:
        p = p.strip().lower()
        if not p:
            continue
        if re.search(re.escape(p), text_low):
            matched_any.append(p)
    for p in phrases_all:
        p = p.strip().lower()
        if not p:
            continue
        if re.search(re.escape(p), text_low) is None:
            return {"ok": False, "any": matched_any}
    return {"ok": (len(phrases_any) == 0 or len(matched_any) > 0), "any": matched_any}


def find_candidates(
    seed_terms: Iterable[str],
    country: str = "us",
    min_rating: float = 4.5,
    min_ratings_count: int = 100,
    phrases_any: Optional[List[str]] = None,
    phrases_all: Optional[List[str]] = None,
    max_review_pages: int = 3,
) -> List[Dict[str, Any]]:
    phrases_any = phrases_any or []
    phrases_all = phrases_all or []

    apps = search_apps_by_terms(seed_terms, country=country)

    pre = [a for a in apps if (a.average_rating or 0) >= min_rating and (a.rating_count or 0) >= min_ratings_count]

    results: List[Dict[str, Any]] = []
    for app in pre:
        reviews = fetch_reviews(app.app_id, country=country, max_pages=max_review_pages)
        matched_reviews = []
        for rv in reviews:
            m = phrases_match(rv.get("title", "") + "\n" + rv.get("content", ""), phrases_any, phrases_all)
            if m["ok"] and (not phrases_any or m["any"]):
                snippet = (rv.get("content") or rv.get("title") or "").strip().replace("\n", " ")
                if len(snippet) > 180:
                    snippet = snippet[:177] + "..."
                matched_reviews.append({
                    "matched_any": ", ".join(sorted(set(m["any"]))),
                    "rating": rv.get("rating"),
                    "snippet": snippet,
                    "updated": rv.get("updated"),
                })
        if matched_reviews:
            results.append({
                **asdict(app),
                "matched_count": len(matched_reviews),
                "examples": matched_reviews[:5],
            })
    results.sort(key=lambda r: (r.get("matched_count", 0), r.get("rating_count", 0)), reverse=True)
    return results


def export_csv(rows: List[Dict[str, Any]], path: str) -> None:
    if not rows:
        headers = [
            "app_id","name","bundle_id","seller_name","url","average_rating","rating_count","price","currency","primary_genre","genres","matched_count","examples"
        ]
        with open(path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(headers)
        return
    rows_out = []
    for r in rows:
        r2 = r.copy()
        r2["genres"] = ", ".join(r2.get("genres", []) or [])
        r2["examples"] = json.dumps(r2.get("examples", []), ensure_ascii=False)
        rows_out.append(r2)
    headers = list(rows_out[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        w.writerows(rows_out)


def parse_csv_list(s: str) -> List[str]:
    return [x.strip() for x in s.split(",") if x.strip()]


def main():
    ap = argparse.ArgumentParser(description="Discover high-rated iOS apps with review-keyword filters")
    ap.add_argument("-t", "--terms", type=str, default="", help="Comma-separated search terms (e.g., 'budget,planner,notes')")
    ap.add_argument("-b", "--bundle", type=str, default="", help="Optional single bundleId to lookup (e.g., com.todoist.Todoist)")
    ap.add_argument("-c", "--country", type=str, default="us", help="Storefront country code (us, gb, de, etc.)")
    ap.add_argument("-r", "--min-rating", type=float, default=4.5, help="Minimum average star rating")
    ap.add_argument("-R", "--min-ratings", type=int, default=100, help="Minimum rating count")
    ap.add_argument("-a", "--phrases-any", type=str, default="", help="Comma-separated list; match if ANY phrase appears in a review")
    ap.add_argument("-A", "--phrases-all", type=str, default="", help="Comma-separated list; match only if ALL phrases appear in a review")
    ap.add_argument("-M", "--max-review-pages", type=int, default=3, help="How many review pages to fetch per app (≈50 reviews/page)")
    ap.add_argument("-o", "--out", type=str, default="appstore_candidates.csv", help="CSV path to write")

    args = ap.parse_args()

    phrases_any = parse_csv_list(args.phrases_any)
    phrases_all = parse_csv_list(args.phrases_all)

    seed_terms: List[str] = []
    if args.terms:
        seed_terms = parse_csv_list(args.terms)

    candidates: List[Dict[str, Any]] = []

    if args.bundle:
        app = lookup_app_by_bundle(args.bundle, country=args.country)
        if app and app.average_rating >= args.min_rating and app.rating_count >= args.min_ratings:
            reviews = fetch_reviews(app.app_id, country=args.country, max_pages=args.max_review_pages)
            matched_reviews = []
            for rv in reviews:
                m = phrases_match(rv.get("title", "") + "\n" + rv.get("content", ""), phrases_any, phrases_all)
                if m["ok"] and (not phrases_any or m["any"]):
                    snippet = (rv.get("content") or rv.get("title") or "").strip().replace("\n", " ")
                    if len(snippet) > 180:
                        snippet = snippet[:177] + "..."
                    matched_reviews.append({
                        "matched_any": ", ".join(sorted(set(m["any"]))),
                        "rating": rv.get("rating"),
                        "snippet": snippet,
                        "updated": rv.get("updated"),
                    })
            if matched_reviews:
                row = {**asdict(app), "matched_count": len(matched_reviews), "examples": matched_reviews[:5]}
                candidates.append(row)
    else:
        if not seed_terms:
            print("Provide --terms or --bundle", flush=True)
            return
        candidates = find_candidates(
            seed_terms=seed_terms,
            country=args.country,
            min_rating=args.min_rating,
            min_ratings_count=args.min_ratings,
            phrases_any=phrases_any,
            phrases_all=phrases_all,
            max_review_pages=args.max_review_pages,
        )

    export_csv(candidates, args.out)
    print(f"Wrote {len(candidates)} candidate apps → {args.out}")


if __name__ == "__main__":
    main()
