import os
import sys

from nep import fetch, deduplicate, post_to_slack, classify_papers, save_urls


def main() -> None:
    nep_name = os.environ.get("NEP_NAME")
    webhook_url = os.environ.get("SLACK_WEBHOOK")
    skip_dedup = os.environ.get("SKIP_DEDUP", "").lower() == "true"
    skip_classifier = os.environ.get("SKIP_CLASSIFIER", "").lower() == "true"
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    classifier_prompt = os.environ.get("CLASSIFIER_PROMPT")
    openai_model = os.environ.get("OPENAI_MODEL")

    memory_file = f"memory/{nep_name}.txt"

    if not nep_name:
        sys.exit("NEP_NAME environment variable is not set.")
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
        new_papers = deduplicate(papers, memory_file)
        print(f"{len(new_papers)} new papers after deduplication.")

    if not new_papers:
        print("Nothing to post.")
        return

    if not skip_classifier:
        if not openai_api_key:
            sys.exit("OPENAI_API_KEY environment variable is not set but classifier is enabled.")
        if not classifier_prompt:
            sys.exit("CLASSIFIER_PROMPT environment variable is not set but classifier is enabled.")
        if not openai_model:
            sys.exit("OPENAI_MODEL environment variable is not set but classifier is enabled.")

        print(f"Classifying papers with {openai_model}...")
        # Save all deduplicated URLs to memory before classification
        # This ensures skipped papers won't be re-evaluated next run
        save_urls([p["url"] for p in new_papers], memory_file)
        new_papers = classify_papers(new_papers, classifier_prompt, openai_api_key, openai_model)
        print(f"{len(new_papers)} relevant papers after classification.")

        if not new_papers:
            print("No relevant papers to post.")
            return
    else:
        print("OpenAI classifier skipped.")

    post_to_slack(new_papers, webhook_url, memory_file)
    print(f"Posted {len(new_papers)} papers.")


if __name__ == "__main__":
    main()
