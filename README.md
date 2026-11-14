# SmartPick Hub

**Smart choices. Better living.**

SmartPick Hub is being developed as a bilingual (English and Urdu/Roman Urdu), AI-assisted product discovery and affiliate shopping platform for people in Pakistan and international markets.

The goal is to help visitors make informed decisions by explaining products, comparing suitable options, and considering budget, needs, availability, and important limitations. The business model may include affiliate links. Affiliate relationships must be disclosed clearly, and recommendations must remain relevant to the visitor rather than being ranked only by commission.

> **Project status:** Early development. The current repository contains a static HTML/CSS/JavaScript website, a Supabase browser-authentication integration, and a FastAPI backend prototype for newsletter subscriptions. The full AI shopping assistant, product catalogue, affiliate tracking, and specialist agents are not yet implemented. Do not treat this repository as production-ready.

## Confirmed product direction

- **Audience:** Pakistan and international users.
- **Categories:** Broad product and service categories, introduced gradually after data sources and quality checks are ready.
- **Languages:** English and Urdu/Roman Urdu.
- **Priority:** Balanced user experience, sustainable affiliate revenue, and user trust.

## Planned user experience

1. Discover products and useful buying guides by category.
2. Tell the shopping assistant what they need, their budget, country/region, and preferences.
3. Receive clear explanations and a shortlist of relevant options.
4. Compare products on price, key specifications, availability, limitations, warranty/returns where verifiable, and suitability.
5. Open retailer pages using clearly identified affiliate links where available.
6. Manage an account and optional saved preferences. Personalisation must be consent-based and privacy-aware.

The assistant must explain uncertainty, avoid fabricated specifications or reviews, and direct users to the retailer or manufacturer to verify changing prices and availability.

## Planned AI and automation architecture

A central shopping assistant will coordinate focused services. These are roadmap items, not currently available features:

- **Product Research:** Gather product facts from approved APIs, feeds, or reviewed sources.
- **Comparison:** Compare verified attributes and explain meaningful differences.
- **Budget Advisor:** Filter and rank options against a user's stated budget.
- **Reviews & Quality:** Summarise authentic, attributable feedback when a permitted source is available; never invent reviews or ratings.
- **Recommendation:** Suggest options based on user needs and transparent ranking criteria.
- **Verification:** Check required product fields, source freshness, destination URLs, and disclosure before publishing.
- **Business-side tools:** Assist with draft buying guides, product catalogue maintenance, broken-link checks, and performance reporting. Human review is required before publication.

Initial implementation should be one reliable assistant backed by modular services. Separate autonomous agents will be introduced only when a clear task, data source, permission boundary, and measurable benefit exist.

## Planned affiliate and business features

- Affiliate programme and retailer integrations, subject to each programme's approval and terms.
- Product cards with source, last-checked date, relevant attributes, and clear affiliate disclosure.
- Click tracking that records only necessary analytics and does not expose personal data.
- Conversion reporting where a programme provides reliable reporting or postbacks.
- Buying guides, category landing pages, search-engine optimisation, and useful editorial content.
- Admin tools for product review, source freshness, link health, content approval, and analytics.
- Email updates only with explicit subscription consent and a working unsubscribe process.

Affiliate commission must not be the sole ranking signal. Do not fabricate discounts, product testing, customer reviews, prices, or availability.

## Current repository structure

```text
.
├── .github/
│   └── workflows/
│       └── quality-checks.yml
├── backend/
│   └── main.py
├── assets/
├── database/
├── models/
├── pages/
├── services/
├── index.html
├── technology.html
├── featured.html
├── guides.html
├── about.html
├── affiliate-disclosure.html
├── privacy.html
├── terms.html
├── 404.html
├── auth.html
├── auth.js
├── auth-nav.js
├── profile.html
├── reset-password.html
├── reset-password.js
├── subscribe.html
├── script.js
├── style.css
├── supabase-config.js
├── vercel.json
├── robots.txt
└── requirements.txt
```

The tree above is an orientation guide; some folders may be empty or still under development. `backend/main.py` is the canonical FastAPI entry point. The previous candidate implementation has been consolidated into it; do not deploy a second backend process.

## Technology currently present

- Frontend: HTML, CSS, and browser JavaScript.
- Authentication/database provider: Supabase (browser client configuration is present).
- Account flow: email/password signup and login, protected profile-page session check, editable display name stored in the signed-in user's Supabase Auth metadata, local logout, account-wide sign-out, and email-based password recovery.
- Backend prototype: Python and FastAPI.
- Newsletter email delivery: Resend integration in the canonical FastAPI backend (`backend/main.py`).
- Newsletter database: SQL migration at `database/migrations/001_newsletter_subscribers.sql`.
- Newsletter frontend: `api-config.js` and `newsletter.js`; the backend URL must be configured after deployment.
- Configuration: environment variables loaded with `python-dotenv`.
- Static hosting: `vercel.json` provides secure response headers and clean URL configuration; the FastAPI API remains a separate deployment.
- Quality checks: GitHub Actions checks local HTML file references, duplicate IDs, Python syntax, and JavaScript syntax.

## Development roadmap

