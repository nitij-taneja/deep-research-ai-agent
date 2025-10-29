"""
Automated Report Generation with Parallel Execution
Efficiently generates structured reports from research data
"""

import asyncio
import json
from datetime import datetime
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=GEMINI_API_KEY,
    temperature=0.4
)


@dataclass
class ReportSection:
    """Structure for report sections"""
    title: str
    content: str
    order: int


class ParallelReportGenerator:
    """Generate report sections in parallel for efficiency"""

    def __init__(self, max_workers: int = 2):
        # Reduce parallelism to avoid hitting API rate/quotas
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def _safe_invoke(self, prompt: str, fallback: str, sleep_sec: float = 0.4) -> str:
        """Invoke Gemini with a lightweight backoff; return fallback on exhaustion/errors."""
        try:
            time.sleep(sleep_sec)
            resp = gemini_client.invoke(prompt)
            return getattr(resp, "content", "") or fallback
        except Exception:
            return fallback

    def _generate_executive_summary(self, query: str, analysis: str) -> ReportSection:
        """Generate executive summary"""
        prompt = f"""Create a concise executive summary (120-180 words) for this research:

Topic: {query}
Analysis: {analysis[:700]}...

Provide only the summary text."""

        text = self._safe_invoke(prompt, fallback=(analysis[:300] + "...") if analysis else "")
        return ReportSection(
            title="Executive Summary",
            content=text,
            order=1
        )

    def _generate_key_findings(self, analysis: str, search_results: List[Dict]) -> ReportSection:
        """Generate key findings section"""
        sources_text = "\n".join([
            f"- {r['title']}: {r['content'][:140]}..."
            for r in search_results[:2]
        ])

        prompt = f"""Extract and format key findings from this research analysis. Be specific and evidence‑oriented. Include brief inline citations using the source title/domain in parentheses:

Analysis: {analysis[:1800]}

Supporting Sources:
{sources_text}

Format as a bulleted list of 5–7 key findings."""

        text = self._safe_invoke(prompt, fallback="- Insufficient data to extract key findings.")
        return ReportSection(
            title="Key Findings",
            content=text,
            order=2
        )

    def _generate_methodology(self, query: str) -> ReportSection:
        """Generate methodology section"""
        prompt = f"""Write a brief methodology section (80-120 words) for research on: {query}

Include:
- Research approach
- Data sources used (web search via Tavily)
- Analysis methods
- Limitations

Provide only the methodology text."""

        text = self._safe_invoke(prompt, fallback="Desk research using reputable web sources; qualitative synthesis; limited by public data and recency.")
        return ReportSection(
            title="Research Methodology",
            content=text,
            order=3
        )

    def _generate_implications(self, analysis: str) -> ReportSection:
        """Generate implications and recommendations"""
        prompt = f"""Based on this analysis, provide implications and recommendations (120-180 words). Be concise and action‑oriented:

{analysis[:1200]}

Include:
- Key implications
- Recommendations for further research
- Practical applications

Provide only the implications text."""

        text = self._safe_invoke(prompt, fallback="- Further research recommended; limited evidence available.")
        return ReportSection(
            title="Implications & Recommendations",
            content=text,
            order=4
        )

    def _generate_conclusion(self, query: str, analysis: str) -> ReportSection:
        """Generate conclusion section"""
        prompt = f"""Write a professional conclusion (90-130 words) for research on: {query}

Analysis summary: {analysis[:400]}...

Provide only the conclusion text."""

        text = self._safe_invoke(prompt, fallback="This research indicates promising momentum; however, conclusions are tentative given limited public evidence.")
        return ReportSection(
            title="Conclusion",
            content=text,
            order=5
        )

    async def generate_report_async(
        self,
        query: str,
        analysis: str,
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate complete report with parallel section generation"""

        loop = asyncio.get_event_loop()

        # Execute all section generations in parallel
        tasks = [
            loop.run_in_executor(
                self.executor,
                self._generate_executive_summary,
                query,
                analysis
            ),
            loop.run_in_executor(
                self.executor,
                self._generate_key_findings,
                analysis,
                search_results
            ),
            loop.run_in_executor(
                self.executor,
                self._generate_methodology,
                query
            ),
            loop.run_in_executor(
                self.executor,
                self._generate_implications,
                analysis
            ),
            loop.run_in_executor(
                self.executor,
                self._generate_conclusion,
                query,
                analysis
            ),
        ]

        sections = await asyncio.gather(*tasks)

        # Sort sections by order
        sections.sort(key=lambda x: x.order)

        # Compile report
        report_content = self._compile_report(
            query=query,
            sections=sections,
            search_results=search_results
        )

        return {
            "success": True,
            "query": query,
            "report": report_content,
            "sections_count": len(sections),
            "generated_at": datetime.now().isoformat(),
            "sources_count": len(search_results)
        }

    def _compile_report(
        self,
        query: str,
        sections: List[ReportSection],
        search_results: List[Dict[str, Any]]
    ) -> str:
        """Compile all sections into final report"""

        # Build a compact literature review from sources
        literature_points = []
        for i, src in enumerate(search_results[:5], 1):
            title = src.get('title', 'Untitled')
            url = src.get('url', 'N/A')
            snippet = (src.get('content', '') or '')[:200].replace('\n', ' ')
            literature_points.append(f"- {title} — {snippet}… (URL: {url})")

        literature_review = "\n".join(literature_points) if literature_points else "- N/A"

        # Create a simple findings relationship diagram from sources
        mermaid_findings = [
            "graph LR",
            "  A[Query] --> B[Key Findings]",
        ]
        for i, src in enumerate(search_results[:3], 1):
            sid = f"S{i}"
            stitle = src.get('title', f'Source {i}').replace('[', '(').replace(']', ')')
            mermaid_findings.append(f"  {sid}[{stitle}] --> B")
        mermaid_block = "\n".join(mermaid_findings)

        # Map generated sections for convenience
        sec_map = {s.title: s for s in sections}
        exec_summary = sec_map.get("Executive Summary", ReportSection("Executive Summary", "", 1)).content
        methodology = sec_map.get("Research Methodology", ReportSection("Research Methodology", "", 3)).content
        key_findings = sec_map.get("Key Findings", ReportSection("Key Findings", "", 2)).content
        implications = sec_map.get("Implications & Recommendations", ReportSection("Implications & Recommendations", "", 4)).content
        conclusion = sec_map.get("Conclusion", ReportSection("Conclusion", "", 5)).content

        report = f"""# 🧠 Research Report: {query}

Generated: {datetime.now().strftime('%B %d, %Y at %H:%M:%S')}

---

## Abstract

{exec_summary}

## Methodology

{methodology}

## Literature Review

{literature_review}

## Key Findings

{key_findings}

### Findings Overview (Visual)

```mermaid
{mermaid_block}
```

## Discussion

{implications}

## Conclusion

{conclusion}

## Sources

"""

        # Add sources
        # (Already opened a Sources section)
        for i, source in enumerate(search_results[:10], 1):
            report += f"{i}. **{source.get('title', 'Untitled')}**\n"
            report += f"   URL: {source.get('url', 'N/A')}\n"
            report += f"   Source: {source.get('source', 'Unknown')}\n\n"

        report += f"\n---\n\n*Report generated by Research AI Agent*\n"
        report += f"*Total sources analyzed: {len(search_results)}*\n"

        return report

    def generate_report_sync(
        self,
        query: str,
        analysis: str,
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Synchronous wrapper for report generation"""
        return asyncio.run(
            self.generate_report_async(query, analysis, search_results)
        )


# Utility function for direct use
def generate_research_report(
    query: str,
    analysis: str,
    search_results: List[Dict[str, Any]]
) -> str:
    """Generate a complete research report"""
    generator = ParallelReportGenerator(max_workers=4)
    result = generator.generate_report_sync(query, analysis, search_results)
    return result["report"] if result["success"] else "Report generation failed"


if __name__ == "__main__":
    # Test report generation
    test_query = "Artificial Intelligence in Healthcare"
    test_analysis = "AI is revolutionizing healthcare through diagnostic improvements and personalized medicine."
    test_results = [
        {
            "title": "AI in Medical Diagnosis",
            "url": "https://example.com/1",
            "content": "Recent studies show AI improving diagnostic accuracy",
            "source": "Medical Journal"
        },
        {
            "title": "Machine Learning in Healthcare",
            "url": "https://example.com/2",
            "content": "ML algorithms are being deployed in hospitals worldwide",
            "source": "Tech News"
        }
    ]

    report = generate_research_report(test_query, test_analysis, test_results)
    print(report)
