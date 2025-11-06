# Agentic AI Lead Qualification Platform

A production-ready **agentic, real‑time B2B lead qualification** platform that continuously discovers company events and intent signals across the open web, first‑party systems, and commercial feeds, then turns them into **actionable sales signals, qualified opportunities, and auto‑generated proposals**.

> Tech stack: **Python backend (FastAPI, Celery, Scrapy/Playwright, LangGraph), JavaScript frontend (Next.js/React), Kafka/Redpanda, PostgreSQL + TimescaleDB, OpenSearch, Neo4j, Redis, MinIO, Dagster**, Docker Compose.

---

## 1) Product Vision & Principles

1. **Agentic loop**: autonomous agents discover, enrich, reason, and act (publish signals, open tickets, draft proposals), supervised by guardrails.
2. **Real‑time by default**: stream ingestion + stateful signal detection; batch only for backfills.
3. **Self‑improving**: continuous feedback from sales outcomes updates scoring, prompts, and rules.
4. **Explainable signals**: every signal includes provenance (URLs, timestamps), features, and rationale.
5. **Privacy‑first & compliant**: GDPR‑aligned data minimization, opt‑out registry, robots.txt honoring, and vendor DPAs.

---

## 2) High‑Level Architecture

```
                ┌──────────── External Web & Feeds ────────────┐
                │  News  | Careers | Tech pages | Docs | Social │
                └──────────────────┬─────────────────────────────┘
                                   │ (scrape/APIs/webhooks)
                         ┌──────────▼──────────┐
                         │ Ingestion Gateways  │  <- Scrapy + Playwright, RSS, APIs
                         └──────────┬──────────┘
                                    │ raw events (JSON)
                          ┌─────────▼─────────┐
                          │  Kafka/Redpanda   │  topics: raw, cleaned, signals, actions
                          └─────────┬─────────┘
                                    │
        ┌───────────────────────────▼───────────────────────────┐
        │          Stream Processing & Agents (Python)         │
        │  - Bytewax/Faust pipelines                           │
        │  - LangGraph agent swarms (Discover→Enrich→Score)    │
        │  - NER, classifiers, embeddings, LLM tools           │
        └───────────────┬───────────────┬──────────────────────┘
                        │               │
                ┌───────▼──────┐  ┌─────▼────────┐
                │ Feature Store │  │  Signal Svc  │ -> webhooks/CRM
                │ (Postgres/TS) │  │ (FastAPI)    │ -> notifications
                └───────┬──────┘  └─────┬────────┘
                        │               │
                ┌───────▼────────┐  ┌───▼──────────┐
                │  OpenSearch     │  │  Neo4j KG    │ (companies, people,
                │  (search)       │  │ (relations)  │  products, events)
                └───────┬─────────┘  └────┬─────────┘
                        │                 │
                    ┌───▼────┐       ┌───▼────┐
                    │  Redis │       │ MinIO  │ (docs, snapshots)
                    └───┬────┘       └───┬────┘
                        │                │
                 ┌───────▼───────────────▼───────┐
                 │ Frontend (Next.js/React)      │
                 │ Dashboards • Signals • Agents │
                 │ Playbooks • Proposals • APIs  │
                 └───────────────────────────────┘
```

---

## 3) Core Components

### 3.1 Ingestion Layer
- **Web crawler**: Scrapy + Playwright (headful for JS). Polite crawling, exponential backoff, robots.txt, domain allow‑lists.
- **Connectors**: RSS/Atom, sitemap, REST/GraphQL, LinkedIn Jobs (via compliance‑friendly partners), Crunchbase/Companies House/API feeds, G2/Capterra reviews (where permitted), GitHub repos, package registries, cloud status pages.
- **First‑party**: CRM/web forms/webhooks (HubSpot/Salesforce), product telemetry, email parsers.
- **Normalizer**: HTML→Markdown→clean text; language detection; boilerplate removal; PII redaction.

### 3.2 Streaming & Processing
- **Transport**: Kafka/Redpanda with topics: `raw.events`, `clean.events`, `companies.updates`, `signals.detected`, `actions.triggered`.
- **Pipelines** (Bytewax/Faust): dedupe, entity resolution, feature extraction, template matchers (regex/dicts), model inference.
- **Embeddings**: local/SaaS models; vector write‑through to OpenSearch.
- **State**: feature store in PostgreSQL + TimescaleDB hypertables for time‑series features.

