# Agentic AI Lead Qualification Platform

A production-ready **agentic, real-time B2B lead qualification platform** that continuously discovers company events and intent signals across the web, turning them into **actionable sales signals, qualified opportunities, and auto-generated proposals**.

![Platform Architecture](docs/architecture.png)

## 🌟 Features

### Core Capabilities

- **🤖 Autonomous AI Agents**: Multi-agent system using LangGraph
  - **Discoverer**: Finds new companies and data sources
  - **Enricher**: Fills in company data and technographics
  - **Scorer**: Calculates lead scores (FIT + INTENT + TIMING)
  - **Proposer**: Generates tailored proposals using LLMs

- **📊 Real-Time Signal Detection**
  - Hiring spike detection
  - Technology adoption signals
  - Funding events
  - Expansion signals
  - Pain point identification
  - Compliance achievements

- **🕷️ Polite Web Crawler**
  - Respects robots.txt
  - Rate-limited per domain
  - Extracts structured data from careers pages, blogs, news

- **📈 Lead Scoring Engine**
  - FIT: Firmographic + technographic matching
  - INTENT: Buying signals from events
  - TIMING: Recency and velocity of activity
  - BANT/CHAMP/MEDDICC qualification

- **📝 AI-Powered Proposal Generation**
  - Context-aware proposals using GPT-4 or Claude
  - Evidence-based with citations
  - PDF export ready

- **🔍 Knowledge Graph (Neo4j)**
  - Company relationships
  - Technology usage patterns
  - Event connections
  - Similar company discovery

- **⚡ Real-Time Processing**
  - Kafka/Redpanda streaming
  - OpenSearch full-text and vector search
  - TimescaleDB for time-series data

## 🏗️ Architecture

### Tech Stack

**Backend:**
- Python 3.11 with FastAPI
- LangChain + LangGraph for AI agents
- Celery for background tasks
- Scrapy + Playwright for crawling

**Frontend:**
- Next.js 14 with React
- TypeScript
- Tailwind CSS
- Real-time dashboard

**Data Stores:**
- PostgreSQL + TimescaleDB (structured data, time-series)
- OpenSearch (full-text + vector search)
- Neo4j (knowledge graph)
- Redis (cache, rate limiting)
- MinIO (object storage)
- Kafka/Redpanda (event streaming)

**AI/ML:**
- OpenAI GPT-4 or Anthropic Claude
- LangChain for LLM orchestration
- LangGraph for agent workflows
- Scikit-learn, XGBoost for ML models

**Observability:**
- Prometheus metrics
- Grafana dashboards
- Structured JSON logging

### Services

```
├── api          - FastAPI REST API
├── workers      - Celery workers running AI agents
├── crawler      - Web crawler service
├── scheduler    - Background job scheduler
└── web          - Next.js dashboard
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose
- At least 8GB RAM
- API keys for OpenAI or Anthropic (for AI agents)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd autonomous-lead-qualification
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env and add your API keys:
# - OPENAI_API_KEY (for GPT-4)
# - ANTHROPIC_API_KEY (for Claude)
```

3. **Start the platform:**
```bash
./start.sh
```

Or manually:
```bash
docker-compose up -d
```

4. **Access the dashboard:**
Open http://localhost:3000 in your browser

### Default Credentials

- **Dashboard**: No auth required (add authentication in production)
- **Grafana**: admin / admin
- **Neo4j**: neo4j / password123
- **MinIO**: admin / admin_password_123

## 📖 Usage Guide

### 1. Adding Companies

**Via API:**
```bash
curl -X POST http://localhost:8080/api/v1/companies/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "domain": "acme.com",
    "industry": "Technology",
    "country": "United States",
    "employee_count": 500
  }'
```

**Via Dashboard:**
Navigate to Companies → Add New Company

### 2. Running Agents

**Discover URLs for a company:**
```bash
curl -X POST http://localhost:8080/api/v1/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "company_discovery",
    "agent_type": "discoverer",
    "company_id": 1
  }'
```

**Generate a proposal:**
```bash
curl -X POST http://localhost:8080/api/v1/proposals/draft?company_id=1&product_id=data_platform
```

### 3. Viewing Signals

**Dashboard:** Real-time signals appear on the main dashboard

**API:**
```bash
# Search signals
curl "http://localhost:8080/api/v1/signals/search?min_score=70&limit=20"

# Get signal by ID
curl "http://localhost:8080/api/v1/signals/1"
```

### 4. Company 360 View

Get comprehensive company view with all signals, events, and scores:

```bash
curl "http://localhost:8080/api/v1/companies/1"
```

### 5. Providing Feedback

Help the system learn from outcomes:

```bash
curl -X POST http://localhost:8080/api/v1/feedback/ \
  -H "Content-Type: application/json" \
  -d '{
    "signal_id": 1,
    "outcome": "won",
    "deal_value": 150000,
    "time_to_close": 45,
    "reason": "Perfect timing, strong intent signals"
  }'
```

