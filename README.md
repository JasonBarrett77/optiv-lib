# optiv-lib

Simplified Python access to vendor APIs for quick automation. The library handles sessions, auth, requests, data transforms, and serialization so you focus on the task instead of the plumbing.

* Python 3.12+
* Stdlib-first design
* PAN-OS support complete; Azure support mostly done

---

## Features

* Unified session management and auth
* Minimal, readable API surface
* Typed models and consistent data formats
* Idempotent “ensure” style helpers
* Works offline in enterprise networks

---

## Install

```bash
# from a local checkout
pip install -U .
# or from a built wheel
pip install dist/optiv_lib-<version>-py3-none-any.whl
```

> Requires Python 3.12+. No extra deps beyond the standard library unless a provider needs them.

---

## Quick Start

### PAN-OS (Panorama) example

```python
from optiv_lib.config import PanoramaConfig, Secret
from optiv_lib.providers.pan.session import PanoramaSession
from optiv_lib.providers.pan.objects.url_category.api import list_url_categories

# Secrets can be sourced lazily (env var, vault, etc.)
cfg = PanoramaConfig(
    hostname="panorama.example.com",
    username="apiuser",
    password=Secret.from_env("PANORAMA_PASSWORD"),
)

with PanoramaSession(cfg) as pano:
    cats = list_url_categories(pano)
    for c in cats:
        print(c.name, c.action)
```

### Azure example (preview)

```python
from optiv_lib.providers.azure.session import AzureSession
from optiv_lib.providers.azure.network.vnets.api import list_vnets

az = AzureSession.from_default()  # uses default credential flow
for vnet in list_vnets(az, subscription_id="<sub-id>"):
    print(vnet.name, vnet.location)
```

---

## Concepts

* **Config**: Small, explicit configuration objects (hostnames, creds, verify).
* **Session**: Reusable, provider-specific HTTP clients.
* **Models**: Typed request/response shapes for safer code.
* **Ensure helpers**: Create/update/no-change flows for idempotence.

---

## Status

* PAN-OS: Production-ready core (objects, policies, commits).
* Azure: Networking coverage in progress; API surface stabilizing.
* Breaking changes may occur before 1.0. Pin versions.

---

## Logging

Structured, human-readable logs by default. Set `OPTIV_LOG=DEBUG` for verbose output.

---

## Testing

```bash
python -m pytest -q
```

Unit tests prefer local doubles over live API calls.

---

## Versioning

Semantic versioning pre-1.0 with care for backward compatibility where possible.

---

## Contributing

Small, focused PRs. Include type hints, docstrings, and a minimal test. Keep APIs simple.

---

## Security

Do not commit secrets. Prefer environment variables or your organization’s secret manager.

---

## License

SPDX: choose an SPDX ID and set `project.license` in `pyproject.toml`.

---

## Minimal Example Script

```python
# examples/list_pan_url_cats.py
from optiv_lib.config import PanoramaConfig, Secret
from optiv_lib.providers.pan.session import PanoramaSession
from optiv_lib.providers.pan.objects.url_category.api import list_url_categories

def main() -> None:
    cfg = PanoramaConfig(
        hostname="panorama.example.com",
        username="apiuser",
        password=Secret.from_env("PANORAMA_PASSWORD"),
    )
    with PanoramaSession(cfg) as pano:
        for c in list_url_categories(pano):
            print(f"{c.name}: {c.action}")

if __name__ == "__main__":
    main()
```

---

## Roadmap (short)

* Azure: fuller coverage for routes, NICs, gateways
* PAN-OS: higher-level policy builders and diffs
* CLI helpers for common tasks

---

## Support

File issues and feature requests in the repository’s tracker.
