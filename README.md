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

### TODO
- [ ] Implement `/boxd-info` (see infos about you)
- [x] Implement `/boxd-events` (toggle which events are sent)
- [x] Implement `/boxd-toggle` (toggle orpheus)
- [x] Implement `/boxd-link` (link Letterboxd to Orpheus)