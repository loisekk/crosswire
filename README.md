# Crosswire v1.0.0

Content syndication engine — automatically cross-post content across LinkedIn, Dev.to, Hashnode, X (Twitter), Reddit, Indeed, and Naukri.

## Flow

```
LinkedIn ──→ X, Reddit, Naukri
Dev.to   ──→ LinkedIn, X, Reddit
Hashnode ──→ LinkedIn, X, Reddit
Naukri   ──→ X, Reddit, LinkedIn, Dev.to, Hashnode
Indeed   ──→ X, Reddit, LinkedIn
```

## Platform Support

| Platform | Source (read) | Target (write) | Method | Cost |
|----------|--------------|----------------|--------|------|
| LinkedIn | Limited | Yes | OAuth 2.0 API | Free |
| Dev.to | Yes | Yes | REST API | Free |
| Hashnode | Yes | Yes | GraphQL API | Free |
| X (Twitter) | Paid | Yes | PostPeer/OpenTweet | $0.002/post or $12/mo |
| Reddit | Yes | Yes | OAuth 2.0 API | Free |
| Indeed | No | Yes | Playwright browser | Free |
| Naukri | No | Yes | Playwright browser | Free |

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Playwright browsers (for Indeed/Naukri)
playwright install chromium

# 3. Configure API keys
copy .env.example .env
# Edit .env with your API keys

# 4. Edit config/settings.json with your credentials

# 5. Run in dry-run mode first
python main.py status

# 6. Start 24/7 automation
python supervisor.py
```

## Setup Guide

### 1. Dev.to API Key
1. Go to https://dev.to/settings/extensions
2. Generate an API Key
3. Add to `.env` as `DEVTO_API_KEY`

### 2. Hashnode API Key
1. Go to https://hashnode.com/settings/integrations
2. Create a Personal Access Token
3. Add to `.env` as `HASHNODE_API_KEY`

### 3. X (Twitter) - Third-Party API (Recommended)
**Option A: PostPeer ($0.002/post)**
1. Sign up at https://postpeer.dev
2. Connect your X account
3. Get API key from dashboard
4. Set `provider: "postpeer"` in config

**Option B: OpenTweet ($12/mo flat)**
1. Sign up at https://opentweet.io
2. Connect your X account
3. Get API key
4. Set `provider: "opentweet"` in config

**Option C: Official API ($100/mo)**
1. Apply at https://developer.x.com
2. Create project and app
3. Get API keys
4. Set `provider: "official"` in config

### 4. Reddit API
1. Go to https://www.reddit.com/prefs/apps
2. Create a "script" type app
3. Get client ID and secret
4. Add to `.env`

### 5. LinkedIn API
1. Go to https://www.linkedin.com/developers/
2. Create an app
3. Request "Share on LinkedIn" permission
4. Get access token
5. Add to `.env`

### 6. Indeed (Browser Automation)
1. Indeed has no public API for posting
2. Uses Playwright to automate browser
3. First run: browser opens, log in manually
4. Login state cached for 24h in `~/.crosspost/`

### 7. Naukri (Browser Automation)
1. Naukri has no public API
2. Uses Playwright to automate browser
3. First run: browser opens, log in manually
4. Login state cached for 24h in `~/.crosspost/`

## Usage

### Check for new posts and cross-post
```bash
python main.py check
```

### Post directly to specific platforms
```bash
# Pipe content
echo "My awesome content" | python main.py post -t x,reddit

# With arguments
python main.py post -t x,linkedin,reddit --title "My Post" --content "Hello world"

# Include URL
python main.py post -t reddit --title "Check this" --content "Great article" --url "https://example.com"
```

### Run 24/7 supervisor
```bash
python supervisor.py
```

### View status
```bash
python main.py status
```

## n8n Integration

Import `n8n-workflow.json` into your n8n instance:

1. Open n8n
2. Go to Workflows → Import
3. Select `n8n-workflow.json`
4. Configure credentials for each platform
5. Activate the workflow

**Webhook endpoint:** `http://localhost:5678/webhook/crosspost-webhook`

**Trigger example:**
```bash
curl -X POST http://localhost:5678/webhook/crosspost-webhook \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Check out my new blog post!",
    "title": "My Blog Post",
    "url": "https://example.com/blog",
    "tags": ["programming", "tech"],
    "source": "naukri"
  }'
```

## Configuration

### config/settings.json

```json
{
  "targets": {
    "x": {
      "enabled": true,
      "provider": "postpeer",
      "api_key": "YOUR_KEY"
    },
    "reddit": {
      "enabled": true,
      "subreddits": ["programming", "webdev"]
    },
    "naukri": {
      "enabled": true,
      "method": "browser_automation"
    }
  },
  "settings": {
    "dry_run": false
  }
}
```

### Dry Run Mode

By default, `dry_run: true` — no actual posts are made. Set to `false` when ready.

## Architecture

```
crosspost-automation/
├── main.py                 # CLI entry point
├── supervisor.py           # 24/7 auto-restart supervisor
├── webhook_server.py       # Webhook server for n8n
├── adapters/
│   ├── base.py             # Base classes
│   ├── devto.py            # Dev.to API
│   ├── hashnode.py         # Hashnode GraphQL API
│   ├── linkedin.py         # LinkedIn API
│   ├── x_twitter.py        # X (PostPeer/OpenTweet/Official)
│   ├── reddit.py           # Reddit OAuth2 API
│   └── browser_automation.py # Indeed/Naukri (Playwright)
├── config/
│   └── settings.json       # Main configuration
└── logs/                   # Application logs
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Playwright not found | `pip install playwright && playwright install chromium` |
| Login state expired | Delete `~/.crosspost/*.json` and re-login |
| Rate limited on Reddit | Wait 5-10 minutes between posts |
| X API errors | Check API key and provider setting |
| Indeed/Naukri login fails | Clear cached state, re-login manually |

## License

MIT
