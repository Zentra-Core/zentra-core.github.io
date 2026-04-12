import subprocess
import json
import os
from flask import request, jsonify

def init_mcp_explore_routes(app, cfg_mgr, logger):
    @app.route("/api/mcp/explore", methods=["GET"])
    def explore_mcp_servers():
        """
        Searches the Smithery.ai registry using npx @smithery/cli.
        Usage: /api/mcp/explore?q=term
        """
        query = request.args.get("q", "").strip()
        if not query:
            return jsonify({"ok": True, "results": []})

        try:
            logger.info(f"[MCP-EXPLORE] Searching Smithery for: '{query}'")
            
            # Use npx --yes to avoid interactive prompts
            # We map 'npx' to 'npx.cmd' on Windows for compatibility
            npx_cmd = "npx.cmd" if os.name == "nt" else "npx"
            
            # Execute search
            result = subprocess.run(
                [npx_cmd, "-y", "@smithery/cli", "mcp", "search", query],
                capture_output=True,
                text=True,
                check=False,
                encoding='utf-8',
                timeout=15  # Limit execution time
            )

            if result.returncode != 0:
                logger.error(f"[MCP-EXPLORE] Smithery CLI error: {result.stderr}")
                return jsonify({"ok": False, "error": "Search failed or timed out."}), 500

            # Parse NDJSON output
            results = []
            for line in result.stdout.strip().split("\n"):
                if not line.strip(): continue
                try:
                    data = json.loads(line)
                    results.append(data)
                except json.JSONDecodeError:
                    continue

            logger.info(f"[MCP-EXPLORE] Found {len(results)} results for '{query}'")
            return jsonify({"ok": True, "results": results})

        except subprocess.TimeoutExpired:
            return jsonify({"ok": False, "error": "Search timed out. Please try again."}), 504
        except Exception as e:
            logger.error(f"[MCP-EXPLORE] Critical error: {e}")
            return jsonify({"ok": False, "error": str(e)}), 500
