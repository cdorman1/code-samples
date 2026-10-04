# Running a service as a locked down local unit behind a reverse proxy

The pattern used for every service in these samples. The application binds to
loopback only and is never reachable directly, secrets live in an environment
file the unit reads at start, and the reverse proxy owns TLS and the public
routing. The unit runs the prebuilt virtual environment explicitly rather than
activating a shell.

Hostnames, ports and paths below are placeholders.

## The unit

```ini
[Unit]
Description=Internal API service
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/service
EnvironmentFile=/etc/service.env
ExecStart=/opt/service/.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8788
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## The route

```yaml
http:
  routers:
    service:
      rule: Host(`example.com`) && PathPrefix(`/service`)
      priority: 1000
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
      middlewares:
        - service-strip-prefix
      service: service

    service-api:
      rule: Host(`example.com`) && PathPrefix(`/api/service`)
      priority: 1001
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt
      service: service

  middlewares:
    service-strip-prefix:
      stripPrefix:
        prefixes:
          - /service

  services:
    service:
      loadBalancer:
        servers:
          - url: http://127.0.0.1:8788
```

Notes that matter in practice:

- The API route has a higher priority than the UI route so a path like
  `/api/service` is not swallowed by the broader prefix.
- `EnvironmentFile` keeps credentials out of the unit file and out of the repo.
- Binding to `127.0.0.1` means a firewall mistake cannot expose the service.
- Only the reverse proxy terminates TLS, so certificates are managed in one place.
