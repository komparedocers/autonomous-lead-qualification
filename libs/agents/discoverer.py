"""
Discoverer Agent - finds new companies and URLs to crawl
"""
from typing import Dict, Any, List
import httpx
from bs4 import BeautifulSoup
import re
from .base_agent import BaseAgent, AgentState


class DiscovererAgent(BaseAgent):
    """
    Discovers new companies and potential data sources
    - Searches for companies matching ICP
    - Finds relevant URLs to crawl (careers, blog, news)
    - Identifies company domains and metadata
    """

    def __init__(self):
        super().__init__(name="Discoverer", agent_type="discoverer")
        self.timeout = 10

    async def execute(self, state: AgentState) -> AgentState:
        """Execute discovery logic"""
        if state.company_data and state.company_data.get("domain"):
            # Discover URLs for existing company
            domain = state.company_data["domain"]
            urls = await self.discover_company_urls(domain)
            state.metadata["discovered_urls"] = urls
            self.log_action("discovered_urls", {"count": len(urls), "domain": domain})
        else:
            # Discover new companies (placeholder - would integrate with data providers)
            companies = await self.discover_new_companies()
            state.metadata["discovered_companies"] = companies
            self.log_action("discovered_companies", {"count": len(companies)})

        return state

    async def discover_company_urls(self, domain: str) -> List[str]:
        """Discover important URLs for a company domain"""
        urls = []

        # Standard URL patterns to check
        patterns = [
            f"https://{domain}/careers",
            f"https://{domain}/jobs",
            f"https://{domain}/about",
            f"https://{domain}/blog",
            f"https://{domain}/news",
            f"https://{domain}/press",
            f"https://{domain}/team",
            f"https://{domain}/company",
            f"https://{domain}/about-us",
        ]

        async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
            for url in patterns:
                try:
                    response = await client.head(url, timeout=5)
                    if response.status_code == 200:
                        urls.append(url)
                        self.logger.debug(f"Found valid URL: {url}")
                except Exception as e:
                    self.logger.debug(f"URL not found: {url}")
                    continue

        # Try to discover sitemap
        sitemap_url = f"https://{domain}/sitemap.xml"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(sitemap_url)
                if response.status_code == 200:
                    urls.append(sitemap_url)
                    self.logger.info(f"Found sitemap: {sitemap_url}")
        except Exception:
            pass

        return urls

    async def discover_new_companies(self) -> List[Dict[str, Any]]:
        """
        Discover new companies to track
        In production, this would integrate with:
        - Crunchbase API
        - LinkedIn Sales Navigator
        - Industry directories
        - News feeds
        - Public company registries
        """
        # Placeholder implementation
        # Would integrate with actual data sources
        companies = []

        self.logger.info("Company discovery would integrate with external APIs")

        return companies

    async def extract_company_info(self, url: str) -> Dict[str, Any]:
        """Extract company information from their website"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, 'html.parser')

                # Extract basic info
                info = {
                    "url": url,
                    "title": soup.title.string if soup.title else "",
                    "description": "",
                    "emails": [],
                    "social_links": {}
                }

                # Extract meta description
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    info["description"] = meta_desc.get("content", "")

                # Extract emails
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, response.text)
                info["emails"] = list(set(emails))[:5]  # Limit to 5 unique emails

                # Extract social links
                social_patterns = {
                    "linkedin": r'linkedin\.com/company/([^/\s"\']+)',
                    "twitter": r'twitter\.com/([^/\s"\']+)',
                    "github": r'github\.com/([^/\s"\']+)'
                }

                for platform, pattern in social_patterns.items():
                    matches = re.findall(pattern, response.text)
                    if matches:
                        info["social_links"][platform] = matches[0]

                return info

        except Exception as e:
            self.logger.error(f"Failed to extract company info: {e}", url=url)
            return {}