### 3.3 Agentic Intelligence
- **Graph of Agents** (LangGraph):
  1) **Discoverer**: finds net‑new companies & new URLs.
  2) **Resolver**: entity resolution (company canonicalization, domain↔legal entity via KG).
  3) **Enricher**: fills firmographics, technographics, intent features.
  4) **Classifier**: BANT/CHAMP/MEDDICC labelers; topic categorization; geo/sector tags.
  5) **Scorer**: real‑time lead score per product, with reasoned explanation.
  6) **Proposer**: drafts tailored proposals & outreach sequences per signal.
  7) **Supervisor**: guardrails, PII policy, rate limits, ethical filters.

- **Models**: small local LLM for extraction; larger hosted LLM for reasoning (toggleable). Add domain‑specific classifiers (sklearn/XGBoost/LightGBM). Few‑shot plus retrieval‑augmented prompts against OpenSearch.

### 3.4 Signal Engine
- **Signal lexicon**: structured definitions like `Hiring spike in {Role}`; `Tech stack change: adopted Snowflake`; `Compliance event: ISO 27001 achieved`; `Budget event: funding round`.
- **Detectors**: pattern/rule‑based + ML (sequence change‑point, anomaly, trend accelerations). Windowed aggregations per company.
- **Scoring**: product matching via rules + learned model. Multi‑armed bandit adjusts thresholds by conversion feedback.
- **Actions**: webhooks, Slack/Teams, CRM task, email draft, proposal draft, calendar booking, or hold for review.

### 3.5 Knowledge Graph (Neo4j)
- Nodes: `Company`, `Person`, `Product`, `Event`, `Tech`, `Region`, `Source`.
- Rels: `USES`, `PART_OF`, `RAISED`, `HIRES_FOR`, `COMPLIES_WITH`, `PARTNERS_WITH`, `MENTIONED_IN`.
- Enables **reasoning over relationships** (e.g., vendor changes, partners, subsidiaries) and **multi‑hop signal rules**.

### 3.6 Storage & Indexing
- **PostgreSQL + TimescaleDB**: features, lead scores, signal history, feedback.
- **OpenSearch**: full‑text + vector search of pages, job posts, PRs, docs.
- **Redis**: rate limits, task queues, short‑lived agent memory.
- **MinIO**: raw HTML, screenshots, PDFs, proposal artifacts.

### 3.7 APIs (FastAPI)
- `/ingest/webhook` (POST) — drop events.
- `/signals/search` (GET) — filter by product, geo, freshness, score.
- `/leads/:company_id` (GET) — profile, features, current signals.
- `/proposals/draft` (POST) — JSON brief → proposal PDF/Markdown.
- `/agents/run` (POST) — run an agent playbook on demand.
- `/feedback` (POST) — close/won/lost + rationale; retrains scorers.
- `/integrations/{crm}` — OAuth + push tasks/contacts/opportunities.

### 3.8 Frontend (Next.js/React)
- **Signals Wall** (real‑time): filters, saved views, pinboards.
- **Company 360**: timeline of events, tech stack, hiring, signals, suggested next best action.
- **Agent Playbooks**: templatized strategies per product/segment.
- **Proposal Studio**: data‑driven outlines; 1‑click PDF/email; AB‑test variants.
- **Team View**: assignment, SLA timers, outcomes, learning loops.
- **Admin**: source rules, crawl scopes, compliance, secrets vault UI.

---

## 4) Data Model (abridged)

**Company**: `id, name, domain, country, industry, size, revenue, tech[], employees[], sources[]`

**Event**: `id, company_id, type, url, ts, text, features{...}, lang`

**Signal**: `id, company_id, product_id, kind, score, ts_start, ts_end, evidence[], explanation`

**LeadScore**: `company_id, product_id, score, components{fit:intent:timing}, updated_at`

**Proposal**: `id, company_id, product_id, outline_md, pdf_uri, status`

**Feedback**: `signal_id, outcome{won,lost,ignore}, reason, value, ts`

---

## 5) Lead Scoring Method

- **FIT**: firmographics + technographics vs ICP (rule + classifier).
- **INTENT**: onsite events, hiring, PRs, budget/funding, tech changes.
- **TIMING**: velocity of events, recency decay, seasonality.
- **Score** = w1*FIT + w2*INTENT + w3*TIMING; calibrated by isotonic regression; monotonic constraints for auditability.
- **Framework tags**: BANT/CHAMP/MEDDICC fields populated for CRM.

