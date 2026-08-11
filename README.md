# Odia Bhagabata Gita - Facebook Daily Auto Post

This repository automatically creates and publishes one devotional Odia post to the Facebook Page using OpenAI and the Meta Graph API.

## Repository structure

```text
odiabhagabat-git/
├── main.py
├── requirements.txt
├── README.md
└── .github/
    └── workflows/
        └── main.yml
```

## GitHub Secrets

Repository → Settings → Secrets and variables → Actions → New repository secret:

- `OPENAI_API_KEY`
- `META_PAGE_ID`
- `META_PAGE_ACCESS_TOKEN`

Never put tokens directly in the source code.

## Schedule

The workflow runs daily at 07:30 AM India Standard Time (IST), and can also be started manually from GitHub Actions using **Run workflow**.

## Meta permissions

Use a Page Access Token with the permissions required by your Meta app/Page setup for publishing Page content, including the appropriate Pages management/publishing permissions.
