# Deep Research AI Agent

A professional, agentic AI platform for **automated deep research and structured report generation**. Built with modern frameworks: **LangGraph**, **Gemini**, and **Tavily**.

  ## 🎯 Features

  - **LangGraph-Powered Agent**: Multi-step research workflow with intelligent query analysis
  - **Gemini Integration**: Advanced language understanding and content synthesis
  - **Tavily Web Search**: Accurate, efficient web searches for comprehensive research
  - **Professional Dark UI**: Modern dark-mode Streamlit interface with polished styling
  - **Visual Flowcharts**: Mermaid-based flow diagrams rendered inline in the report and UI
  - **Live Agent Report**: Real-time Gemini summary of current progress during execution
  - **Compact Timeline**: Single, minimal live timeline of LangGraph/Tavily/Gemini stages
  - **Single Progress Bar**: Weighted by stages and aligned with actual render timing

  ## 🏗️ Architecture
  
  ```mermaid
  flowchart LR
    UI[Streamlit Dark UI] --> QA[Query Analyzer]
    QA --> WR[Web Researcher (Tavily)]
    WR --> CA[Content Analyzer (Gemini)]
    CA -->|Parallel| PRG[Parallel Report Generator]
    PRG --> REP[Structured Markdown Report]
    REP --> DL[Download .md]
    REP --> VW[In-app View]
  
    subgraph Observability
      TL[Agent Timeline]:::obs
      AN[AI Action Narrative]:::obs
    end
  
    QA -.logs .-> TL
    WR -.logs .-> TL
    CA -.logs .-> TL
    PRG -.logs .-> TL
    TL --> AN
  
    classDef obs fill:#1f2937,stroke:#60a5fa,stroke-width:1px,color:#e5e7eb;
  ```
  ### Notes on Visuals & Observability

- The UI renders a Mermaid flowchart and a polished dark theme.
- The report renders Mermaid diagrams inline at their exact positions.
- A compact live Timeline shows one line per stage (QA, Web, Analysis, Report).
- A Live Agent Report (Gemini) narrates progress during execution.

## 📋 Project Structure

```
research-ai-agent/
{{ ... }}
├── app.py                    # Main Streamlit application
├── research_agent.py         # LangGraph research workflow
├── report_generator.py       # Parallel report generation
├── .env                      # API keys (not in git)
├── requirements.txt          # Python dependencies
├── .streamlit/
│   └── config.toml          # Streamlit configuration
└── README.md                # This file
```

## 🔧 Core Components

### 1. Research Agent (`research_agent.py`)

Implements a multi-step LangGraph workflow:

- **Query Analyzer**: Refines research queries and identifies focus areas
- **Web Researcher**: Conducts searches using Tavily API
- **Content Analyzer**: Synthesizes findings and identifies key insights
- **Report Generator**: Creates structured research output

### 2. Report Generator (`report_generator.py`)

Generates report sections in parallel:

- Executive Summary
- Key Findings
- Research Methodology
- Implications & Recommendations
- Conclusion

Uses ThreadPoolExecutor for efficient parallel execution.

### 3. Streamlit Interface (`app.py`)

Professional web UI featuring:

- Research query input
- Polished dark theme
- Single weighted progress bar aligned to render timing
- Compact live timeline (one line per stage)
- Live Agent Report (Gemini) during execution
- Inline Mermaid visuals inside the final report
- Report download functionality

### 4. Progress & Logging (`progress.py`)

- Lightweight event logger for internal steps (LangGraph, Tavily, Gemini)
- Emits structured events with timestamp, component, action, status, metadata
- Returned as `progress` in results and rendered in the UI

## 📊 Workflow

1. **User Input**: Enter a research query
2. **Query Analysis**: Agent refines the query and identifies research focus
3. **Web Research**: Tavily searches for relevant sources
4. **Content Analysis**: Gemini synthesizes findings
5. **Report Generation**: Drafted with concise, evidence‑oriented sections
6. **Inline Visuals**: Mermaid diagrams rendered in place inside the report
7. **Observability**: Weighted progress bar, compact timeline, live agent report
8. **Output**: Display and download options

## 🌐 Deployment Options

### Option 1: Streamlit Cloud (Recommended for Quick Deployment)

1. Push your project to GitHub
2. Go to [Streamlit Cloud](https://streamlit.io/cloud)
3. Create new app and connect to your GitHub repo
4. Add secrets in the Streamlit Cloud dashboard:
   ```
   GEMINI_API_KEY = your_key
   TAVILY_API_KEY = your_key
   ```
5. Deploy!

### Option 2: Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

Build and run:
```bash
docker build -t research-agent .
docker run -p 8501:8501 --env-file .env research-agent
```

### Option 3: Traditional Server (Ubuntu/Linux)

```bash
# Install Python and dependencies
sudo apt-get update
sudo apt-get install python3-pip

# Clone project and install
git clone <your-repo>
cd research-ai-agent
pip install -r requirements.txt

# Run with systemd or screen
streamlit run app.py --server.port 80
```

## 🔐 Security Best Practices

- **Never commit `.env` file** to version control
- Use environment variables for API keys
- For Streamlit Cloud, use the Secrets management feature
- Consider using API key rotation
- Monitor API usage for unexpected activity

## 📈 Performance Optimization

- **Parallel Execution**: Report sections generated concurrently
- **Caching**: Streamlit caches results automatically
- **Efficient Search**: Tavily provides optimized web search
- **Async Processing**: Support for future async enhancements

## 🎓 Learning Resources

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Gemini API Guide](https://ai.google.dev/gemini-api)
- [Tavily Search API](https://tavily.com/)
- [Streamlit Documentation](https://docs.streamlit.io/)

## ✅ What this demonstrates

✅ **Modern AI Frameworks**: LangGraph for agentic workflows
✅ **API Integration**: Seamless Gemini and Tavily integration
✅ **Live Observability**: Progress, timeline, and narrated status
✅ **Professional UI**: Clean, intuitive Streamlit interface
✅ **Production-Ready**: Deployment instructions and best practices
✅ **Scalability**: Designed for expansion and enhancement

## 📝 Example Queries

Try these research queries to see the agent in action:

- "What are the latest advances in agentic AI frameworks?"
- "How is AI transforming enterprise software development?"
- "What are the emerging trends in LLM applications?"
- "How do modern AI agents compare to traditional automation?"
- "What are the best practices for implementing AI in production?"

## 🐛 Troubleshooting

### API Key Issues
- Verify keys are correctly set in `.env`
- Check API quotas and usage limits
- Ensure keys have appropriate permissions

### Search Results Empty
  - Try simpler, more specific queries
  - Check Tavily API status
  - Verify internet connection

### Report Generation Slow
  - Reduce search results count in `research_agent.py`
  - Increase max_workers in `ParallelReportGenerator`
  - Check API response times
## 📄 License
  
  This project is provided as-is for educational and professional showcase purposes.
  
Copyright © 2025 Nitij Taneja <tanejanitij4002@gmail.com>
  
## 🙋 Support
  
  For issues or questions:
  1. Check the troubleshooting section
  2. Review API documentation
  3. Examine error logs in Streamlit console
---

**Built with ❤️ — Powered by Nitij Taneja**

*Last Updated: October 2025*
