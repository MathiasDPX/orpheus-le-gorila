# Orpheus Le Gorila

Posts Letterboxd entries to personal channels!

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