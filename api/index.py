"""Vercel entry point.

Vercel's Python runtime looks for a WSGI/ASGI callable named `app` in a file
under `api/`. Everything real lives in `gatewaydashboard/`; this file only puts
that directory on the import path and re-exports the Flask app, so the same
code runs locally (`python gatewaydashboard/app.py`) and hosted, with no
Vercel-specific branches in the application itself.

The one difference between the two environments is handled in config.py:
`VERCEL=1` moves the on-disk cache to /tmp, because the deployment filesystem
is read-only. Durable storage is Supabase's job — see gatewaydashboard/store.py.
"""

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "gatewaydashboard"),
)

from app import app  # noqa: E402,F401  (re-exported for the Vercel runtime)
