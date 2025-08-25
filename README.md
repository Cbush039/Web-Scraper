ALL OF THIS IS IN THE MD BUT HERE IS ALSO ACCESSIBLE

# App Store Scraper – Usage & Reference Guide

This guide explains how to install, run, and extend the `web_scraper.py` tool for discovering iOS apps that meet rating and review‑keyword criteria. It includes Windows‑specific notes, a full flag reference, example commands, troubleshooting tips, and guidelines for safe/ethical use.

---

## 1) What the scraper does (in plain English)

* Searches Apple’s App Store using public iTunes endpoints.
* Filters apps by **average rating** and **rating count** (e.g., ≥4.5 stars and ≥200 ratings).
* Fetches recent **customer reviews** and matches **keywords/phrases** (e.g., “hidden gem”, “rare find”).
* Outputs a **CSV** listing matched apps with sample review snippets.

> The tool is designed for **discovery**—surfacing high‑quality apps that under‑index on marketing but over‑deliver for users.

---

## 2) Installation

**Prereqs**

* Python 3.9+ (Windows/macOS/Linux)
* `requests` library

**Install dependencies**

```bash
pip install requests
```

> Windows tip: If you have multiple Python versions, ensure you’re using the one shown in VS Code via **Python: Select Interpreter**.

---

## 3) Running the scraper

### Windows (PowerShell) – recommended patterns

Always call Python explicitly; do **not** use `/usr/bin/env` on Windows.

**Basic discovery (no phrases):**

```powershell
python .\web_scraper.py -t "budget,calendar,notes" -c us -r 4.5 -R 200
```

**With review keyword(s):**

```powershell
python .\web_scraper.py -t "habit tracker,productivity" -r 4.5 -R 200 -a "hidden gem,rare find"
```

**Single known app by bundle id:**

```powershell
python .\web_scraper.py -b com.todoist.Todoist -r 4.5 -R 200 -a "underrated,hidden gem"
```

### Windows (cmd.exe)

```cmd
python web_scraper.py -t "fitness,wellness" -c us -r 4.3 -R 100
```

### macOS / Linux

```bash
python3 web_scraper.py -t "budget,calendar,notes" -c us -r 4.5 -R 200 -a "hidden gem,rare find"
```

---

## 4) Output

* File: `appstore_candidates.csv` (created in the working directory)
* Columns:

  * `app_id`, `name`, `bundle_id`, `seller_name`, `url`,
  * `average_rating`, `rating_count`, `price`, `currency`,
  * `primary_genre`, `genres`,
  * `matched_count` (reviews that matched your keywords),
  * `examples` (JSON mini‑list with up to 5 review snippets)

Open with Excel/Numbers, or preview in VS Code. You can sort by `matched_count` or `rating_count` to prioritize.

---

## 5) Command‑line flags (short + long)

| Flag | Long                 | Type   | Default                   | Meaning                                                                                 |
| ---- | -------------------- | ------ | ------------------------- | --------------------------------------------------------------------------------------- |
| `-t` | `--terms`            | string | ""                        | Comma‑separated search terms (e.g., `"budget,planner"`). Required unless `-b` is used.  |
| `-b` | `--bundle`           | string | ""                        | Single bundle id to check (e.g., `com.todoist.Todoist`). Bypasses multi‑term discovery. |
| `-c` | `--country`          | string | `us`                      | App Store country/storefront (e.g., `us`, `gb`, `de`).                                  |
| `-r` | `--min-rating`       | float  | `4.5`                     | Minimum average star rating.                                                            |
| `-R` | `--min-ratings`      | int    | `100`                     | Minimum number of user ratings.                                                         |
| `-a` | `--phrases-any`      | string | ""                        | CSV list of phrases; pass if **any** are present in a review.                           |
| `-A` | `--phrases-all`      | string | ""                        | CSV list of phrases; require **all** to appear in the same review.                      |
| `-M` | `--max-review-pages` | int    | `3`                       | Review pages to fetch per app (\~50 reviews per page).                                  |
| `-o` | `--out`              | string | `appstore_candidates.csv` | Output CSV path.                                                                        |

> **Tip:** If you pass both `-a` and `-A`, a review must satisfy `ALL` phrases, and also at least one of the `ANY` phrases (if provided).

---

## 6) Example command recipes

**A. Broad discovery with strong quality gates**

```powershell
python .\web_scraper.py -t "budget,calendar,notes" -r 4.6 -R 500 -M 2 -o results_high_quality.csv
```

**B. Niche hunt by sentiment**

```powershell
python .\web_scraper.py -t "habit tracker,gratitude,journal" -r 4.3 -R 150 -a "hidden gem,underrated,rare find" -o niche_sentiment.csv
```

**C. Validate one app by bundle id**

