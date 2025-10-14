# 🚀 optiv-lib

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

Choose one of the following.

### From GitHub tag (recommended)
```bash
pip install --no-cache-dir "git+https://github.com/<org>/optiv-lib@v<version>"
```

### From a GitHub Release wheel

```bash
pip install --no-cache-dir "https://github.com/<org>/optiv-lib/releases/download/v<version>/optiv_lib-<version>-py3-none-any.whl"
```

> Requires Python 3.12+. Provider submodules (Azure, PAN-OS) pull any needed deps.

---

## Quick Start

### PAN-OS (Panorama)

```python
from optiv_lib.config import PanoramaConfig, Secret
from optiv_lib.providers.pan.session import PanoramaSession
from optiv_lib.providers.pan.objects.url_category.api import list_url_categories

cfg = PanoramaConfig(
    hostname="panorama.example.com",
    username="apiuser",
    password=Secret.from_env("PANORAMA_PASSWORD"),
)

with PanoramaSession(cfg) as pano:
    for c in list_url_categories(pano):
        print(c.name, c.action)
```

### Azure (preview)

```python
from optiv_lib.providers.azure.session import AzureSession
from optiv_lib.providers.azure.network.vnets.api import list_vnets

az = AzureSession.from_default()
for vnet in list_vnets(az, subscription_id="<sub-id>"):
    print(vnet.name, vnet.location)
```

---

## Concepts

* **Config** – explicit configuration objects
* **Session** – reusable provider HTTP clients
* **Models** – typed request/response shapes
* **Ensure helpers** – idempotent create/update/no-change

---

## Status

* PAN-OS: Production-ready core (objects, policies, commits)
* Azure: Networking coverage in progress
* <1.0 may change APIs. Pin versions.

---

## Logging

Structured logs by default. Set `OPTIV_LOG=DEBUG` for verbose output.

---

## Testing

```bash
python -m pytest -q
```

---

# 🧪 Development and Editable Installs

This section is for contributors and internal builds.

### What is “editable”?

An **editable install** (`pip install -e .`) links your working copy into the environment instead of copying built files. Changes to source take effect immediately without reinstalling. Use it only for local development, not for production use.

#### Editable install (local dev)

```bash
pip install -U pip
pip install -e .
```

#### Uninstall editable

```bash
pip uninstall -y optiv-lib
```

### Build and Publish (GitHub releases)

1. **Bump version**

```bash
# pyproject.toml
version = "<version>"
```

2. **Commit and tag**

```bash
git add -A
git commit -m "v<version>"
git tag v<version>
git push origin main --tags
```

3. **Build artifacts**

```bash
rm -rf dist build *.egg-info
python -m pip install -U build
python -m build
# dist/optiv_lib-<version>-py3-none-any.whl
```

4. **Create GitHub Release and attach files**

* GitHub → Releases → Draft new release → choose tag `v<version>`
* Upload:

  * `dist/optiv_lib-<version>-py3-none-any.whl`
  * (optional) `dist/optiv-lib-<version>.tar.gz`
* Publish

**Resulting install URL:**

```
https://github.com/<org>/optiv-lib/releases/download/v<version>/optiv_lib-<version>-py3-none-any.whl
```

### Force reinstall during testing

```bash
pip install --no-cache-dir --force-reinstall "git+https://github.com/<org>/optiv-lib@v<version>"
```

---

## Contributing

Small, focused PRs with type hints, docstrings, and minimal tests. Keep APIs simple.

---

## Security

Do not commit secrets. Use environment variables or your org’s secret manager.

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

* Azure: routes, NICs, gateways
* PAN-OS: higher-level policy builders and diffs
* CLI helpers for common tasks

---

## Support

Open issues and feature requests in the repo tracker.

```

Source sections preserved and reorganized from your original README (Install, Quick Start, Concepts, Status). :contentReference[oaicite:0]{index=0} :contentReference[oaicite:1]{index=1} :contentReference[oaicite:2]{index=2}
```
