import os
import re
import time

import requests
from bs4 import BeautifulSoup, Tag
from openai import OpenAI

RATE_LIMIT_WINDOW_SECONDS = 60
MEMORY_FILE = "memory/url.txt"


def _strip(s: str | None) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", s).strip()


def _extract_field(rows: list[str], prefix: str) -> str:
    match = next((r for r in rows if r.startswith(prefix)), "")
    return match[len(prefix):].strip() if match else ""


def fetch(nep_name: str) -> dict:
    """Fetch and parse the latest issue of a NEP report.

    Returns a dict with keys:
      - ``update``: issue date string from the page title
      - ``papers``: list of paper dicts
    """
    url = f"https://nep.repec.org/{nep_name}/latest"
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    title_tag = soup.find("title")
    update = re.sub(rf"{re.escape(nep_name)}\s*\|.*", "", title_tag.get_text()).strip() if title_tag else ""

    papers = [_parse_paper(li) for li in soup.select(".coblo_li")]
    return {"update": update, "papers": papers}


def _parse_paper(li: Tag) -> dict:
    head = li.find("div")
    a = head.find("a") if head else None
    title = _strip(a.get_text()) if a else ""
    url = a["href"] if a else ""

    rows = [_strip(tr.get_text()) for tr in li.find_all("tr")]
    return {
        "title": title,
        "authors": _extract_field(rows, "By:"),
        "created": _extract_field(rows, "Date:"),
        "abstract": _extract_field(rows, "Abstract:"),
        "url": url,
    }


def load_seen_urls(memory_file: str = MEMORY_FILE) -> set[str]:
    try:
        with open(memory_file) as f:
            return {line.strip() for line in f if line.strip()}
    except FileNotFoundError:
        return set()


def save_urls(urls: list[str], memory_file: str = MEMORY_FILE) -> None:
    os.makedirs(os.path.dirname(memory_file), exist_ok=True)
    with open(memory_file, "a") as f:
        for url in urls:
            f.write(url + "\n")


def deduplicate(papers: list[dict], memory_file: str = MEMORY_FILE) -> list[dict]:
    seen = load_seen_urls(memory_file)
    return [p for p in papers if p["url"] not in seen]


def post_to_slack(
    papers: list[dict],
    webhook_url: str,
    memory_file: str = MEMORY_FILE,
    wait_seconds: int = 2,
    rate_limit: int = 10,
) -> None:
    """Post papers to Slack, respecting rate limits.

    Saves each URL to the memory file immediately after a successful post
    so that a mid-run failure does not cause already-posted papers to be
    posted again on the next run.
    """
    n = len(papers)
    start = time.time()

    for i, paper in enumerate(papers, start=1):
        print(".", end="", flush=True)
        resp = requests.post(webhook_url, json=paper, timeout=10)

        if resp.status_code != 200 or not resp.json().get("ok"):
            raise RuntimeError(f"Slack error {resp.status_code}: {resp.text!r}")

        save_urls([paper["url"]], memory_file)

        if i % rate_limit == 0:
            elapsed = time.time() - start
            time.sleep(max(0.0, RATE_LIMIT_WINDOW_SECONDS - elapsed))
            start = time.time()
        elif i < n:
            time.sleep(wait_seconds)

    print()


def classify_paper(paper: dict, prompt: str, api_key: str, model: str = "gpt-4o-mini") -> bool:
    """Classify a paper using an LLM to check if it matches the research area.

    Args:
        paper: Paper dict with title, authors, abstract, etc.
        prompt: User-defined prompt describing the research area of interest.
        api_key: OpenAI API key.
        model: OpenAI model to use (default: gpt-4o-mini).

    Returns:
        True if the paper is relevant, False otherwise.
    """
    client = OpenAI(api_key=api_key)

    system_message = prompt

    user_message = f"""Paper to classify: Title: {paper['title']} Abstract: {paper['abstract']} """

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message},
        ],
        max_tokens=10,
        temperature=0,
    )

    answer = response.choices[0].message.content.strip().upper()
    return answer == "YES"


def classify_papers(
    papers: list[dict],
    prompt: str,
    api_key: str,
    model: str = "gpt-4o-mini",
) -> list[dict]:
    """Filter papers based on LLM classification.

    Args:
        papers: List of paper dicts.
        prompt: User-defined prompt describing the research area of interest.
        api_key: OpenAI API key.
        model: OpenAI model to use.

    Returns:
        List of papers that match the research area.
    """
    relevant = []
    for paper in papers:
        try:
            if classify_paper(paper, prompt, api_key, model):
                relevant.append(paper)
                print(f"  [RELEVANT] {paper['title'][:60]}...")
            else:
                print(f"  [SKIPPED] {paper['title'][:60]}...")
        except Exception as e:
            print(f"  [ERROR] {paper['title'][:60]}... - {e}")
            relevant.append(paper)
    return relevant
