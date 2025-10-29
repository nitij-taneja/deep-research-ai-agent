"""
Deep Research AI Agent using LangGraph, Gemini, and Tavily
Designed for professional research and report generation
"""

import os
import json
from typing import Any, Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from tavily import TavilyClient
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from progress import ProgressLogger, set_current_logger, log_event

# Load environment variables
load_dotenv()

# Initialize API clients
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

gemini_client = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=GEMINI_API_KEY,
    # Lower temperature for crisper, more factual writing
    temperature=0.4
)

tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


# State models
class ResearchState(BaseModel):
    """State management for research workflow"""
    query: str
    research_topic: str = ""
    search_results: List[Dict[str, Any]] = Field(default_factory=list)
    analysis: str = ""
    report: str = ""
    status: str = "initialized"
    error: Optional[str] = None


class SearchResult(BaseModel):
    """Structure for search results"""
    title: str
    url: str
    content: str
    source: str


# Agent nodes
def query_analyzer(state: ResearchState) -> ResearchState:
    """Analyze and refine the research query"""
    try:
        log_event("LangGraph", "analyze_query", "started", "Analyzing query", {"query": state.query})
        prompt = f"""You are a senior research strategist. Analyze the user's query and produce
an action-ready brief to drive a high‑quality web research and reporting workflow.

USER QUERY: {state.query}

DELIVERABLE (concise, markdown):
### Refined Search Terms (3–6)
- terms…

### Research Focus Areas (3–5)
- focus…

### Key Questions to Answer (4–6)
- question…

### Evidence To Prioritize
- data points, benchmarks, real examples, recent updates (≤12 months) where possible

CONSTRAINTS:
- Professional, precise tone. No fluff. No speculation.
- Prefer recent, credible sources; note if the topic lacks fresh evidence.
"""
        log_event("Gemini", "invoke", "started", "Generating topic analysis")
        response = gemini_client.invoke(prompt)
        state.research_topic = response.content
        state.status = "query_analyzed"
        log_event("Gemini", "invoke", "completed", "Topic analysis generated")
        # Mark node completion for progress bars
        log_event("LangGraph", "analyze_query", "completed", "Query analysis completed")
        return state
    except Exception as e:
        state.error = f"Query analysis failed: {str(e)}"
        state.status = "error"
        log_event("LangGraph", "analyze_query", "error", state.error)
        return state


def web_researcher(state: ResearchState) -> ResearchState:
    """Conduct web research using Tavily"""
    try:
        if not state.query:
            state.error = "No query provided for research"
            state.status = "error"

        # Perform Tavily search
        log_event("Tavily", "search", "started", "Searching the web", {"max_results": 3})
        search_response = tavily_client.search(
            query=state.query,
            max_results=3,
            include_answer=False
        )

        # Process results
        results = []
        if "results" in search_response:
            for result in search_response["results"][:2]:
                results.append({
                    "title": result.get("title", ""),
                    "url": result.get("url", ""),
                    "content": result.get("content", ""),
                    "source": result.get("source", "")
                })

        state.search_results = results
        state.status = "research_completed"
        log_event("Tavily", "search", "completed", f"Found {len(results)} results")
        return state
    except Exception as e:
        state.error = f"Web research failed: {str(e)}"
        state.status = "error"
        log_event("Tavily", "search", "error", state.error)
        return state


def content_analyzer(state: ResearchState) -> ResearchState:
    """Analyze and synthesize research findings"""
    try:
        if not state.search_results:
            state.error = "No search results to analyze"
            state.status = "error"
            return state

        # Prepare content for analysis
        content_summary = "\n\n".join([
            f"Source: {r['title']}\nURL: {r['url']}\nContent: {r['content'][:200]}..."
            for r in state.search_results[:2]
        ])

        prompt = f"""You are an expert analyst. Synthesize the following findings into a crisp, evidence‑backed analysis, and project the near‑term future.

TOPIC: {state.query}

FINDINGS (title, url, excerpts):
{content_summary}

DELIVERABLE (markdown):
### Executive Insights (5–8 bullets)
- Each insight should be specific, decision‑useful, and grounded in evidence.

### Key Facts & Data
- Fact (source)
- Fact (source)

### Comparative Notes or Alternatives (if applicable)
- contrast…

### Risks, Limitations, or Unknowns
- risk…

### Recommendations (3–5, actionable)
- Start with a strong verb; include minimal rationale.

### 12–24 Month Outlook (scenarios)
- Best‑case, base‑case, risk‑aware scenarios and triggers to watch

### Enterprise Adoption Considerations
- Integration, governance, security, skills, and ROI notes

CITATIONS:
- Reference inline as (source: domain or short title) matching the provided URLs/titles. Do not fabricate sources.
STYLE:
- Professional, precise, minimal adjectives. Avoid hedging. No hallucinations.
"""

        # Mark node start and invoke LLM
        log_event("LangGraph", "analyze_content", "started", "Analyzing synthesized content")
        log_event("Gemini", "invoke", "started", "Synthesizing content analysis")
        response = gemini_client.invoke(prompt)
        state.analysis = response.content
        state.status = "analysis_completed"
        log_event("Gemini", "invoke", "completed", "Analysis synthesized")
        log_event("LangGraph", "analyze_content", "completed", "Content analysis completed")
        return state
    except Exception as e:
        state.error = f"Content analysis failed: {str(e)}"
        state.status = "error"
        log_event("Gemini", "invoke", "error", state.error)
        return state


