# ContribFlow - Quick Start Guide

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Git
- GitHub Personal Access Token
- OpenAI API Key (for Stage 3)

### Installation

1. **Clone the repository**
```bash
git clone <your-repo-url>
cd ContribFlow
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables**

Edit `.env` file and add your API keys:
```bash
GITHUB_TOKEN=your_github_token_here
OPENAI_API_KEY=your_openai_key_here
```

**Get your tokens:**
- GitHub Token: https://github.com/settings/tokens (needs `public_repo` scope)
- OpenAI Key: https://platform.openai.com/api-keys

### Running the Application

#### Option 1: Automated Start (Recommended)

**Windows PowerShell:**
```powershell
.\start.ps1
```

**Windows Command Prompt:**
```cmd
.\start.bat
```

**Linux/Mac:**
```bash
chmod +x start.sh
./start.sh
```

This will start both the backend API and frontend UI automatically.

#### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
python -m streamlit run app.py
```

### Access the Application

- **Frontend UI:** http://localhost:8501
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs

## 📋 Usage

### Stage 1: Gap Finder
1. Enter a GitHub repository URL in the sidebar
2. Click "Analyze Repository"
3. Copy the generated prompt to Bob IDE
4. Paste Bob's response back to see identified gaps

### Stage 2: Idea Deduplication
1. Enter your contribution idea
2. Click "Check for Conflicts"
3. Review any conflicting issues/PRs

### Stage 3: Change Impact Analysis
1. Describe your proposed changes
2. Optionally paste a git diff
3. Click "Analyze Impact"
4. Review affected files and services

### Stage 4: Pre-PR Quality Check
1. Paste your git diff
2. Click "Run Static Checks"
3. Review issues found
4. Optionally use Bob for deeper analysis

## 🎯 Demo Repositories

Good repositories for testing:
- `opensre/tracer-cloud` (validated ground truth)
- `pallets/flask` (small, well-structured)
- `requests/requests` (popular, active)

## 📂 Ready-to-Use Examples

Two example files are provided in the `examples/` folder with pre-filled inputs for all 4 stages:

- `examples/example1_requests_library.md` — uses `psf/requests`
- `examples/example2_flask.md` — uses `pallets/flask`

Each file contains the repo URL, stage inputs, and expected outputs ready to copy-paste into the UI.

## 🔧 Troubleshooting

### Backend not starting
- Check if port 8000 is already in use
- Verify `.env` file has valid API keys
- Check Python version: `python --version`

### Frontend not loading
- Check if port 8501 is already in use
- Verify Streamlit is installed: `pip show streamlit`
- Check backend is running at http://localhost:8000/health

### API Rate Limits
- GitHub: 5,000 requests/hour with token
- OpenAI: Depends on your plan
- If rate limited, wait and try again

### Stage 3 Errors
- Verify `OPENAI_API_KEY` is set in `.env`
- Check OpenAI account has credits
- Try with a smaller repository

## 📊 API Endpoints

All endpoints are prefixed with `/api`:

- `POST /api/stage1/analyze` - Gap Finder
- `POST /api/stage2/deduplicate` - Idea Dedup
- `POST /api/stage3/impact` - Impact Analysis
- `POST /api/stage4/review` - Quality Check

See full documentation at http://localhost:8000/docs

## 🐛 Known Issues

1. **Large repositories may timeout** - Limit to repos with < 1000 files
2. **Stage 3 requires OpenAI** - Other stages work without it
3. **Bob integration is manual** - Copy-paste workflow by design

## 💡 Tips

- Start with small repositories for testing
- Use the sidebar to set repository once for all stages
- Static checks in Stage 4 run instantly (no AI needed)
- Stage 3 is most token-intensive - use sparingly

## 📞 Support

For issues or questions:
1. Check the logs in terminal windows
2. Verify API keys are valid
3. Test with `/health` endpoint
4. Review error messages in UI

---

**Built for IBM Bob Hackathon 2026**