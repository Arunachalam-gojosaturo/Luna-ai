# LUNA OS X - Agent System Report

## Deployed Agents
All agents are deployed as modular microservices within the FastAPI router namespace `/api/agents/*`.

* **System Agent (`/api/luna/execute`)**: Connects to Arch Linux root processes using `asyncio.subprocess`. Safely executes sys-commands and monitors system telemetry using `psutil`.
* **Browser Agent (`/api/agents/browser`)**: Handles internet research, HTML DOM extraction, and URL navigation.
* **File Agent (`/api/agents/file`)**: Reads, writes, modifies, and indexes the local file system.
* **Terminal Agent (`/api/agents/terminal`)**: Sandboxed CLI execution environment.
* **GitHub Agent**: Manages `git` processes and source control workflows.
* **Device Agent**: Cross-platform telemetry ingestion.

## Function Calling
The AI Brain autonomously invokes these agents based on contextual intent.