def report_generator(state: ResearchState) -> ResearchState:
    """Generate structured research report"""
    try:
        # Include prior analysis to enable a higher‑quality draft
        prior_analysis = state.analysis or ""

        # Collate brief source list for better inline citations
        src_lines = []
        try:
            for i, s in enumerate((state.search_results or [])[:6], 1):
                src_lines.append(f"- {i}. {s.get('title','Untitled')} ({s.get('url','N/A')})")
        except Exception:
            pass
        src_block = "\n".join(src_lines)

        prompt = f"""You are a principal researcher. Draft a concise, professional report for:

TOPIC: {state.query}

PRIOR ANALYSIS (for reference):
{prior_analysis}

SOURCES (short list):
{src_block}

STRUCTURE (markdown):
## Executive Summary
- 4–6 bullets capturing the essence; avoid restating section headers.

## Research Methodology (short)
- Summarize the approach at a high level (analysis of reputable sources, timeframe, scope constraints).

## Discussion & Implications
- Most decision‑useful takeaways with brief rationale (reference sources inline by short title/domain).

## 12–24 Month Outlook
- Scenario‑based view (best/base/risk), key drivers, and signals to monitor.

## Enterprise Adoption Roadmap
- Phased steps (Pilot → Limited Deploy → Scale), risks/controls, KPIs, and ownership.

## Vendor Landscape (short)
- Compare LangChain, LangSmith, CrewAI, AutoGen (strengths, gaps, enterprise fit).

## Conclusion
- 2–3 sentences with a clear position and next steps.

STYLE & CONSTRAINTS:
- Precise, confident, and evidence‑oriented. No fluff; avoid over‑generalization.
- Use simple markdown lists and short paragraphs.
 - Include brief inline citations (source: short title/domain) when asserting facts.
"""
        log_event("LangGraph", "generate_report", "started", "Composing final report")
        log_event("Gemini", "invoke", "started", "Generating final report")
        response = gemini_client.invoke(prompt)
        state.report = response.content
        state.status = "report_generated"
        log_event("Gemini", "invoke", "completed", "Report generated")
        log_event("LangGraph", "generate_report", "completed", "Report generation completed")
        return state
    except Exception as e:
        state.error = f"Report generation failed: {str(e)}"
        state.status = "error"
        return state


# Build the research graph
def build_research_graph():
    """Construct the LangGraph workflow"""
    workflow = StateGraph(ResearchState)

    # Add nodes
    workflow.add_node("analyze_query", query_analyzer)
    workflow.add_node("research", web_researcher)
    workflow.add_node("analyze_content", content_analyzer)
    workflow.add_node("generate_report", report_generator)

    # Define edges
    workflow.add_edge(START, "analyze_query")
    workflow.add_edge("analyze_query", "research")
    workflow.add_edge("research", "analyze_content")
    workflow.add_edge("analyze_content", "generate_report")
    workflow.add_edge("generate_report", END)

    return workflow.compile()


# Main research execution function
async def execute_research(query: str) -> Dict[str, Any]:
    """Execute the complete research workflow"""
    try:
        graph = build_research_graph()
        # Set up progress logging for this run
        progress_logger = ProgressLogger()
        set_current_logger(progress_logger)

        initial_state = ResearchState(query=query)

        # Execute the graph
        result = graph.invoke(initial_state)

        # Normalize result to a dict to handle both dict and Pydantic object outputs
        if isinstance(result, dict):
            state_dict = result
        else:
            # Assume Pydantic model-like object
            state_dict = {
                "query": getattr(result, "query", None),
                "research_topic": getattr(result, "research_topic", ""),
                "search_results": getattr(result, "search_results", []),
                "analysis": getattr(result, "analysis", ""),
                "report": getattr(result, "report", ""),
                "status": getattr(result, "status", "")
            }

        output = {
            "success": True,
            "query": state_dict.get("query"),
            "topic_analysis": state_dict.get("research_topic", ""),
            "search_results": state_dict.get("search_results", []),
            "analysis": state_dict.get("analysis", ""),
            "report": state_dict.get("report", ""),
            "status": state_dict.get("status", ""),
            "progress": [
                {
                    "timestamp": e.timestamp,
                    "component": e.component,
                    "action": e.action,
                    "status": e.status,
                    "message": e.message,
                    "meta": e.meta,
                }
                for e in progress_logger.events
            ],
        }
        set_current_logger(None)
        return output
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "query": query
        }


if __name__ == "__main__":
    # Test the agent
    import asyncio

    async def test():
        result = await execute_research("What are the latest advances in AI agents?")
        print(json.dumps(result, indent=2))

    asyncio.run(test())
