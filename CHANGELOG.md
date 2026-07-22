# Changelog

## v2.0.0 (2026-07-23)

### Added
- **AI Content Transformer** — Ollama-powered content transformation per platform
  - LinkedIn: Professional tone, hashtags, call-to-action
  - X/Twitter: Max 280 chars, punchy, emojis
  - Reddit: Casual, community-focused, no corporate speak
  - Dev.to: Technical, markdown, code blocks
  - Hashnode: Blog-style, detailed headings
  - Medium: Storytelling narrative
  - Job platforms: Professional, skills-focused
- **8 new platform adapters**: Medium, Glassdoor, ZipRecruiter, Shine.com, TimesJobs, Apna, IIMJobs
- **Web dashboard** at localhost:8080
  - Stats row (platforms, posts, AI engine, mode)
  - 14-platform grid with live status dots
  - Cross-post form with AI transformation
  - AI Preview panel — see how content adapts per platform
  - Dry run mode
  - Post history tracking
  - Auto-refresh every 30 seconds
  - Dark theme, responsive design
- **n8n workflow** updated with AI transformation node and 14 platforms
- **API endpoints**:
  - POST /api/post — cross-post to platforms
  - POST /api/transform — AI content transformation
  - GET /api/status — engine status
  - GET /api/history — post history
  - GET /api/history/export — full history export
  - GET /api/settings — current configuration
  - GET /api/health/platforms — per-platform health

### Changed
- Platform count: 7 → 14
- Webhook URLs: port 5678 → 5679
- Engine: added AI transformation support
- Dashboard: complete redesign with dark theme

### Fixed
- Hardcoded publication host in hashnode.py
- Unused import in base.py
- Test files now use env-based credentials

## v1.0.0 (2026-07-21)

### Added
- Initial release
- 7 platforms: LinkedIn, X, Reddit, Dev.to, Hashnode, Indeed, Naukri
- CLI with check, post, scheduler, status commands
- Webhook server for n8n integration
- Supervisor for 24/7 operation
- Content dedup and state persistence