```powershell
python .\web_scraper.py -b com.example.MyApp -r 4.5 -R 100 -a "life saver,indispensable" -o single_app.csv
```

**D. Sanity check (looser thresholds)**

```powershell
python .\web_scraper.py -t "fitness,health" -r 4.0 -R 50 -a "great"
```

---

## 7) Troubleshooting

**Symptom:** `/usr/bin/env : The term '/usr/bin/env' is not recognized ...`

* Cause: Running a Unix‑style shebang on Windows.
* Fix: Call with `python ...` (PowerShell/cmd) and/or remove the shebang line from the file.

**Symptom:** `Provide --terms or --bundle`

* Cause: No search terms or bundle id provided.
* Fix: Add `-t "term1,term2"` or `-b com.example.App`.

**Symptom:** `SyntaxError: unterminated string literal` around `phrases_match`

* Cause: Broken paste that lost the `"\n"` between title/content.
* Fix: Ensure the line contains `"\n"` exactly: `rv.get("title","") + "\n" + rv.get("content","")`.

**Symptom:** Script runs but CSV is empty

* Cause: Filters too strict (e.g., `-a "hidden gem"` rarely appears verbatim).
* Fix: Loosen thresholds, remove phrases, or use common tokens (e.g., `-a "great,underrated"`).

**Symptom:** Slow run time

* Cause: Each HTTP call sleeps \~0.4s for rate‑limiting; 3 review pages × many apps adds up.
* Fix: Reduce `-M` to 1–2, limit terms, or parallelize in a future enhancement.

---

## 8) Best practices & tips

* **Start broad**, then tighten filters once you see the CSV content.
* Use **multiple related terms** to broaden the candidate pool.
* Prefer **phrases that actually appear** in user reviews; test a few runs to calibrate.
* Sort by `matched_count` and then `rating_count` to find promising apps with social proof.
* Consider **time‑bounded phrases** (add “recent”, “2024”, etc.) only if you also implement date filtering.

---

## 9) Ethical use & Terms of Service

* Respect Apple’s ToS and rate limits.
* Use the data for **research/discovery**; do not attempt to re‑host proprietary content.
* If you scale this up, implement **backoff/retry** and caching; avoid aggressive scraping.

---

## 10) Extending the scraper (roadmap)

* **Free‑only filter:** Keep apps where `price == 0.0`.
* **Genre filters:** Include/exclude based on `primary_genre` or `genres`.
* **Recency gate:** Only count reviews updated in the last N days.
* **Sentiment gate:** Require `rating >= 4` for matching reviews.
* **Negative keyword blacklist:** Exclude reviews containing `ads`, `paywall`, etc.
* **Concurrency:** Speed up with `asyncio`/`httpx` plus polite throttling.
* **Google Play module:** Add parallel discovery for Android.

> If you want, I can add toggles for these (e.g., `--free-only`, `--genre-include`, `--recent-days`, `--min-review-stars`, `--exclude-phrases`).

---

## 11) FAQ

**Q: Can I pass spaces in terms?**
A: Yes, the script splits by commas, so quote the whole list: `-t "personal finance,habit tracker"`.

**Q: Do phrase matches ignore case?**
A: Yes. Matching is case‑insensitive and literal (regex‑escaped).

**Q: Where is the CSV saved?**
A: In your current working directory (the folder shown in your terminal prompt) unless you set `-o` to another path.

**Q: Will this work outside the US store?**
A: Yes—use `-c gb`, `-c de`, etc. Review results vary by storefront.

**Q: How many reviews are checked?**
A: About `50 × M` per app, where `M` is `-M` (default 3 → \~150 reviews/app).

---

## 12) Orientation checklist (what to try first)

1. Run a broad search:

   ```powershell
   python .\web_scraper.py -t "budget,calendar,notes" -r 4.5 -R 200
   ```
2. Add phrases to narrow:

   ```powershell
   python .\web_scraper.py -t "habit tracker,productivity" -r 4.5 -R 200 -a "underrated,rare find"
   ```
3. Inspect `appstore_candidates.csv` and sort by `matched_count`.
4. Iterate: tweak `-t`, `-r`, `-R`, and `-a`/`-A` to hone in on gems.

---

## 13) One‑liner reference (copy‑paste)

```powershell
# Broad search
python .\web_scraper.py -t "budget,calendar,notes" -r 4.5 -R 200

# Phrase‑filtered search
python .\web_scraper.py -t "habit tracker,productivity" -r 4.5 -R 200 -a "hidden gem,rare find"

# Single app by bundle id
python .\web_scraper.py -b com.todoist.Todoist -r 4.5 -R 200 -a "underrated"
```

---

If you want, I can tailor preset command snippets for your exact niches (e.g., education, journaling, finance) and add them to this guide.
