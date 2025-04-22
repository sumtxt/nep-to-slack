NEP to Slack Tool
===================

This simple tool automates the process of fetching the latest issue of [NEP: New Economics Papers](https://nep.repec.org/) and posts the papers to a Slack channel via a workflow webhook. The script checks NEP every day at 23:50 UTC for new issues.

To use this tool for your own Slack, clone this repository and navigate to Security > Secrets and Variables > Actions. Set the SLACK_WEBHOOK as a repository secret with your webhook.