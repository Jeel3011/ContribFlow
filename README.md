# ContribFlow 🚀

**ContribFlow** is a 4-Stage, Multi-Agent OSS Contribution Co-Pilot built for the IBM Bob Hackathon. It orchestrates specialized AI agents to guide developers from finding an open issue all the way to a pristine pull request, using **LangGraph** for autonomous orchestration.

## 🌟 The 4-Stage Multi-Agent Pipeline

ContribFlow is powered by 4 specialized agents working in sequence:

1. **Gap Finder (Stage 1):** Scans repositories for gaps (missing tests, poor error handling) and recommends contributions. *Optimization: Pre-scores file suspiciousness locally to save API tokens.*
2. **Idea Deduplication (Stage 2):** Checks open issues and PRs using semantic vector embeddings and LLM verification to ensure you aren't building something already in progress.
3. **Change Impact Analysis (Stage 3):** Uses GitHub Code Search and dependency mapping to predict the blast radius of your change, providing **Explainable Dependency Traces**.
4. **Pre-PR Quality Check (Stage 4):** A hybrid agent that runs deterministic `ruff` linting merged with LLM semantic reviews to guarantee pristine code before CI/CD.

## 🏗️ Architecture
- **Backend:** FastAPI + Python
- **Orchestration:** LangGraph (StateGraph) + LangChain + Pydantic Structured Outputs
- **Frontend:** React + Vite
- **Data Source:** GitHub REST & Code Search APIs

## 🚀 Quickstart

### Prerequisites
- Python 3.10+
- Node.js 18+
- GitHub Personal Access Token (Classic)
- OpenAI API Key

### 1. Backend Setup
```bash
cd ContribFlow
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create a .env file with your keys
echo "GITHUB_TOKEN=your_github_token" > .env
echo "OPENAI_API_KEY=your_openai_key" >> .env

# Run the backend
uvicorn main:app --port 8000 --reload
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to start contributing!

## 🛡️ Hackathon Constraints Handled
- **Token Budgets:** We aggressively pre-filter files (e.g. `score_file_suspiciousness`, static import tracking) before invoking the LLM, keeping our API spend extremely low.
- **Bobcoin Preservation:** By implementing an `impact_only` routing mode, users don't waste Bobcoins on full pipeline runs if they only want blast radius analysis.
- **Compliance:** 100% adherence to the `ContribFlow_IO_Design.md` contract using Pydantic `with_structured_output()`.

## 📁 Repository Structure
- `/ContribFlow` - FastAPI Backend & LangGraph Agent Nodes
- `/frontend` - React UI and Components
- `/bob_sessions` - Exported IBM Bob prompt histories for Hackathon Validation
