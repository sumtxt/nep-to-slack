NEP to Slack
============

Fetches the latest issue of a [NEP: New Economics Papers](https://nep.repec.org/) report and posts each paper to a Slack channel via a workflow webhook. Runs daily at 23:55 UTC. Papers are deduplicated against a memory file so nothing is posted twice.

## Setup

1. Clone this repository.
2. Go to **Settings → Secrets and Variables → Actions** and add `SLACK_WEBHOOK` as a repository secret.

## Running manually

Trigger the workflow from **Actions → NEP to Slack → Run workflow**. Available inputs:

| Input | Default | Description |
|---|---|---|
| `nep_name` | `nep-mig` | NEP report identifier (e.g. `nep-env`, `nep-lab`) |
| `skip_dedup` | `false` | Set to `true` to post all papers regardless of memory |
