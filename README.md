NEP to Slack
============

Fetches the latest issue of a [NEP: New Economics Papers](https://nep.repec.org/) report and posts each paper to a Slack channel via a workflow webhook. Runs daily. Papers are deduplicated against a memory file (one per NEP report, e.g., `memory/nep-mig.txt`) so nothing is posted twice. Optionally, papers can be filtered using an OpenAI LLM classifier to only post papers relevant to a specific research area. Papers rejected by the classifier are still saved to the memory file to avoid re-evaluating them on subsequent runs.

## Workflows

There are two GitHub Actions workflows:

1. **nep-mig** - Posts papers from the NEP Migration report without classification
2. **nep-ecm** - Posts papers from the NEP Econometrics report with OpenAI classification

## Setup

Go to **Settings → Secrets and Variables → Actions** and add the following repository secrets:

### nep-mig workflow

| Secret | Description |
|---|---|
| `SLACK_WEBHOOK_MIG` | Slack webhook URL for nep-mig papers |

### nep-ecm workflow

**Secrets:**

| Secret | Description |
|---|---|
| `SLACK_WEBHOOK_ECM` | Slack webhook URL for nep-ecm papers |
| `OPENAI_API_KEY` | OpenAI API key for classification |

**Variables:**

| Variable | Description |
|---|---|
| `CLASSIFIER_PROMPT_ECM` | Prompt for the classifier |
