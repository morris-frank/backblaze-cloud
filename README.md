# BackBlaze-Cloud-Viewer

![Python](https://img.shields.io/badge/Python-3.8.5-blue?logo=python)
![GitHub](https://img.shields.io/github/license/morris-frank/backblaze-cloud)
[![Issues](https://img.shields.io/github/issues/morris-frank/backblaze-cloud)](https://github.com/morris-frank/backblaze-cloud/issues)

This is a little performant web app for browsing and viewing the contents of a B2 buckets. This is a read-only _cloud_ that generates thumbnails (previews) locally and caches the folder content lists to be performant.

This is using:

- [Sanic](https://github.com/huge-success/sanic) as the web-server
- [b2sdk](https://github.com/Backblaze/b2-sdk-python) for the connection to the bucket
- Pillow for image processing

## Installation

Exact dependencies are in the `pyproject.toml`. Best installed with poetry:

```bash
poetry install
```

## Configuration

Copy the `config.example.py` to `config.py` and edit all the variables (should be self explanatory). Authentication right now is done with simple HTTPAuth and one user. The point here is simplicity!

## Running

After installation running the Sanic web-server directly, without middleware is the easiest:

```bash
sanic server.app --host=0.0.0.0 --port=80 --workers=1 --no-access-logs
```

## Screenshots

![A screenshot of the web-app in action.](screenshot.png)