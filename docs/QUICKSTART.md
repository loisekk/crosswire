# Quick Start Guide

Get Crosswire running in 5 minutes.

## Prerequisites

- Python 3.9+
- pip
- Git

## Step 1: Clone and Install

```bash
git clone https://github.com/loisekk/crosswire.git
cd crosswire
pip install -r requirements.txt
playwright install chromium
```

## Step 2: Install Ollama (for AI transformation)

```bash
# Download from https://ollama.com/download
# Then pull a model:
ollama pull qwen2.5:3b
```

## Step 3: Configure

```bash
# Copy example config
copy .env.example .env

# Edit .env with your API keys
# Edit config/settings.json with your credentials
```

## Step 4: Start Dashboard

```bash
python dashboard/app.py
# Open http://localhost:8080
```

## Step 5: Test

1. Open the dashboard
2. Write some content in the form
3. Click "Dry Run" to test
4. Check the AI Preview panel

## Step 6: Go Live

1. Set `dry_run: false` in config/settings.json
2. Click "Cross-Post Now" in the dashboard
3. Or run `python supervisor.py` for 24/7 automation

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Ollama not connecting | Run `ollama serve` |
| Playwright errors | Run `playwright install chromium` |
| Dashboard won't start | Check if port 8080 is in use |
| Posts failing | Check API keys in .env |
