"""
Web crawler service for polite, compliant data collection
"""
import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
from kafka import KafkaProducer
import structlog
from urllib.robotparser import RobotFileParser
import time

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()


class PoliteCrawler:
    """Polite web crawler that respects robots.txt and rate limits"""

    def __init__(self):
        self.kafka_brokers = os.getenv("KAFKA_BROKERS", "redpanda:9092").split(',')
        self.redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

        # Initialize Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=self.kafka_brokers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )

        # Crawler settings
        self.user_agent = "LeadQualificationBot/1.0 (polite crawler; +https://example.com/bot)"
        self.delay_seconds = float(os.getenv("CRAWLER_DELAY_SECONDS", "1.0"))
        self.timeout = 30
        self.respect_robots_txt = True

        # Rate limiting: domain -> last crawl time
        self.last_crawl_times = {}

        # Robots.txt cache: domain -> RobotFileParser
        self.robots_cache = {}

        logger.info("Crawler initialized", delay=self.delay_seconds)

    async def can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        if not self.respect_robots_txt:
            return True

        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        # Check cache
        if domain not in self.robots_cache:
            robots_url = urljoin(domain, "/robots.txt")
            parser = RobotFileParser()
            parser.set_url(robots_url)

            try:
                async with httpx.AsyncClient(timeout=10) as client:
                    response = await client.get(robots_url)
                    if response.status_code == 200:
                        parser.parse(response.text.splitlines())
                    else:
                        # No robots.txt or error, allow crawling
                        pass
            except Exception as e:
                logger.debug(f"Could not fetch robots.txt: {e}", url=robots_url)

            self.robots_cache[domain] = parser

        parser = self.robots_cache[domain]
        can_fetch = parser.can_fetch(self.user_agent, url)

        if not can_fetch:
            logger.info("URL blocked by robots.txt", url=url)

        return can_fetch

    async def rate_limit(self, domain: str):
        """Apply rate limiting per domain"""
        if domain in self.last_crawl_times:
            elapsed = time.time() - self.last_crawl_times[domain]
            if elapsed < self.delay_seconds:
                wait_time = self.delay_seconds - elapsed
                logger.debug(f"Rate limiting, waiting {wait_time:.2f}s", domain=domain)
                await asyncio.sleep(wait_time)

        self.last_crawl_times[domain] = time.time()

    async def fetch_url(self, url: str) -> Dict[str, Any]:
        """Fetch a single URL with politeness and error handling"""
        parsed = urlparse(url)
        domain = parsed.netloc

        # Check robots.txt
        if not await self.can_fetch(url):
            return {"error": "blocked_by_robots_txt", "url": url}

        # Rate limit
        await self.rate_limit(domain)

        # Fetch
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": self.user_agent}
                )
                response.raise_for_status()

                # Parse content
                soup = BeautifulSoup(response.text, 'html.parser')

                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()

                # Extract text
                text = soup.get_text(separator='\n', strip=True)

                # Extract title
                title = soup.title.string if soup.title else ""

                # Extract meta description
                meta_desc = soup.find("meta", attrs={"name": "description"})
                description = meta_desc.get("content", "") if meta_desc else ""

                # Extract links
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    full_url = urljoin(url, href)
                    if urlparse(full_url).netloc == domain:  # Same domain only
                        links.append(full_url)

                result = {
                    "url": url,
                    "status_code": response.status_code,
                    "title": title,
                    "description": description,
                    "text": text[:10000],  # Limit text length
                    "links": list(set(links))[:50],  # Unique links, max 50
                    "crawled_at": datetime.utcnow().isoformat(),
                    "content_length": len(response.text)
                }

                logger.info("URL fetched successfully", url=url, status=response.status_code)
                return result

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error: {e}", url=url, status=e.response.status_code)
            return {"error": "http_error", "status_code": e.response.status_code, "url": url}
        except httpx.TimeoutException:
            logger.error("Request timeout", url=url)
            return {"error": "timeout", "url": url}
        except Exception as e:
            logger.error(f"Fetch error: {e}", url=url)
            return {"error": str(e), "url": url}

    async def crawl_company(self, company_id: int, domain: str, urls: List[str]):
        """Crawl all URLs for a company"""
        logger.info("Starting company crawl", company_id=company_id, domain=domain, url_count=len(urls))

        for url in urls:
            result = await self.fetch_url(url)

            if "error" not in result:
                # Publish to Kafka
                event = {
                    "event_type": "web_crawl",
                    "company_id": company_id,
                    "data": result,
                    "timestamp": datetime.utcnow().isoformat()
                }

                self.producer.send("raw.events", value=event)
                logger.debug("Event published", url=url)

        logger.info("Company crawl completed", company_id=company_id)

    async def crawl_careers_page(self, company_id: int, careers_url: str):
        """Specifically crawl careers/jobs pages for hiring signals"""
        logger.info("Crawling careers page", company_id=company_id, url=careers_url)

        result = await self.fetch_url(careers_url)

        if "error" not in result:
            # Parse job postings
            jobs = self.extract_job_postings(result)

            event = {
                "event_type": "job_postings",
                "company_id": company_id,
                "data": {
                    "url": careers_url,
                    "jobs": jobs,
                    "job_count": len(jobs)
                },
                "timestamp": datetime.utcnow().isoformat()
            }

            self.producer.send("raw.events", value=event)
            logger.info("Job postings extracted", company_id=company_id, count=len(jobs))

    def extract_job_postings(self, crawl_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract structured job postings from careers page"""
        # Simplified job extraction
        # In production, would use more sophisticated parsing

        jobs = []
        text = crawl_result.get("text", "")

        # Simple heuristic: look for common job title keywords
        job_keywords = [
            "engineer", "developer", "manager", "director",
            "analyst", "designer", "architect", "lead",
            "data scientist", "product manager", "sales"
        ]

        lines = text.split('\n')
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in job_keywords):
                if len(line) < 100:  # Likely a job title, not description
                    jobs.append({
                        "title": line.strip(),
                        "detected_at": datetime.utcnow().isoformat()
                    })

        return jobs[:50]  # Limit to 50 jobs

    def run_scheduler(self):
        """Run scheduled crawls"""
        logger.info("Starting crawler scheduler")

        # In production, this would:
        # 1. Poll database for companies to crawl
        # 2. Check crawl schedules
        # 3. Prioritize based on lead scores
        # 4. Queue crawl jobs

        # Simplified: continuous loop
        while True:
            try:
                # Would get companies from database
                # For now, just sleep
                logger.info("Crawler scheduler running...")
                time.sleep(60)

            except KeyboardInterrupt:
                logger.info("Scheduler interrupted")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}", exc_info=True)
                time.sleep(10)


if __name__ == "__main__":
    crawler = PoliteCrawler()
    crawler.run_scheduler()
