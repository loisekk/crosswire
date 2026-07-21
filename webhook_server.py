#!/usr/bin/env python3
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import threading
from pathlib import Path
from adapters.engine import CrossPostEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/webhook.log")
    ]
)
logger = logging.getLogger(__name__)


class WebhookHandler(BaseHTTPRequestHandler):
    engine = None

    def do_POST(self):
        if self.path == "/webhook/naukri":
            self._handle_crosspost("naukri")
        elif self.path == "/webhook/all":
            self._handle_crosspost("all")
        elif self.path.startswith("/api/crosspost/"):
            platform = self.path.split("/")[-1]
            self._handle_single_platform(platform)
        else:
            self._respond(404, {"error": "Not found"})

    def _handle_crosspost(self, source):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            logger.info(f"Received webhook from {source}: {json.dumps(data)[:200]}")

            post_content = data.get("description", data.get("content", ""))
            post_title = data.get("title", "")
            post_url = data.get("url", "")
            post_image = data.get("image_url")
            post_tags = data.get("tags", [])

            if not post_content and not post_title:
                self._respond(400, {"error": "No content or title provided"})
                return

            targets = ["linkedin", "x", "reddit", "devto", "hashnode", "indeed", "naukri"]
            results = self.engine.post_directly(
                content=post_content or post_title,
                targets=targets,
                title=post_title,
                url=post_url,
                tags=post_tags
            )

            logger.info(f"Cross-post results: {json.dumps(results, default=str)}")
            self._respond(200, {
                "status": "cross-posted",
                "results": results,
                "source": source
            })

        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
        except Exception as e:
            logger.error(f"Webhook error: {e}")
            self._respond(500, {"error": str(e)})

    def _handle_single_platform(self, platform):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body)
            logger.info(f"Posting to {platform}: {json.dumps(data)[:200]}")

            results = self.engine.post_directly(
                content=data.get("content", ""),
                targets=[platform],
                title=data.get("title"),
                url=data.get("url"),
                tags=data.get("tags", [])
            )

            self._respond(200, {
                "status": "posted",
                "platform": platform,
                "result": results.get(platform, {})
            })

        except json.JSONDecodeError:
            self._respond(400, {"error": "Invalid JSON"})
        except Exception as e:
            logger.error(f"Post to {platform} error: {e}")
            self._respond(500, {"error": str(e)})

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {
                "status": "healthy",
                "service": "crosswire-webhook",
                "platforms": list(self.engine.targets.keys()) if self.engine else []
            })
        elif self.path == "/status":
            self._respond(200, {
                "sources": list(self.engine.sources.keys()) if self.engine else [],
                "targets": list(self.engine.targets.keys()) if self.engine else [],
                "dry_run": self.engine.dry_run if self.engine else True
            })
        else:
            self._respond(404, {"error": "Not found"})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        logger.info(f"{self.address_string()} - {format % args}")


def run_server(host="0.0.0.0", port=5679):
    Path("logs").mkdir(exist_ok=True)

    WebhookHandler.engine = CrossPostEngine()
    server = HTTPServer((host, port), WebhookHandler)

    logger.info(f"=== Crosswire Webhook Server ===")
    logger.info(f"Listening on {host}:{port}")
    logger.info(f"Endpoints:")
    logger.info(f"  POST /webhook/naukri    - Naukri webhook trigger")
    logger.info(f"  POST /webhook/all       - Cross-post to all platforms")
    logger.info(f"  POST /api/crosspost/<platform> - Post to specific platform")
    logger.info(f"  GET  /health            - Health check")
    logger.info(f"  GET  /status            - Current status")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