### Phase 1 — Foundation and audit
- Review every existing page, script, backend route, and configuration file.
- Use one maintainable FastAPI entry point (`backend/main.py`).
- Resolve dependency, navigation, accessibility, and responsive-layout issues.
- Keep database migrations and least-privilege access rules in version control.

### Phase 2 — Secure accounts and data
- Verify Supabase Auth settings and Row Level Security (RLS).
- A least-privilege `user_profiles` migration and SQL security test are prepared in `database/migrations/002_user_profiles.sql` and `database/tests/002_user_profiles_security.sql`. Apply and test them in Supabase before connecting the frontend to this table.
- Let signed-in users update their own display name through Supabase Auth user metadata; do not use client-editable metadata for permissions or privileged decisions.
- Provide a user-initiated global sign-out control for lost/shared-device scenarios. Verify session revocation behavior in a real browser before launch.
- Configure the deployed frontend URL in Supabase Auth's allowed redirect URLs, including `profile.html` and `reset-password.html`.
- Test signup email confirmation, login, logout, protected profile access, password reset, and expired recovery links in a real browser.
- Define user profiles, saved preferences, product, retailer, affiliate-click, and content schemas.
- Keep service-role/secret keys only in backend environment variables.
- Add consent and privacy controls.

### Phase 3 — Product catalogue and affiliate foundation
- Start with a small number of categories and approved, reliable data sources.
- Define a normalised product and retailer data model.
- Validate destination URLs and affiliate programme requirements.
- Add transparent disclosures and privacy-conscious click analytics.

### Phase 4 — Shopping assistant
- Build the FastAPI product-search and comparison endpoints.
- Add bilingual intent handling and structured responses.
- Ground product answers in retrieved data; show when information is missing or stale.
- Add budget and country/availability filters.

### Phase 5 — Specialist agents and admin tools
- Add focused research, comparison, budget, review-quality, and verification workflows.
- Add editorial approval and audit logs.
- Introduce automation gradually with rate limits, cost controls, and human review.

### Phase 6 — Growth and launch
- Publish useful category pages and evidence-based buying guides.
- Add SEO metadata, analytics, consent-based email, and conversion reporting.
- Test mobile usability, security, accessibility, performance, and failure cases.
- Deploy the static frontend and Python backend to suitable hosting services; configure secrets in the hosting provider, not in Git.
- Connect a custom domain only after deployment and security checks.

## Preview and deployment

The repository is prepared for a static Vercel preview from the `project-foundation` branch. Use the repository root as the project root, select the `Other` framework preset, leave the build command empty, and use `.` as the output directory if the Vercel import flow requests one. The frontend can be previewed without a live newsletter API, but newsletter signup will remain unavailable until the FastAPI backend is deployed and `api-config.js` is configured. Authentication also requires the matching preview URL to be added to Supabase Auth redirect settings.

The Vercel deployment integration must be connected to the user's Vercel account before an actual hosted preview can be created. Do not make the private repository public just to preview it.

## Local development notes

The backend dependencies are listed in `requirements.txt`. A backend deployment needs environment variables configured in the hosting platform. Never commit a real `.env` file or paste secret keys into issues, chat, screenshots, or frontend JavaScript.

The current backend prototype expects configuration such as:

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY` (server-side only; never expose in the browser)
- `RESEND_API_KEY` (server-side only)
- `RESEND_FROM_EMAIL` (a sender address/domain verified in Resend)
- `PUBLIC_API_URL`
- `FRONTEND_URL` (used by the canonical FastAPI backend for CORS and confirmation links)

Apply `database/migrations/001_newsletter_subscribers.sql` to create the newsletter table with RLS enabled and browser-role access revoked. Then run `database/tests/001_newsletter_security.sql` in the Supabase SQL Editor to verify the expected grants. The separate user-profile migration `database/migrations/002_user_profiles.sql` creates a row per authenticated user with owner-only RLS policies; run `database/tests/002_user_profiles_security.sql` after applying it. Do not connect profile editing to this table until the migration and security test have been completed in the target Supabase project. The backend uses a server-side Supabase secret key. The frontend also needs `window.SMARTPICK_API_BASE_URL` set in `api-config.js` to the deployed HTTPS API origin. Configure `RESEND_FROM_EMAIL` with a sender domain verified in Resend before sending real messages.

## Trust, privacy, and security principles

The current privacy and service terms drafts are published as `privacy.html` and `terms.html`. They describe the features currently present and distinguish them from planned product features. Review them for the final hosting providers, legal jurisdiction, and operational retention practices before public launch.

- Never expose Supabase secret/service-role keys or email-provider keys in frontend files.
- Apply least-privilege database policies and test them with separate user accounts.
- Collect only data required for the feature and explain its use.
- Ask before saving optional preferences or sending marketing email.
- Clearly label affiliate links and sponsored placements.
- Keep product facts attributable to sources and show freshness where possible.
- Do not claim personal product testing unless it actually happened.
- Provide a way to report incorrect information and broken links.

## Contribution and change policy

Work in a feature branch first, review the diff, test the affected feature, and merge only after verification. Avoid replacing working files wholesale when a small, reviewed change is sufficient.
