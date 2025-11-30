# Development (hot reload)

Use the development docker-compose to get Django auto-reload when you change code or templates.

```
cd docker
docker compose -f docker-compose.dev.yml up --build
```

The `web` service mounts the repository into `/code` and runs `manage.py runserver` so edits are reflected immediately. The DB container stores its data under `docker/postgres-data-dev`. Stop with `docker compose -f docker-compose.dev.yml down`.
