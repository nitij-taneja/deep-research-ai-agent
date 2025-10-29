"""
Streamlit Web Application for Deep Research AI Agent
Interactive and professional interface for LinkedIn showcase
"""

import streamlit as st
import asyncio
import json
import os
from typing import Dict, Any
from research_agent import execute_research
from report_generator import generate_research_report
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
import threading
import time
from progress import get_current_logger, ProgressLogger, set_current_logger
import re

# --- Configuration ---
st.set_page_config(
    page_title="Deep Research AI Agent",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Helper Functions ---
@st.cache_data(show_spinner=False)
def run_research(query: str) -> Dict[str, Any]:
    """Synchronous wrapper to run the async research execution"""
    return asyncio.run(execute_research(query))

def generate_report_from_research(research_result: Dict[str, Any]) -> str:
    """Generate the final report using the parallel generator"""
    if research_result.get("success"):
        return generate_research_report(
            query=research_result["query"],
            analysis=research_result["analysis"],
            search_results=research_result["search_results"]
        )
    return "Report generation failed due to previous research error."

# --- Mermaid Renderer (must be defined before use) ---
def render_mermaid(mermaid_code: str):
    """Render a Mermaid diagram via components.html"""
    html = f"""
    <div id=\"mermaid-container\">
      <pre class=\"mermaid\">{mermaid_code}</pre>
    </div>
    <script src=\"https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js\"></script>
    <script>
      if (window.mermaid) {{
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
      }}
    </script>
    """
    components.html(html, height=420, scrolling=False)

def build_flow_mermaid(active: str = "") -> str:
    highlight = active or ""
    code = f"""
flowchart LR
  U[User Query] --> QA[Query Analyzer]
  QA --> WR[Web Researcher]
  WR --> CA[Content Analyzer]
  CA -->|Parallel| ES[Exec Summary]
  CA -->|Parallel| KF[Key Findings]
  CA -->|Parallel| RM[Methodology]
  CA -->|Parallel| IR[Implications]
  ES --> RP[Final Report]
  KF --> RP
  RM --> RP
  IR --> RP

  classDef active fill:#334155,stroke:#60a5fa,stroke-width:2px,color:#e5e7eb;
  class {highlight} active;
"""
    return code

# --- Progress Narrative (Gemini) ---
def generate_progress_narrative(events: Any) -> str:
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Gemini API key missing; cannot generate narrative."
        client = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key, temperature=0.4)
        bullet_log = "\n".join(
            [
                f"- [{e.get('timestamp','')}] {e.get('component','')} {e.get('action','')} -> {e.get('status','')}: {e.get('message','')}"
                for e in (events or [])
            ]
        )
        prompt = f"""Summarize the following agent action log into a short, engaging narrative (3-5 sentences)
with a professional tone, calling out major steps and any errors succinctly. End with the outcome.

Action Log:\n{bullet_log}"""
        resp = client.invoke(prompt)
        return resp.content or "(No narrative generated)"
    except Exception as ex:
        return f"Narrative generation failed: {ex}"

# --- Mermaid Renderer ---
def render_mermaid(mermaid_code: str):
    """Render a Mermaid diagram via components.html"""
    html = f"""
    <div id="mermaid-container">
      <pre class="mermaid">{mermaid_code}</pre>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <script>
      if (window.mermaid) {{
        mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
      }}
    </script>
    """
    components.html(html, height=420, scrolling=False)

# --- Progress Narrative (Gemini) ---
def generate_progress_narrative(events: Any) -> str:
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Gemini API key missing; cannot generate narrative."
        client = ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=api_key, temperature=0.4)
        bullet_log = "\n".join(
            [
                f"- [{e.get('timestamp','')}] {e.get('component','')} {e.get('action','')} -> {e.get('status','')}: {e.get('message','')}"
                for e in (events or [])
            ]
        )
        prompt = f"""Summarize the following agent action log into a short, engaging narrative (3-5 sentences) 
with a professional tone, calling out major steps and any errors succinctly. End with the outcome.

Action Log:\n{bullet_log}"""
        resp = client.invoke(prompt)
        return resp.content or "(No narrative generated)"
    except Exception as ex:
        return f"Narrative generation failed: {ex}"

# --- Streamlit UI Components ---

def display_results(research_result: Dict[str, Any]):
    """Display the detailed research and report results"""
    if not research_result.get("success"):
        st.error(f"Research failed with error: {research_result.get('error', 'Unknown Error')}")
        return

    st.markdown("### ✅ <span class='success-glow'>Research and Report Generation Completed</span>", unsafe_allow_html=True)

    # Generate the final structured report
    final_report = generate_report_from_research(research_result)

    # --- Report Display (inline Mermaid rendering) ---
    st.markdown("## 📄 Final Research Report")
    # Interleave Markdown and Mermaid blocks so visuals appear in-place
    pattern = re.compile(r"```mermaid\n([\s\S]*?)```", re.MULTILINE)
    pos = 0
    for m in pattern.finditer(final_report):
        # Markdown segment before this mermaid block
        before = final_report[pos:m.start()]
        if before.strip():
            st.markdown(before)
        # Mermaid diagram
        code = m.group(1).strip()
        render_mermaid(code)
        pos = m.end()
    # Remainder after last mermaid block
    tail = final_report[pos:]
    if tail.strip():
        st.markdown(tail)

    # Note: Do not show flowchart during the report section to keep it clean

    # Note: Action Narrative removed per UX request

    # --- Download Button ---
    st.download_button(
        label="Download Report (Markdown)",
        data=final_report,
        file_name=f"research_report_{research_result['query'][:20].replace(' ', '_')}.md",
        mime="text/markdown"
    )

    # Note: Full Agent Timeline and Detailed Process moved to live view; not repeated after report