---

## 6) Proposal Generation

1) Retrieve **company context** (KG + OpenSearch).
2) Map **needs→product features** (product KB collection).
3) Generate **outline** (LLM) with slots filled from evidence table.
4) Produce **Markdown + PDF** with citations to evidence URLs and a costed package.
5) **Versioning & AB‑tests** stored in MinIO with outcomes tracked.

---

## 7) Observability & Operations

- **Logging**: JSON logs via structlog; request IDs; source URL trace.
- **Metrics**: Prometheus + Grafana dashboards (ingest lag, signals/min, precision@k, time‑to‑signal, win‑rate uplift).
- **Data Quality**: great_expectations checks; dead‑link monitor.
- **Canaries**: shadow pipelines for new detectors before promotion.
- **Security**: SSO/SAML, OIDC, secrets via Doppler/Vault, audit log.

---

## 8) Compliance & Safety

- Robots.txt, rate limits, and polite fetching with cache.
- Opt‑out do‑not‑crawl/erase for companies/domains.
- PII minimization; legal basis registry; data retention policies.
- Vendor risk review; DPA templates; region‑aware storage.

---

## 9) Docker Compose (services sketch)

```yaml
version: "3.9"
services:
  api:
    image: ghcr.io/yourorg/leadq-api:latest
    build: ./services/api
    environment:
      - DATABASE_URL=postgresql://app:pass@db/app
      - OPENSEARCH_URL=http://opensearch:9200
      - KAFKA_BROKERS=redpanda:9092
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=http://minio:9000
    depends_on: [db, opensearch, redpanda, redis, minio]
    ports: ["8080:8080"]

  workers:
    build: ./services/workers
    environment:
      - KAFKA_BROKERS=redpanda:9092
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://app:pass@db/app
    depends_on: [redpanda, db, redis]
    deploy:
      replicas: 2

  crawler:
    build: ./services/crawler
    environment:
      - QUEUE=kafka://redpanda:9092/raw.events
    depends_on: [redpanda]

  redpanda:
    image: redpandadata/redpanda:latest
    command: ["start","--overprovisioned","--smp","1","--memory","1G","--reserve-memory","0M"]
    ports: ["9092:9092"]

  db:
    image: timescale/timescaledb-ha:pg16
    environment:
      - POSTGRES_USER=app
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=app
    ports: ["5432:5432"]

  opensearch:
    image: opensearchproject/opensearch:2
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=true
    ports: ["9200:9200","9600:9600"]

  redis:
    image: redis:7

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      - MINIO_ROOT_USER=admin
      - MINIO_ROOT_PASSWORD=admin123
    ports: ["9000:9000","9001:9001"]

  web:
    build: ./web
    environment:
      - NEXT_PUBLIC_API_BASE=http://localhost:8080
    depends_on: [api]
    ports: ["3000:3000"]
```

---

## 10) Implementation Outline (by repo directory)

```
.
├── services
│   ├── api (FastAPI: REST, auth, integrations, proposals)
│   ├── workers (Celery/Bytewax: pipelines, agents, scoring)
│   ├── crawler (Scrapy+Playwright: sources, robots, sitemaps)
│   └── scheduler (Dagster: backfills, maintenance, retrains)
├── libs
│   ├── nlp (NER, classifiers, embeddings, language id)
│   ├── agents (LangGraph graphs, tools, guardrails)
│   ├── signals (lexicon, detectors, scoring models)
│   └── kg (Neo4j adapters, Cypher queries)
├── infra
│   ├── compose.yml (above)
│   ├── opensearch-templates.json
│   ├── grafana-dashboards/
│   └── great_expectations/
├── web (Next.js app: dashboards, components, auth)
└── docs (runbooks, DPA, architecture)
```

---

## 11) Key Data Flows (E2E)

1) **Discover**: Crawler finds `/careers` updates at `acme.com` ⇒ pushes `raw.events`.
2) **Clean**: pipeline extracts text, timestamps, jobs, locations ⇒ `clean.events`.
3) **Resolve**: entity resolution links `acme.com` to `Acme AB` in KG.
4) **Detect**: hiring spike for “Data Platform” roles in EU within 14 days.
5) **Score**: fit (industry=Fintech, size=2000), intent (hiring spike), timing (fresh) ⇒ 86/100 for “Data Lake Product”.
6) **Signal**: `signals.detected` with evidence URLs.
7) **Act**: webhook → Salesforce opportunity + proposal draft.
8) **Learn**: Sales marks **Won**; score calibrator updates weights.

