# BuddAI Web Frontend

This directory contains the Single Page Application (SPA) for the P.DE.I Framework.

## Architecture

- **Tech Stack**: React 18, TailwindCSS, Babel (Standalone).
- **Delivery**: Served statically by `pdei_core/server.py` at `/web`.
- **Communication**: REST API (`/api/*`) and WebSockets (`/api/ws/chat`).

## Features

- Real-time Chat with Markdown & Code Highlighting.
- System Health Monitoring (CPU/RAM).
- Interactive "Eyes" UI (Mouse Tracking).
- Session Management & Local Storage.