# --- Main Application Logic ---

def main():
    """Main function to run the Streamlit app"""
    st.markdown(
        """
        <section style="display:flex;flex-direction:column;gap:10px;margin-bottom:8px;">
          <div style="display:flex;align-items:center;justify-content:space-between;">
            <div style="font-size:34px;font-weight:800;letter-spacing:.2px;">🧠 Deep Research AI Agent</div>
            <div style="font-size:12px;color:var(--muted);">Powered by <b>Nitij Taneja</b></div>
          </div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <div class="pill">Agentic</div>
            <div class="pill">Parallel</div>
            <div class="pill">Professional</div>
          </div>
          <div class="highlight-card">
            <p style="margin:0;opacity:.9">A professional AI platform for automated deep research and structured, beautiful reporting.<br>
            Powered by <b>LangGraph</b>, <b>Gemini</b>, and <b>Tavily</b>.</p>
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )

    # --- Sidebar for API Keys (Optional, but good practice for deployment) ---
    with st.sidebar:
        st.header("Configuration")
        st.markdown(
            """
            This application uses the Gemini and Tavily API keys provided in the `.env` file.
            For security, please ensure your keys are correctly configured.
            """
        )
        st.info(f"Gemini Key Status: {'Loaded' if os.getenv('GEMINI_API_KEY') else 'Missing'}")
        st.info(f"Tavily Key Status: {'Loaded' if os.getenv('TAVILY_API_KEY') else 'Missing'}")
        st.markdown("---")
        st.caption("Built with Streamlit, LangGraph, Gemini, and Tavily.")


    # --- Input Form ---
    with st.form("research_form"):
        query = st.text_input(
            "Enter your research query:",
            placeholder="e.g., The future of agentic AI frameworks in enterprise applications"
        )
        submitted = st.form_submit_button("Start Deep Research", help="Runs the multi-step research pipeline", type="primary")

    if submitted and query:
        # Placeholders for live UI
        st.markdown("## 🗺️ Research Flow")
        flow_ph = st.empty()
        progress_ph = st.container()
        timeline_ph = st.empty()

        # Start background execution
        result_holder: Dict[str, Any] = {}

        def _run():
            result_holder["result"] = run_research(query)

        # Ensure a fresh logger is visible to the UI loop
        set_current_logger(ProgressLogger())
        t = threading.Thread(target=_run, daemon=True)
        t.start()

        last_len = 0
        active_stage = "U"
        # Track latest status per (component, action) to avoid repeats and allow in-place updates
        event_state: dict[tuple[str, str], dict] = {}

        # Render flowchart once (no repeated renders)
        with flow_ph:
            render_mermaid(build_flow_mermaid(active_stage))

        # Prepare progress bars
        with progress_ph:
            st.markdown("### Progress")
            overall_bar = st.progress(0)
            progress_note_ph = st.empty()
            # Live Agent Narrator sits BELOW the bar per UX
            narrator_ph = st.empty()

        # Live poll progress while the background thread runs
        # track started/completed flags for weighted progress
        qa_started = False; qa_done = False
        wr_started = False; wr_done = False
        ca_started = False; ca_done = False
        rp_started = False; rp_done = False
        live_findings_ph = st.empty()
        wr_sources_ph = st.empty()
        last_narration_len = 0
        last_narr_time = 0.0
        wr_shown_sources = False

        while t.is_alive():
            logger = get_current_logger()
            events = list(logger.events) if logger else []

            # Update active stage based on latest event
            if events:
                e = events[-1]
                if e.component == "LangGraph" and e.action == "analyze_query":
                    active_stage = "QA"
                elif e.component == "Tavily" and e.action == "search":
                    active_stage = "WR"
                elif e.component == "LangGraph" and e.action == "analyze_content":
                    active_stage = "CA"
                elif e.component == "LangGraph" and e.action == "generate_report":
                    active_stage = "RP"

            # Do not re-render the flowchart repeatedly; no active badge/status row per UX

            # Render only new events; update in-place state per (component, action)
            if len(events) > last_len:
                chunk = events[last_len:]
                for x in chunk:
                    # Update stage flags on started/completed events
                    if x.component == "LangGraph" and x.action == "analyze_query":
                        if x.status == "started": qa_started = True
                        if x.status == "completed": qa_done = True
                    elif x.component == "Tavily" and x.action == "search":
                        if x.status == "started": wr_started = True
                        if x.status == "completed": wr_done = True
                    elif x.component == "LangGraph" and x.action == "analyze_content":
                        if x.status == "started": ca_started = True
                        if x.status == "completed": ca_done = True
                    elif x.component == "LangGraph" and x.action == "generate_report":
                        if x.status == "started": rp_started = True
                        if x.status == "completed": rp_done = True

                    # Record the latest status for this (component, action)
                    event_state[(x.component, x.action)] = {
                        "timestamp": x.timestamp,
                        "status": x.status,
                        "message": x.message,
                    }

                # Update single overall progress bar using weighted, real-time stages
                # Weights: QA(20), WR(30), CA(30), RP(20)
                # Partial credit for QA/WR/CA on start; REPORT only counts on completion to avoid early fill
                prog = 0
                prog += 8 if qa_started and not qa_done else (20 if qa_done else 0)
                prog += 12 if wr_started and not wr_done else (30 if wr_done else 0)
                prog += 12 if ca_started and not ca_done else (30 if ca_done else 0)
                prog += 0 if rp_started and not rp_done else (20 if rp_done else 0)

                # Hold bar under 85% until the actual result object exists, then jump to 100%
                result_ready = "result" in result_holder
                displayed = 100 if result_ready and rp_done else min(85, int(prog))
                overall_bar.progress(displayed)
                if not result_ready:
                    progress_note_ph.info("Agent is running…")

                # Compact single timeline (no 4 sections)
                def fmt_line(comp: str, action: str) -> str:
                    d = event_state.get((comp, action))
                    if not d: return ""
                    comp_emoji = {"LangGraph": "🧩", "Tavily": "🌐", "Gemini": "✨"}.get(comp, "🔸")
                    status_emoji = "✅" if d["status"] == "completed" else "▶️"
                    return f"{comp_emoji} {status_emoji} [{d['timestamp']}] {comp} · {action} — {d['status']}"

                lines = list(filter(None, [
                    fmt_line("LangGraph", "analyze_query"),
                    fmt_line("Tavily", "search"),
                    fmt_line("LangGraph", "analyze_content"),
                    fmt_line("LangGraph", "generate_report"),
                ]))
                # Include fetched count inline when available
                tav = event_state.get(("Tavily", "search"))
                if tav and tav.get("status") == "completed" and "Found" in (tav.get("message") or ""):
                    import re as _re
                    m = _re.search(r"Found\s+(\d+)", tav.get("message") or "")
                    if m and len(lines) > 1:
                        lines[1] += f"  •  📥 {m.group(1)} sources"
                if lines:
                    timeline_ph.markdown("\n".join(lines))

                # Live findings once when analysis completes
                if ca_done and live_findings_ph:
                    ca_text = result_holder.get("result", {}).get("analysis", "")
                    if ca_text:
                        bullets = [b.strip() for b in ca_text.split("\n") if b.strip().startswith(("-", "•", "1.", "2.", "3."))]
                        bullets = bullets[:3] if bullets else [ca_text[:240] + ("..." if len(ca_text) > 240 else "")]
                        live_findings_ph.markdown("### Live Findings\n" + "\n".join(bullets))

                # Show source titles when web research completes (once)
                if not wr_shown_sources and wr_done:
                    sr = result_holder.get("result", {}).get("search_results", []) or []
                    if sr:
                        titles = [f"- {i+1}. {x.get('title','Untitled')}" for i, x in enumerate(sr[:5])]
                        wr_sources_ph.markdown("### Sources fetched\n" + "\n".join(titles))
                        wr_shown_sources = True

                # Live Agent Narrator (Gemini) — throttled (below the bar)
                try:
                    import time as _t
                    now = _t.time()
                    if len(events) != last_narration_len and (now - last_narr_time) > 5:
                        summary = generate_progress_narrative([
                            {
                                "timestamp": d.get("timestamp"),
                                "component": c,
                                "action": a,
                                "status": d.get("status"),
                                "message": d.get("message"),
                            }
                            for (c,a), d in event_state.items()
                        ])
                        if summary:
                            narrator_ph.markdown("### 🎙️ Live Agent Report")
                            narrator_ph.info(summary)
                        last_narration_len = len(events)
                        last_narr_time = now
                except Exception:
                    pass

                last_len = len(events)

            # Narrator panel handles live status; no separate running label
            time.sleep(0.35)

        # Ensure bar aligns with final rendering: maintain hold, then finalize to 100
        progress_note_ph.info("Finalizing and rendering report…")
        try:
            final_summary = generate_progress_narrative([
                {
                    "timestamp": d.get("timestamp"),
                    "component": c,
                    "action": a,
                    "status": d.get("status"),
                    "message": d.get("message"),
                }
                for (c,a), d in event_state.items()
            ])
            if final_summary:
                narrator_ph.markdown("### ✅ Agent Finished")
                narrator_ph.success(final_summary)
        except Exception:
            pass
        research_result = result_holder.get("result", {"success": False, "error": "Unknown error"})
        # Now fill to 100 just before displaying results
        overall_bar.progress(100)
        progress_note_ph.success("Report ready.")

        # Display results
        display_results(research_result)
    elif submitted and not query:
        st.warning("Please enter a research query to begin.")

if __name__ == "__main__":
    main()
