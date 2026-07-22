import json
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, render_template, jsonify, request

sys.path.insert(0, str(Path(__file__).parent.parent))
from adapters.engine import CrossPostEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

CONFIG_PATH = os.getenv("CROSSWIRE_CONFIG", "config/settings.json")

# All 14 platforms with metadata
ALL_PLATFORMS = {
    "linkedin":      {"type": "API",     "icon": "in"},
    "x":             {"type": "API",     "icon": "x"},
    "reddit":        {"type": "API",     "icon": "rd"},
    "devto":         {"type": "API",     "icon": "dt"},
    "hashnode":      {"type": "API",     "icon": "hn"},
    "medium":        {"type": "Browser", "icon": "md"},
    "indeed":        {"type": "Browser", "icon": "id"},
    "naukri":        {"type": "Browser", "icon": "nk"},
    "glassdoor":     {"type": "Browser", "icon": "gd"},
    "ziprecruiter":  {"type": "Browser", "icon": "zr"},
    "shine":         {"type": "Browser", "icon": "sh"},
    "timesjobs":     {"type": "Browser", "icon": "tj"},
    "apna":          {"type": "Browser", "icon": "ap"},
    "iimjobs":       {"type": "Browser", "icon": "ij"},
}

PLATFORM_COLORS = {
    "linkedin": "#0a66c2",
    "x": "#ffffff",
    "reddit": "#ff4500",
    "devto": "#0a0a0a",
    "hashnode": "#2962ff",
    "medium": "#00ab6c",
    "indeed": "#2164f3",
    "naukri": "#4a90d9",
    "glassdoor": "#0caa41",
    "ziprecruiter": "#5ba4d2",
    "shine": "#f7941d",
    "timesjobs": "#e74c3c",
    "apna": "#f58220",
    "iimjobs": "#1a73e8",
}


def get_engine():
    return CrossPostEngine(CONFIG_PATH)


@app.route("/")
def index():
    engine = get_engine()
    status = engine.get_status()
    # Enrich with platform metadata
    platforms = []
    for name in ALL_PLATFORMS:
        meta = ALL_PLATFORMS[name]
        enabled = name in status["targets"]
        # Determine live status from recent posts
        live_status = "idle"  # yellow
        last_posted = None
        for post in reversed(status.get("recent_posts", [])):
            if post.get("target") == name:
                last_posted = post.get("timestamp")
                if post.get("status") == "posted":
                    live_status = "ok"  # green
                elif post.get("status") == "error":
                    live_status = "error"  # red
                break

        platforms.append({
            "name": name,
            "type": meta["type"],
            "icon": meta["icon"],
            "color": PLATFORM_COLORS.get(name, "#00d4ff"),
            "enabled": enabled,
            "live_status": live_status,
            "last_posted": last_posted,
        })

    status["platforms"] = platforms
    return render_template("index.html", status=status)


@app.route("/api/status")
def api_status():
    engine = get_engine()
    status = engine.get_status()

    platforms = []
    for name in ALL_PLATFORMS:
        meta = ALL_PLATFORMS[name]
        enabled = name in status["targets"]
        live_status = "idle"
        last_posted = None
        for post in reversed(status.get("recent_posts", [])):
            if post.get("target") == name:
                last_posted = post.get("timestamp")
                if post.get("status") == "posted":
                    live_status = "ok"
                elif post.get("status") == "error":
                    live_status = "error"
                break
        platforms.append({
            "name": name,
            "type": meta["type"],
            "icon": meta["icon"],
            "color": PLATFORM_COLORS.get(name, "#00d4ff"),
            "enabled": enabled,
            "live_status": live_status,
            "last_posted": last_posted,
        })

    status["platforms"] = platforms
    return jsonify(status)


@app.route("/api/post", methods=["POST"])
def api_post():
    data = request.json or {}
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "Content is required"}), 400

    targets = data.get("targets", [])
    if not targets:
        return jsonify({"error": "Select at least one target platform"}), 400

    dry_run = data.get("dry_run", False)

    engine = get_engine()

    # Override dry_run if explicitly passed
    original_dry_run = engine.dry_run
    if dry_run:
        engine.dry_run = True

    try:
        result = engine.post_directly(
            content=content,
            targets=targets,
            title=data.get("title"),
            url=data.get("url"),
            tags=data.get("tags", []),
            source_platform=data.get("source_platform", "linkedin")
        )
    finally:
        engine.dry_run = original_dry_run

    return jsonify(result)


@app.route("/api/history")
def api_history():
    engine = get_engine()
    history = engine.state.get("post_history", [])
    # Return last 20, most recent first
    return jsonify(history[-20:][::-1])


@app.route("/api/health")
def api_health():
    return jsonify({"status": "healthy", "service": "crosswire-dashboard"})


@app.route("/api/transform", methods=["POST"])
def api_transform():
    data = request.json or {}
    content = data.get("content", "").strip()
    platform = data.get("platform", "linkedin")

    if not content:
        return jsonify({"error": "Content is required"}), 400

    try:
        from adapters.ai_transformer import AITransformer
        transformer = AITransformer()
        result = transformer.transform(
            content=content,
            title=data.get("title", ""),
            platform=platform,
            source_platform=data.get("source_platform", "linkedin")
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e), "content": content, "transformed": False}), 500


@app.route("/api/settings", methods=["GET"])
def api_settings():
    engine = get_engine()
    return jsonify({
        "dry_run": engine.dry_run,
        "ai_enabled": engine.ai_enabled,
        "ai_model": engine.config.get("settings", {}).get("ai_model", "N/A"),
        "ai_provider": engine.config.get("settings", {}).get("ai_provider", "ollama"),
        "timezone": engine.config.get("settings", {}).get("timezone", "UTC"),
        "sources": list(engine.sources.keys()),
        "targets": list(engine.targets.keys())
    })


def run_dashboard(host="0.0.0.0", port=8080):
    logger.info(f"Crosswire Dashboard starting on http://{host}:{port}")
    app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    run_dashboard()
