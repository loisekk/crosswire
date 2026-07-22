# Crosswire v2.0

AI-powered content syndication engine — automatically cross-post content across 14 platforms with AI transformation.

## What It Does

1. **Post on LinkedIn** → triggers n8n workflow
2. **AI transforms content** per platform (Ollama, free & local)
3. **Cross-posts to 14 platforms** within 5 minutes
4. **Dashboard** monitors everything in real-time

```
LinkedIn ──→ AI Transform ──→ 14 Platforms
                      │
                      ├── X (Twitter) — punchy, 280 chars
                      ├── Reddit — casual, community
                      ├── Dev.to — technical, markdown
                      ├── Hashnode — blog-style
                      ├── Medium — storytelling
                      ├── Indeed — job posting
                      ├── Naukri — job posting
                      ├── Glassdoor — company review
                      ├── ZipRecruiter — job listing
                      ├── Shine.com — job posting
                      ├── TimesJobs — job listing
                      ├── Apna — short & simple
                      └── IIMJobs — executive-level
```

## Platform Support

| Platform | Type | Method | Cost |
|----------|------|--------|------|
| LinkedIn | API | OAuth 2.0 | Free |
| X (Twitter) | API | PostPeer/OpenTweet | $0.002/post |
| Reddit | API | OAuth 2.0 | Free |
| Dev.to | API | REST | Free |
| Hashnode | API | GraphQL | Free |
| Medium | Browser | Playwright | Free |
| Indeed | Browser | Playwright | Free |
| Naukri | Browser | Playwright | Free |
| Glassdoor | Browser | Playwright | Free |
| ZipRecruiter | Browser | Playwright | Free |
| Shine.com | Browser | Playwright | Free |
| TimesJobs | Browser | Playwright | Free |
| Apna | Browser | Playwright | Free |
| IIMJobs | Browser | Playwright | Free |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browsers
playwright install chromium

# 3. Install Ollama (for AI transformation)
# Download from https://ollama.com/download
ollama pull qwen2.5:3b

# 4. Configure credentials
copy .env.example .env
# Edit .env with your API keys

# 5. Start dashboard
python dashboard/app.py
# → opens http://localhost:8080

# 6. Start 24/7 automation
python supervisor.py
```

## Dashboard

Open `http://localhost:8080` after starting the dashboard.

- **Stats**: platforms active, posts published, AI engine, mode
- **Platform Grid**: 14 cards with live status dots
- **Cross-Post Form**: write content, AI transforms per platform
- **AI Preview**: see how content adapts for each platform
- **Dry Run**: test without actually posting
- **History**: track all cross-posts with status

### Dashboard API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/status` | GET | Engine status, platforms, history |
| `/api/post` | POST | Cross-post content to platforms |
| `/api/transform` | POST | AI content transformation preview |
| `/api/history` | GET | Post history |
| `/api/history/export` | GET | Full history export |
| `/api/settings` | GET | Current configuration |
| `/api/health/platforms` | GET | Per-platform health status |

## AI Transformation

Uses **Ollama** (local, free) with `qwen2.5:3b` model. Each platform gets content rewritten with:

- **LinkedIn**: Professional, hashtags, call-to-action
- **X**: Max 280 chars, punchy, emojis
- **Reddit**: Casual, community-focused
- **Dev.to**: Technical, markdown, educational
- **Hashnode**: Blog-style, detailed
- **Medium**: Storytelling narrative
- **Job platforms**: Professional, skills-focused

### Test AI Transformation

```python
from adapters.ai_transformer import AITransformer

transformer = AITransformer()
result = transformer.transform(
    content="Just built Crosswire!",
    platform="x",
    source_platform="linkedin"
)
print(result["content"])
```

## n8n Integration

Import `n8n-workflow.json` into your n8n instance:

1. Open n8n → Workflows → Import
2. Select `n8n-workflow.json`
3. Configure credentials for each platform
4. Activate the workflow

**Flow:** Webhook → Prepare Content → Split to Platforms → AI Transform → Route → Post to 14 Platforms

**Webhook endpoint:** `http://localhost:5679/webhook/crosspost-webhook`

```bash
curl -X POST http://localhost:5679/webhook/crosspost-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Check out my new blog post!",
    "title": "My Blog Post",
    "url": "https://example.com/blog",
    "source": "linkedin"
  }'
```

## CLI Usage

```bash
# Check for new posts and cross-post
python main.py check

# Post directly to specific platforms
python main.py post -t x,reddit,devto --title "My Post" --content "Hello world"

# Run 24/7 supervisor
python supervisor.py

# View status
python main.py status
```

## Architecture

```
crosswire/
├── main.py                    # CLI entry point
├── supervisor.py              # 24/7 auto-restart
├── webhook_server.py          # Webhook server (port 5679)
├── dashboard/
│   ├── app.py                 # Flask dashboard (port 8080)
│   └── templates/index.html   # Dashboard UI
├── adapters/
│   ├── base.py                # Base classes
│   ├── engine.py              # CrossPostEngine
│   ├── ai_transformer.py      # Ollama AI transformation
│   ├── devto.py               # Dev.to API
│   ├── hashnode.py            # Hashnode GraphQL
│   ├── linkedin.py            # LinkedIn API
│   ├── x_twitter.py           # X (PostPeer/OpenTweet)
│   ├── reddit.py              # Reddit OAuth2
│   ├── medium.py              # Medium (browser)
│   ├── browser_automation.py  # Indeed/Naukri (Playwright)
│   └── job_platforms.py       # Glassdoor/ZipRecruiter/etc
├── config/
│   ├── settings.json          # Main config (gitignored)
│   └── settings.example.json  # Template
├── n8n-workflow.json          # n8n workflow
├── .env.example               # API keys template
├── requirements.txt           # Python dependencies
└── CHANGELOG.md               # Version history
```

## Configuration

### config/settings.json

```json
{
  "targets": {
    "x": { "enabled": true, "provider": "postpeer" },
    "reddit": { "enabled": true },
    "linkedin": { "enabled": true },
    "devto": { "enabled": true },
    "hashnode": { "enabled": true },
    "indeed": { "enabled": true, "method": "browser_automation" },
    "naukri": { "enabled": true, "method": "browser_automation" }
  },
  "settings": {
    "dry_run": true,
    "ai_transform": true,
    "ai_model": "qwen2.5:3b",
    "ai_provider": "ollama"
  }
}
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Ollama not connecting | Run `ollama serve` in terminal |
| Playwright not found | `pip install playwright && playwright install chromium` |
| Login state expired | Delete `~/.crosspost/*.json` and re-login |
| Dashboard not loading | Check if port 8080 is available |
| AI transformation slow | First call loads model (~10s), subsequent calls are fast |

## License

MIT