---

## 12) Example Signal Definitions

- **Hiring Spike**: job postings for `{roles}` increase ≥ 2.5× rolling 30‑day baseline; min 4 openings; countries in `{region}`.
- **Tech Adoption**: detection of vendor script/DNS/TXT/headers indicates new tool; corroborated by blog/release notes within 14 days.
- **Compliance Win**: press/news mentions `ISO 27001` OR `SOC 2` + audit certificate link.
- **Budget Event**: funding ≥ Series A OR public tender above threshold in region.

Each signal emits: `company_id, kind, score, evidence[ {url, snippet, ts} ], explanation`.

---

## 13) Models & MLOps

- **Feature extraction**: keyword spans, transformers for intent, multilingual support.
- **Supervised scorers**: XGBoost/LightGBM with SHAP explainability.
- **LLM**: RAG over company corpus for classification rationales & proposal drafting.
- **Retraining**: nightly if drift detected (PSI, KS tests); champion/challenger.
- **Evaluation**: precision/recall on labeled signal dataset; lead conversion uplift.

---

## 14) Integrations

- **CRMs**: Salesforce, HubSpot (OAuth, webhooks, field mapping for BANT/MEDDICC).
- **Comms**: Slack/Teams notifications with deep links.
- **Calendars**: Google/Microsoft for instant meeting links.
- **Email**: provider‑agnostic (SendGrid/Postmark) for proposal delivery.

---

## 15) Security Hardening

- Private network for stateful stores; TLS in‑cluster via Traefik/Caddy.
- JWT with short TTL + refresh; role‑based access; audit tables; signed URLs for MinIO.
- Content sanitization; sandboxed rendering of third‑party HTML/PDF.

---

## 16) Frontend UX Highlights

- **Signals Stream**: live tiles with score, confidence, evidence chips, one‑click “Create opp”.
- **Company 360**: river of events + callouts; graph mini‑map (KG) of related vendors.
- **Proposal Studio**: side‑by‑side: evidence, outline, editable copy, export to PDF.
- **Agent Console**: runbooks, test‑run agents, cost/latency stats.

---

## 17) Rollout Plan

- **Phase 1 (4–6 weeks)**: Core ingestion, 6 signal types, scoring v1, basic dashboards.
- **Phase 2**: Proposal Studio, CRM bi‑directional sync, agent supervisor.
- **Phase 3**: Multi‑region sources, advanced KG rules, A/B proposals, attribution.

---

## 18) Acceptance Criteria (MVP)

- Ingest ≥ 50k pages/day politely; median page→signal latency < 5 min.
- ≥ 70% precision on top‑3 signal types (hiring, tech adoption, funding).
- Proposal draft in < 60s with ≥ 3 evidence links.
- End‑to‑end traceability from signal → closed‑won in CRM.

---

## 19) Example FastAPI Snippets (illustrative)

```python
# POST /signals/search
@router.get("/signals/search")
async def search_signals(q: str | None = None, product: str | None = None, min_score: int = 70):
    must = [{"range": {"score": {"gte": min_score}}}]
    if product:
        must.append({"term": {"product": product}})
    if q:
        must.append({"multi_match": {"query": q, "fields": ["company^3","evidence.text"]}})
    res = opensearch.search(index="signals", query={"bool": {"must": must}})
    return [hit["_source"] for hit in res["hits"]["hits"]]
```

```python
# Proposal Draft Worker (simplified)
context = retrieve_company_context(company_id)
outline = llm.generate_outline(context, product)
proposal_md = fill_outline(outline, context)
uri = save_pdf_and_markdown(proposal_md)
notify_crm(company_id, uri)
```

---

## 20) Future Enhancements

- Voice & chat agents to qualify inbound in real‑time.
- Tender scanners per region; citation extraction from PDFs.
- Privacy‑preserving learning (federated signals per client).
- Cost‑aware agent planning (latency/cost SLOs per action).

---

**Outcome**: A robust, explainable, and compliant agentic platform that turns noisy, multilingual web activity into **timely, high‑precision sales signals** and **ready‑to‑send proposals**, deployable via a single Docker Compose stack.

