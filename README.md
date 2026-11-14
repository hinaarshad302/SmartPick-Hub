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
├── backend/
│   ├── main.py
│   └── main_candidate_professional.py
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
├── auth.html
├── auth.js
├── auth-nav.js
├── profile.html
├── subscribe.html
├── script.js
├── style.css
├── supabase-config.js
└── requirements.txt
```

The tree above is an orientation guide; some folders may be empty or still under development. The two backend files are alternatives under review. Confirm the canonical entry point before deploying.

## Technology currently present

- Frontend: HTML, CSS, and browser JavaScript.
- Authentication/database provider: Supabase (browser client configuration is present).
- Backend prototype: Python and FastAPI.
- Newsletter email delivery: Resend integration in the backend prototype.
- Configuration: environment variables loaded with `python-dotenv`.

## Development roadmap

### Phase 1 — Foundation and audit
- Review every existing page, script, backend route, and configuration file.
- Select one maintainable FastAPI entry point.
- Resolve dependency, navigation, accessibility, and responsive-layout issues.
- Document the required database tables and access policies before changing data.

### Phase 2 — Secure accounts and data
- Verify Supabase Auth settings and Row Level Security (RLS).
- Define user profiles, saved preferences, product, retailer, affiliate-click, and content schemas.
- Keep service-role/secret keys only in backend environment variables.
- Add account recovery, session handling, consent, and privacy controls.

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

## Local development notes

The backend dependencies are listed in `requirements.txt`. A backend deployment needs environment variables configured in the hosting platform. Never commit a real `.env` file or paste secret keys into issues, chat, screenshots, or frontend JavaScript.

The current backend prototype expects configuration such as:

- `SUPABASE_URL`
- `SUPABASE_SECRET_KEY` (server-side only; never expose in the browser)
- `RESEND_API_KEY` (server-side only)
- `PUBLIC_API_URL`
- `FRONTEND_URL` (used by the professional candidate backend for CORS and confirmation links)

The newsletter prototype also expects a correctly configured `newsletter_subscribers` database table. Verify the actual schema and access policies before enabling it.

## Trust, privacy, and security principles

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