## 🎯 Key Workflows

### Signal Generation Flow

```
1. Crawler discovers company URLs
   ↓
2. Raw events published to Kafka
   ↓
3. Workers process events
   - Clean and normalize
   - Extract entities
   - Generate embeddings
   ↓
4. Enricher agent adds context
   ↓
5. Scorer agent calculates scores
   ↓
6. Signals published and indexed
   ↓
7. Dashboard shows real-time signals
```

### Proposal Generation Flow

```
1. High-score signal detected
   ↓
2. Trigger proposal generation
   ↓
3. Proposer agent:
   - Retrieves company context from KG
   - Fetches recent signals and events
   - Maps needs to product features
   - Generates proposal using LLM
   ↓
4. Store proposal in database
   ↓
5. Generate PDF and store in MinIO
   ↓
6. Send notification
```

## 📊 Monitoring & Operations

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f workers
docker-compose logs -f crawler
```

### Metrics & Dashboards

- **Grafana**: http://localhost:3001
- **Prometheus**: http://localhost:9090
- **API Metrics**: http://localhost:8080/metrics

### Health Checks

```bash
# API health
curl http://localhost:8080/health

# Check all services
docker-compose ps
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# AI Provider (choose one)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Crawler behavior
CRAWLER_DELAY_SECONDS=1.0
CRAWLER_RESPECT_ROBOTS_TXT=true

# Signal scoring weights
SIGNAL_FIT_WEIGHT=0.4
SIGNAL_INTENT_WEIGHT=0.4
SIGNAL_TIMING_WEIGHT=0.2

# Signal threshold
SIGNAL_SCORE_THRESHOLD=70
```

### Scaling Workers

Adjust worker replicas in `docker-compose.yml`:

```yaml
workers:
  deploy:
    replicas: 4  # Increase for more throughput
```

## 📚 API Documentation

Full API documentation available at:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

### Key Endpoints

**Companies:**
- `POST /api/v1/companies/` - Create company
- `GET /api/v1/companies/` - List companies
- `GET /api/v1/companies/{id}` - Company 360 view

**Signals:**
- `GET /api/v1/signals/search` - Search signals
- `GET /api/v1/signals/{id}` - Get signal
- `POST /api/v1/signals/{id}/action` - Trigger action

**Agents:**
- `POST /api/v1/agents/run` - Run agent playbook
- `GET /api/v1/agents/{run_id}` - Get agent results

**Proposals:**
- `POST /api/v1/proposals/draft` - Generate proposal
- `GET /api/v1/proposals/{id}` - Get proposal

## 🧪 Development

### Running Tests

```bash
# Backend tests
docker-compose exec api pytest

# Frontend tests
docker-compose exec web npm test
```

### Adding New Agents

1. Create agent in `libs/agents/`:
```python
from .base_agent import BaseAgent, AgentState

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MyAgent", agent_type="my_type")

    async def execute(self, state: AgentState) -> AgentState:
        # Your logic here
        return state
```

2. Register in `libs/agents/__init__.py`

3. Use in workers or API

### Adding New Signal Types

1. Add to `SignalKind` enum in `models.py`
2. Implement detection logic in workers
3. Update scoring logic in `scorer.py`

## 🔒 Security & Compliance

- **robots.txt**: Crawler respects robots.txt
- **Rate Limiting**: Per-domain rate limits
- **PII Minimization**: Configurable data retention
- **Auth**: JWT-based authentication (configure in production)
- **HTTPS**: Enable in production with reverse proxy

## 📈 Performance

**Throughput:**
- 50,000+ pages/day crawling capacity
- <5 min signal detection latency
- Sub-second API response times

**Scalability:**
- Horizontal scaling via worker replicas
- Distributed data stores
- Kafka for event streaming

## 🛠️ Troubleshooting

### Services won't start

```bash
# Check Docker resources
docker system df

# Remove old volumes
docker-compose down -v
docker-compose up -d
```

### OpenSearch won't start

Increase vm.max_map_count:
```bash
# Linux
sudo sysctl -w vm.max_map_count=262144

# Docker Desktop: Settings → Resources → Advanced
```

### Agents not working

Check API keys are set:
```bash
docker-compose exec api env | grep API_KEY
```

## 🗺️ Roadmap

- [ ] Voice & chat agents for inbound qualification
- [ ] Multi-language support
- [ ] Advanced ML models for scoring
- [ ] CRM integrations (Salesforce, HubSpot)
- [ ] Email sequences
- [ ] A/B testing for proposals
- [ ] Multi-tenant support

## 📄 License

[Your License Here]

## 🤝 Contributing

Contributions welcome! Please read CONTRIBUTING.md first.

## 📞 Support

For issues and questions:
- GitHub Issues: [link]
- Documentation: [link]
- Email: support@example.com

---

Built with ❤️ using FastAPI, LangChain, Next.js, and modern data stack.
