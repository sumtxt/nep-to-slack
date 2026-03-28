import os
import sys

from nep import fetch, deduplicate, post_to_slack

MEMORY_FILE = "memory/url.txt"


def main() -> None:
    nep_name = os.environ.get("NEP_NAME", "nep-mig")
    webhook_url = os.environ.get("SLACK_WEBHOOK")
    skip_dedup = os.environ.get("SKIP_DEDUP", "false").lower() == "true"

    if not webhook_url:
        sys.exit("SLACK_WEBHOOK environment variable is not set.")

    print(f"Fetching {nep_name}...")
    data = fetch(nep_name)
    papers = data["papers"]
    print(f"Found {len(papers)} papers in issue: {data['update']}")

    if skip_dedup:
        new_papers = papers
        print("Deduplication skipped.")
    else:
        new_papers = deduplicate(papers, MEMORY_FILE)
        print(f"{len(new_papers)} new papers after deduplication.")

    if not new_papers:
        print("Nothing to post.")
        return

    post_to_slack(new_papers, webhook_url, MEMORY_FILE)
    print(f"Posted {len(new_papers)} papers.")


if __name__ == "__main__":
    main()
