# Security Policy

## Supported Versions

The `1.0.0` submission is the actively maintained line. Security fixes land on
`main` and are rolled into the next tagged release.

| Version | Supported |
| ------- | --------- |
| 1.0.x   | ✅        |

## Reporting a Vulnerability

Please report suspected vulnerabilities **privately** — do not open a public
GitHub issue for security matters.

- **Email:** ritik.prajapat@thinktaurus.com
- Include: a description of the issue, affected endpoint or module, and clear
  reproduction steps (a minimal request/payload is ideal).

### What to expect

- **Acknowledgement:** within **3 business days** of your report.
- **Initial assessment:** within **7 business days**, including whether we can
  reproduce the issue and its expected severity.
- **Fix & disclosure:** we aim to ship a fix within **30 days** for confirmed
  issues and will coordinate a disclosure timeline with you.

Please give us a reasonable window to remediate before any public disclosure.

## Handling of Secrets

- The Gemini API key is read **only** from the `GEMINI_API_KEY` environment
  variable (see [`app/config.py`](app/config.py)) and never leaves the server
  process or appears in API responses.
- `.env` is git-ignored; never commit real credentials. Use
  [`.env.example`](.env.example) as the template.
