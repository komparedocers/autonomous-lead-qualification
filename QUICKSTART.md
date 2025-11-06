# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Prerequisites
Ensure you have:
- Docker & Docker Compose installed
- At least 8GB RAM available
- OpenAI API key OR Anthropic API key

### Step 2: Setup

```bash
# 1. Clone and enter directory
cd autonomous-lead-qualification

# 2. Copy environment file
cp .env.example .env

# 3. Edit .env and add your API key
# Required: Set ONE of these
nano .env  # or use your preferred editor
# Add: OPENAI_API_KEY=sk-...
# OR:  ANTHROPIC_API_KEY=sk-ant-...
```

### Step 3: Launch

```bash
# Start everything with one command
./start.sh

# OR manually:
docker-compose up -d
```

### Step 4: Access

Open in your browser:
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8080/docs

## 🎯 First Use

### Add Your First Company

**Via API:**
```bash
curl -X POST http://localhost:8080/api/v1/companies/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example Corp",
    "domain": "example.com",
    "industry": "Technology",
    "country": "United States",
    "employee_count": 500,
    "tech_stack": ["Python", "AWS", "React"]
  }'
```

### Run Discovery Agent

```bash
curl -X POST http://localhost:8080/api/v1/agents/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "discover_company",
    "agent_type": "discoverer",
    "company_id": 1
  }'
```

### View Real-Time Signals

Go to http://localhost:3000 to see signals as they're detected!

## 📊 What You Get

### Services Running:
- ✅ FastAPI Backend (Python)
- ✅ Next.js Frontend (React/TypeScript)
- ✅ AI Agents (LangChain + LangGraph)
- ✅ Web Crawler (Scrapy + Playwright)
- ✅ PostgreSQL + TimescaleDB
- ✅ OpenSearch
- ✅ Neo4j Knowledge Graph
- ✅ Kafka/Redpanda Streaming
- ✅ Redis Cache
- ✅ MinIO Storage
- ✅ Prometheus + Grafana

### Features Available:
- 🤖 Autonomous AI agents
- 📊 Real-time signal detection
- 🎯 Lead scoring (FIT + INTENT + TIMING)
- 📝 AI-powered proposal generation
- 🕸️ Knowledge graph of companies
- 🕷️ Polite web crawling
- 📈 Analytics dashboard

## 🔍 Monitor Your System

```bash
# View logs
docker-compose logs -f

# View specific service
docker-compose logs -f api
docker-compose logs -f workers

# Check status
docker-compose ps

# Check API health
curl http://localhost:8080/health
```

## 🛑 Stop Everything

```bash
docker-compose down

# To remove all data (fresh start)
docker-compose down -v
```

## 🆘 Troubleshooting

**OpenSearch won't start?**
```bash
# Increase vm.max_map_count
sudo sysctl -w vm.max_map_count=262144
```

**Out of memory?**
```bash
# Check Docker resources
docker system df

# Adjust in Docker Desktop: Settings → Resources
# Increase RAM to at least 8GB
```

**API keys not working?**
```bash
# Verify environment variables
docker-compose exec api env | grep API_KEY

# Restart services
docker-compose restart api workers
```

## 📚 Next Steps

1. Read the full [README.md](README.md)
2. Explore the [API Documentation](http://localhost:8080/docs)
3. Check the [Architecture Documentation](agentic_ai_lead_qualification_platform_architecture_implementation.md)
4. Add more companies
5. Configure integrations
6. Customize agents

## 🎓 Learn More

- **API Endpoints**: http://localhost:8080/docs
- **Metrics**: http://localhost:9090
- **Dashboards**: http://localhost:3001
- **Neo4j Browser**: http://localhost:7474

---

Need help? Check the main README.md or open an issue!
