# Orpheus Le Gorila

Orpheus Le Gorila is a Slack bot that forward your Letterboxd activity to your personal channel

## Commands

- `/boxd-link` Link your Slack account to Letterboxd
- `/boxd-toggle` Toggle Letterboxd logging in this channel
- `/boxd-events` Manage which events are sent
- `/boxd-info` Open a popup showing informations about you
- `/boxd-roll` Pick a random movie among your watchlist

## Installation

docker-compose.yml:
```yaml
services:
  orpheus:
    build: .
    container_name: orpheus-le-gorila
    env_file:
      - .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
```
