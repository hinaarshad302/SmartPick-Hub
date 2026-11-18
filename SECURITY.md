# Security Policy

## Supported project version

Security fixes should be reported against the latest code in the project-foundation branch until a release process is established.

## Reporting a vulnerability

Please do not publish passwords, API keys, access tokens, private subscriber information, or exploitable vulnerability details in a public issue.

Use GitHub's private vulnerability reporting feature for this repository when it is enabled. If private reporting is unavailable, contact the repository owner through a verified private channel before sharing technical details.

Include:
- A short description of the issue and its possible impact.
- The affected page, endpoint, or file.
- Reproduction steps that do not expose real user data.
- Any suggested mitigation.

## Secret handling

- Never commit .env files, Supabase secret/service-role keys, Resend API keys, or deployment tokens.
- Browser code may contain only the Supabase publishable key.
- If a secret is exposed, revoke or rotate it immediately in its provider dashboard; removing it from Git history alone is not enough.
- Do not use real subscriber or account data in test reports or screenshots.

## Current limitations

SmartPick Hub is under active development and is not production-ready. Database migrations, access policies, provider configuration, and browser flows must be tested in the actual deployment environment before public launch.
