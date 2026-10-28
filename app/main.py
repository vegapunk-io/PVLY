"""Provenably. FastAPI application (UI + JSON API).

Run:  uvicorn app.main:app --host 0.0.0.0 --port 8000
Docs: /api/docs (OpenAPI)   Health: /health

Scaling path (see README): the analyzer pipeline is a pure function `pipeline.run_scan(scan_id)`; swap
BackgroundTasks for a queue worker (arq/Celery), SQLite for Postgres, local blobs for S3, routes stay the same.
"""
from __future__ import annotations

import contextvars
import ipaddress
import json
import logging
import mimetypes
import pathlib
import socket
import threading
import time
import uuid
import urllib.parse
import urllib.request
from typing import Optional

from contextlib import asynccontextmanager
from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
from pydantic import BaseModel, Field

from . import config, db, pipeline
from .analyzers import text_an
from . import removal as removal_mod
from .analyzers.c2pa_an import HAVE_SDK as HAVE_C2PA, trust_sources
from .rules import engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("provenably")

_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

# --- lightweight Prometheus-style metrics (stdlib only, no extra dependency) ---
_metrics_lock = threading.Lock()
_metrics: dict[str, int] = {"requests_total": 0, "requests_5xx": 0, "scans_created": 0, "rate_limited": 0}
_request_counts: dict[str, int] = {}  # "METHOD path status" -> count

# --- in-process rate limiter (per client IP, token bucket) ---
_rate_lock = threading.Lock()
_rate_buckets: dict[str, list[float]] = {}


def _check_rate_limit(client_ip: str) -> bool:
    """Return True if allowed, False if rate-limited."""
    if config.RATE_LIMIT_PER_MINUTE <= 0:
        return True
    now = time.time()
    window = 60.0
    with _rate_lock:
        bucket = _rate_buckets.setdefault(client_ip, [])
        # drop entries outside window
        cutoff = now - window
        while bucket and bucket[0] < cutoff:
            bucket.pop(0)
        if len(bucket) >= config.RATE_LIMIT_PER_MINUTE:
            return False
        bucket.append(now)
        return True

BASE = pathlib.Path(__file__).resolve().parent
FRONTEND_DIR = BASE.parent / "frontend" / "build"
@asynccontextmanager
async def _lifespan(app: FastAPI):
    db.init_db()

    def janitor():
        while True:
            time.sleep(600)
            try:
                n = pipeline.cleanup_expired_blobs()
                # also clean expired removal + batch output blobs
                for fn in (db.expired_removal_blobs, db.expired_batch_blobs):
                    for row in fn():
                        p = row.get("output_blob_path")
                        if p:
                            try:
                                pathlib.Path(p).unlink(missing_ok=True)
                            except Exception:
                                pass
                if n:
                    log.info("janitor removed %d expired blobs", n)
            except Exception:
                log.exception("janitor")
    threading.Thread(target=janitor, daemon=True, name="blob-janitor").start()
    yield


app = FastAPI(title="Provenably API", version=config.APP_VERSION, docs_url="/api/docs", redoc_url=None, openapi_url="/api/openapi.json", lifespan=_lifespan)
app.add_middleware(GZipMiddleware, minimum_size=1024)


@app.middleware("http")
async def request_id_and_logging(request: Request, call_next):
    rid = request.headers.get("x-request-id") or uuid.uuid4().hex
    token = _request_id_var.set(rid)
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = rid
        return response
    except Exception:
        status_code = 500
        raise
    finally:
        dur = time.perf_counter() - start
        path = request.url.path
        key = f"{request.method} {path} {status_code}"
        with _metrics_lock:
            _metrics["requests_total"] += 1
            if status_code >= 500:
                _metrics["requests_5xx"] += 1
            _request_counts[key] = _request_counts.get(key, 0) + 1
        log.info("rid=%s method=%s path=%s status=%d dur=%.3fs", rid, request.method, path, status_code, dur)
        _request_id_var.reset(token)


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # Only API calls are limited; page shells and static assets (dozens per page view) are exempt.
    if not request.url.path.startswith("/v1/"):
        return await call_next(request)
    client_ip = request.client.host if request.client else "unknown"
    # X-Forwarded-For is client-controlled; honor it only behind a proxy that overwrites it.
    xff = request.headers.get("x-forwarded-for")
    if xff and config.TRUST_PROXY_HEADERS:
        client_ip = xff.split(",")[0].strip()
    if not _check_rate_limit(client_ip):
        with _metrics_lock:
            _metrics["rate_limited"] += 1
        return JSONResponse({"detail": "You are sending requests too quickly. Wait a minute and try again."},
                            status_code=429, headers={"Retry-After": "60"})
    return await call_next(request)



app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")
templates = Jinja2Templates(directory=BASE / "templates")
templates.env.globals.update(app_name=config.APP_NAME, app_version=config.APP_VERSION)


# ------------------------------------------------------------------------------------------------ helpers
def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    """Auth hook. Enforced when keys are configured OR PROVENABLY_REQUIRE_AUTH is set."""
    if config.API_KEYS:
        if x_api_key not in config.API_KEYS:
            raise HTTPException(401, "invalid or missing X-API-Key")
        return True
    if config.REQUIRE_AUTH:
        raise HTTPException(401, "authentication required (no API keys configured)")
    return True


def _render(request: Request, name: str, **ctx):
    return templates.TemplateResponse(request, name, ctx)


def _frontend_available() -> bool:
    return (FRONTEND_DIR / "index.html").is_file()


def _frontend_response(request: Request, relative_path: str, status_code: int = 200):
    """Serve one SvelteKit static file safely, honoring adapter-static Brotli/Gzip variants."""
    if not FRONTEND_DIR.is_dir():
        return None

    frontend_root = FRONTEND_DIR.resolve()
    target = (frontend_root / relative_path).resolve()
    try:
        target.relative_to(frontend_root)
    except ValueError:
        return None
    if target.is_dir():
        target = target / "index.html"
    if not target.is_file():
        return None

    media_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    relative = target.relative_to(frontend_root).as_posix()
    if relative.startswith("_app/immutable/"):
        cache_control = "public, max-age=31536000, immutable"
    elif target.suffix == ".html":
        cache_control = "no-cache"
    else:
        cache_control = "public, max-age=3600"

    accepted_encodings = set()
    for part in request.headers.get("accept-encoding", "").lower().split(","):
        token, _, params = part.partition(";")
        if params.strip() not in {"q=0", "q=0.0", "q=0.00", "q=0.000"}:
            accepted_encodings.add(token.strip())
    compressed_path = None
    content_encoding = None
    if "br" in accepted_encodings:
        candidate = target.with_suffix(target.suffix + ".br")
        if candidate.is_file():
            compressed_path = candidate
            content_encoding = "br"
    if compressed_path is None and "gzip" in accepted_encodings:
        candidate = target.with_suffix(target.suffix + ".gz")
        if candidate.is_file():
            compressed_path = candidate
            content_encoding = "gzip"

    headers = {
        "Cache-Control": cache_control,
        "Vary": "Accept-Encoding",
        "X-Content-Type-Options": "nosniff",
    }
    if content_encoding:
        headers["Content-Encoding"] = content_encoding
        return FileResponse(compressed_path, media_type=media_type, status_code=status_code, headers=headers)
    return FileResponse(target, media_type=media_type, status_code=status_code, headers=headers)


def _frontend_or_render(request: Request, frontend_path: str, template_name: str, **ctx):
    if _frontend_available():
        response = _frontend_response(request, frontend_path)
        if response is not None:
            return response
    return _render(request, template_name, **ctx)


def _redirect_with_query(request: Request, path: str, template_name: str, **ctx):
    if not _frontend_available():
        return _render(request, template_name, **ctx)
    suffix = f"?{request.url.query}" if request.url.query else ""
    return RedirectResponse(f"{path}{suffix}", status_code=307)


def _fmt_ts(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(ts)) if ts else ""


templates.env.filters["ts"] = _fmt_ts
templates.env.filters["kb"] = lambda n: f"{(n or 0) / 1024:.0f} KB" if (n or 0) < 1024 * 1024 else f"{(n or 0) / 1024 / 1024:.1f} MB"


def _safe_fetch(url: str) -> tuple[bytes, str]:
    """Fetch a public URL with an SSRF guard (no private/loopback/link-local targets, http(s) only, size cap)."""
    u = urllib.parse.urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise HTTPException(400, "only http(s) URLs are allowed")
    try:
        infos = socket.getaddrinfo(u.hostname, u.port or (443 if u.scheme == "https" else 80), proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise HTTPException(400, "hostname does not resolve")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            raise HTTPException(400, "URL resolves to a non-public address")
    req = urllib.request.Request(url, headers={"User-Agent": f"{config.APP_NAME}/{config.APP_VERSION} (+provenance scanner)"})
    with urllib.request.urlopen(req, timeout=config.URL_FETCH_TIMEOUT) as r:  # nosec - guarded above
        data = r.read(config.MAX_UPLOAD_MB * 1024 * 1024 + 1)
    if len(data) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, "remote file too large")
    name = pathlib.Path(u.path).name or "download"
    return data, name


def _run_bg(scan_id: str, options: dict | None = None):
    try:
        pipeline.run_scan(scan_id, options)
    except Exception as e:
        log.exception("scan %s failed", scan_id)
        db.set_status(scan_id, "error", str(e)[:500])


# ------------------------------------------------------------------------------------------------ UI routes
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return _frontend_or_render(request, "index.html", "scan.html", recent=db.list_scans(8))


@app.get("/scan", response_class=HTMLResponse)
def scan_page(request: Request):
    return _frontend_or_render(request, "scan.html", "scan.html", recent=db.list_scans(8))


@app.get("/report/{scan_id}", response_class=HTMLResponse)
def report_page(request: Request, scan_id: str):
    if _frontend_available():
        return _frontend_response(request, "200.html")
    row = db.get_scan(scan_id)
    if not row:
        raise HTTPException(404)
    report = json.loads(row["report_json"]) if row.get("report_json") else None
    return _render(request, "report.html", scan=row, report=report)


@app.get("/registry", response_class=HTMLResponse)
def registry_page(request: Request, modality: str = ""):
    if _frontend_available():
        return _frontend_response(request, "registry.html")
    entries = [e for e in engine.REGISTRY if not modality or e["modality"] == modality]
    return _render(request, "registry.html", entries=entries, modality=modality, meta=engine.REGISTRY_META)


@app.get("/registry/{slug}", response_class=HTMLResponse)
def registry_item(request: Request, slug: str):
    if _frontend_available():
        return _frontend_response(request, "200.html")
    e = engine.registry_entry(slug)
    if not e:
        raise HTTPException(404)
    return _render(request, "registry_item.html", e=e)


@app.get("/laws", response_class=HTMLResponse)
def laws_page(request: Request):
    return _redirect_with_query(
        request, "/rules", "laws.html", jurisdictions=engine.JURISDICTIONS, platforms=engine.PLATFORMS
    )


@app.get("/tools", response_class=HTMLResponse)
def tools_page(request: Request):
    return _frontend_or_render(request, "tools.html", "tools.html")


@app.get("/lab", response_class=HTMLResponse)
def lab_page(request: Request):
    return _frontend_or_render(request, "lab.html", "lab.html")


@app.get("/docs-guide", response_class=HTMLResponse)
def docs_page(request: Request):
    return _redirect_with_query(request, "/api", "docs.html", caps=capabilities())


@app.get("/demo", response_class=HTMLResponse)
def demo_page(request: Request):
    if _frontend_available():
        return RedirectResponse("/scan?tab=demo", status_code=307)
    return _render(request, "demo.html", demo_files=_demo_files())


# ------------------------------------------------------------------------------------------------ API: scans
@app.post("/v1/scans", dependencies=[Depends(require_api_key)])
async def create_scan(background: BackgroundTasks, request: Request,
                      file: UploadFile | None = File(default=None), text: str | None = Form(default=None),
                      url: str | None = Form(default=None), hash_only: bool = Form(default=config.HASH_ONLY_DEFAULT),
                      greenlist_key: str | None = Form(default=None), wait: bool = Form(default=False)):
    """Create a scan from exactly one of: multipart `file`, `text`, or `url`. Returns scan id; poll GET /v1/scans/{id}."""
    options = {}
    if greenlist_key:
        options["greenlist_key"] = greenlist_key
    if file is not None and file.filename:
        # Stream in chunks to avoid reading huge uploads fully into memory.
        max_bytes = config.MAX_UPLOAD_MB * 1024 * 1024
        chunks = []
        total = 0
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise HTTPException(413, f"file exceeds {config.MAX_UPLOAD_MB} MB")
            chunks.append(chunk)
        data = b"".join(chunks)
        if not data:
            raise HTTPException(400, "empty file")
        scan_id = pipeline.new_scan_from_bytes(data, file.filename, hash_only=hash_only)
    elif text and text.strip():
        scan_id = pipeline.new_scan_from_text(text)
    elif url and url.strip():
        data, name = _safe_fetch(url.strip())
        scan_id = pipeline.new_scan_from_bytes(data, name, hash_only=hash_only)
    else:
        raise HTTPException(400, "provide one of: file, text, url")
    with _metrics_lock:
        _metrics["scans_created"] += 1
    if wait:
        await run_in_threadpool(_run_bg, scan_id, options)
        row = db.get_scan(scan_id)
        return JSONResponse(json.loads(row["report_json"]) if row.get("report_json") else {"id": scan_id, "status": row["status"], "error": row["error"]})
    background.add_task(_run_bg, scan_id, options)
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return RedirectResponse(f"/report/{scan_id}", status_code=303)
    return {"id": scan_id, "status": "queued", "report_url": f"/v1/scans/{scan_id}", "html_url": f"/report/{scan_id}"}


@app.get("/v1/demo-files")
def demo_files_api():
    return {"files": _demo_files()}


@app.get("/v1/scans", dependencies=[Depends(require_api_key)])
def list_scans(limit: int = 25):
    return {"scans": db.list_scans(min(limit, 200))}


@app.get("/v1/scans/{scan_id}", dependencies=[Depends(require_api_key)])
def get_scan(scan_id: str):
    row = db.get_scan(scan_id)
    if not row:
        raise HTTPException(404)
    out = {k: row[k] for k in ("id", "status", "modality", "filename", "mime", "size", "sha256", "created_at", "updated_at", "error")}
    if row.get("report_json"):
        out["report"] = json.loads(row["report_json"])
    return out


@app.get("/v1/scans/{scan_id}/report.json", dependencies=[Depends(require_api_key)])
def get_report_json(scan_id: str):
    row = db.get_scan(scan_id)
    if not row or not row.get("report_json"):
        raise HTTPException(404, "report not ready")
    return JSONResponse(json.loads(row["report_json"]), headers={"Content-Disposition": f'attachment; filename="provenably-{scan_id}.json"'})


@app.post("/v1/scans/demo/{name}")
async def scan_demo(name: str, background: BackgroundTasks, request: Request, wait: bool = False):
    """Scan one of the bundled demo fixtures (no upload needed)."""
    p = (config.DEMO_DIR / pathlib.Path(name).name)
    if not p.is_file() or p.parent != config.DEMO_DIR:
        raise HTTPException(404, "unknown demo asset")
    options = {"greenlist_key": "demo-key"} if name.startswith("text_greenlist") else {}
    scan_id = pipeline.new_scan_from_bytes(p.read_bytes(), p.name)
    if wait:
        await run_in_threadpool(_run_bg, scan_id, options)
        return json.loads(db.get_scan(scan_id)["report_json"])
    background.add_task(_run_bg, scan_id, options)
    accept = request.headers.get("accept", "")
    if "text/html" in accept and "application/json" not in accept:
        return RedirectResponse(f"/report/{scan_id}", status_code=303)
    return {"id": scan_id, "status": "queued", "html_url": f"/report/{scan_id}"}


@app.post("/v1/remove", dependencies=[Depends(require_api_key)])
def remove_endpoint(scan_id: str, attested: bool = False, background: BackgroundTasks = None):
    """Layer-1 removal with re-scan verification. Requires attested=true (Layer-2 disclaimer acceptance)."""
    if not attested:
        raise HTTPException(400, "attested=true required (accept the Layer-2 disclaimer)")
    try:
        result = removal_mod.remove_layer1(scan_id, attested=True)
    except removal_mod.RemovalError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        log.exception("removal %s failed", scan_id)
        raise HTTPException(500, str(e)[:300])
    return {
        "removal_id": result.removal_id,
        "scan_id": result.scan_id,
        "status": result.status,
        "modality": result.modality,
        "input_sha256": result.input_sha256,
        "output_sha256": result.output_sha256,
        "fields_removed": result.fields_removed,
        "output_download_url": result.output_download_url,
        "verdict": result.verdict,
        "before": result.before,
        "after": result.after,
        "layer2_disclaimer": result.layer2_disclaimer,
    }


@app.get("/v1/removals/{removal_id}", dependencies=[Depends(require_api_key)])
def get_removal(removal_id: str):
    row = db.get_removal(removal_id)
    if not row:
        raise HTTPException(404)
    out = {k: row[k] for k in ("id", "scan_id", "status", "modality", "input_sha256",
                               "output_sha256", "fields_removed", "error", "created_at", "updated_at")}
    if row.get("report_json"):
        out["report"] = json.loads(row["report_json"])
    return out


@app.get("/v1/removals/{removal_id}/download", dependencies=[Depends(require_api_key)])
def download_removal(removal_id: str):
    row = db.get_removal(removal_id)
    if not row or not row.get("output_blob_path"):
        raise HTTPException(404)
    p = pathlib.Path(row["output_blob_path"])
    if not p.exists():
        raise HTTPException(404, "output expired")
    return FileResponse(p, filename=f"cleaned-{removal_id}{p.suffix}")


class BatchIn(BaseModel):
    scan_ids: list[str] = Field(min_length=1)
    preset: str = "generic"
    attested: bool = False


@app.post("/v1/batches", dependencies=[Depends(require_api_key)])
def create_batch_endpoint(body: BatchIn, background: BackgroundTasks):
    if not body.attested:
        raise HTTPException(400, "attested=true required (accept the Layer-2 disclaimer)")
    # validate scans exist
    for sid in body.scan_ids:
        if not db.get_scan(sid):
            raise HTTPException(404, f"scan not found: {sid}")
    batch_id = uuid.uuid4().hex
    db.create_batch(batch_id, body.scan_ids, body.preset, body.attested)
    background.add_task(removal_mod.run_batch, batch_id, body.scan_ids, body.preset, body.attested)
    return {"batch_id": batch_id, "status": "queued", "download_url": f"/v1/batches/{batch_id}/download"}


@app.get("/v1/batches/{batch_id}", dependencies=[Depends(require_api_key)])
def get_batch(batch_id: str):
    row = db.get_batch(batch_id)
    if not row:
        raise HTTPException(404)
    out = {k: row[k] for k in ("id", "status", "preset", "attested", "scan_ids", "removal_ids", "error", "created_at", "updated_at")}
    if row.get("report_json"):
        out["report"] = json.loads(row["report_json"])
    return out


@app.get("/v1/batches/{batch_id}/download", dependencies=[Depends(require_api_key)])
def download_batch(batch_id: str):
    row = db.get_batch(batch_id)
    if not row or not row.get("output_blob_path"):
        raise HTTPException(404, "not ready")
    p = pathlib.Path(row["output_blob_path"])
    if not p.exists():
        raise HTTPException(404, "output expired")
    return FileResponse(p, filename=f"batch-{batch_id}.zip")


@app.get("/v1/scans/{scan_id}/preview.jpg")
def scan_preview(scan_id: str):
    """Downscaled preview of an image scan while its bytes are still retained (never for hash-only scans)."""
    row = db.get_scan(scan_id)
    if not row or row["modality"] != "image" or not row.get("blob_path") or not pathlib.Path(row["blob_path"]).exists():
        raise HTTPException(404)
    from io import BytesIO
    from PIL import Image
    try:
        im = Image.open(row["blob_path"])
        im.thumbnail((640, 640))
        buf = BytesIO()
        im.convert("RGB").save(buf, "JPEG", quality=80)
    except Exception:
        raise HTTPException(415, "cannot render preview")
    from fastapi.responses import Response
    return Response(buf.getvalue(), media_type="image/jpeg", headers={"Cache-Control": "private, max-age=600"})


@app.get("/demo-assets/{name}")
def demo_asset(name: str):
    p = config.DEMO_DIR / pathlib.Path(name).name
    if not p.is_file():
        raise HTTPException(404)
    return FileResponse(p)


# ------------------------------------------------------------------------------------------------ API: rules & registry
@app.get("/v1/registry")
def registry_api(modality: str = ""):
    return {"meta": engine.REGISTRY_META, "entries": [e for e in engine.REGISTRY if not modality or e["modality"] == modality]}


@app.get("/v1/registry/{slug}")
def registry_item_api(slug: str):
    e = engine.registry_entry(slug)
    if not e:
        raise HTTPException(404)
    return e


@app.get("/v1/rules/platforms")
def platforms_api():
    return {"platforms": engine.PLATFORMS}


@app.get("/v1/rules/jurisdictions")
def jurisdictions_api():
    return {"jurisdictions": engine.JURISDICTIONS}


class DisclosureIn(BaseModel):
    content_type: str = Field(pattern="^(image|video|audio|text)$")
    is_ai_generated: bool = False
    is_ai_edited: bool = False
    depicts_real_person: bool = False
    public_interest_text: bool = False
    human_reviewed: bool = False
    artistic: bool = False
    has_c2pa: bool = False
    has_visible_label: bool = False
    has_metadata_id: bool = False
    jurisdictions: list[str] | None = None


@app.post("/v1/disclosure/check")
def disclosure_api(body: DisclosureIn):
    return engine.disclosure_check(**body.model_dump())


class PlatformPreviewIn(BaseModel):
    scan_id: str | None = None
    facts: dict | None = None
    self_disclosure: bool = False


@app.post("/v1/platforms/preview")
def platform_preview_api(body: PlatformPreviewIn):
    facts = body.facts or {}
    if body.scan_id:
        row = db.get_scan(body.scan_id)
        if not row or not row.get("report_json"):
            raise HTTPException(404, "report not ready")
        facts = engine.facts_from_report(json.loads(row["report_json"]))
    return {"facts": facts, "preview": engine.platform_preview(facts, body.self_disclosure)}


# ------------------------------------------------------------------------------------------------ API: text tools & lab
class TextIn(BaseModel):
    text: str = Field(min_length=1, max_length=2_000_000)
    keep_joiners: bool = True
    ascii_dashes: bool = False


@app.post("/v1/text/unicode")
def unicode_api(body: TextIn):
    scan = text_an.scan_unicode(body.text)
    cleaned = text_an.clean_unicode(body.text, keep_joiners=body.keep_joiners, ascii_dashes=body.ascii_dashes)
    return {"scan": scan, "cleaned": cleaned, "changed": cleaned != body.text}


class GreenlistIn(BaseModel):
    action: str = Field(pattern="^(generate|detect)$")
    key: str = "demo-key"
    gamma: float = 0.5
    strength: float = 0.9
    n: int = 300
    text: str | None = None


@app.post("/v1/lab/greenlist")
def greenlist_api(body: GreenlistIn):
    if body.action == "generate":
        toks = text_an.greenlist_generate(body.key, n=min(body.n, 2000), gamma=body.gamma, strength=body.strength)
        return {"text": " ".join(toks[1:]), "stats": text_an.greenlist_zscore(toks, body.key, body.gamma)}
    toks = ["<s>"] + (body.text or "").split()
    return {"stats": text_an.greenlist_zscore(toks, body.key, body.gamma)}


# ------------------------------------------------------------------------------------------------ API: meta
def capabilities() -> dict:
    """What is live vs. manual in this deployment, surfaced in the UI and API so nobody over-trusts a 'clean' result."""
    def _try(mod):
        try:
            __import__(mod)
            return True
        except Exception:
            return False
    return {
        "live": {
            "c2pa_validation": HAVE_C2PA,
            "c2pa_trust_sources": trust_sources(),
            "metadata_forensics": True,
            "open_watermark_dwtdct": _try("pywt") and _try("cv2"),
            "image_forensic_context": True,
            "audio_container_spectral": True,
            "video_bmff_and_frame_sampling": _try("cv2"),
            "text_unicode_hygiene": True,
            "text_stylometry_heuristic": True,
            "text_greenlist_lab": True,
            "platform_label_preview": True,
            "disclosure_checklist": True,
            "registry": len(engine.REGISTRY),
        },
        "manual_integration": {
            "openai_verify_connector": bool(config.OPENAI_VERIFY_ENDPOINT and config.OPENAI_VERIFY_API_KEY),
            "google_synthid_connector": bool(config.GOOGLE_SYNTHID_ENDPOINT and config.GOOGLE_ACCESS_TOKEN),
            "official_c2pa_trust_list": config.TRUST_ANCHORS_PEM.exists(),
            "audioseal_torch": _try("audioseal"),
            "videoseal_torch": _try("videoseal"),
            "trustmark_torch": _try("trustmark"),
            "stable_signature_torch": False,
            "passive_image_classifier_gpu": False,
            "zero_shot_text_detector_gpu": False,
            "ffmpeg_audio_demux": False,
            "auth_and_billing": bool(config.API_KEYS),
            "production_signing_cert_tsa_kms": False,
        },
    }


@app.get("/v1/capabilities")
def capabilities_api():
    return capabilities()


@app.get("/health")
def health():
    return {"ok": True, "version": config.APP_VERSION, **db.stats()}


@app.get("/metrics", include_in_schema=False)
def metrics():
    """Prometheus text exposition (no external dependency)."""
    lines = []
    with _metrics_lock:
        for k in ("requests_total", "requests_5xx", "scans_created"):
            lines.append(f"provenably_{k} {_metrics[k]}")
        for key, val in sorted(_request_counts.items()):
            method, path, status = key.split(" ", 2)
            lines.append(f'provenably_request_count{{method="{method}",path="{path}",status="{status}"}} {val}')
    try:
        stats = db.stats()
        for k, v in stats.items():
            lines.append(f"provenably_db_{k} {v}")
    except Exception:
        pass
    return Response("\n".join(lines) + "\n", media_type="text/plain; version=0.0.4")


def _demo_files() -> list[dict]:
    desc = {
        "ai_generated_signed.jpg": ("image", "Valid Content Credential declaring trainedAlgorithmicMedia (demo signer)."),
        "camera_capture_signed.jpg": ("image", "Valid Content Credential declaring digitalCapture + camera EXIF."),
        "ai_edited_composite_signed.jpg": ("image", "Composite with ingredient chain: camera parent + generative edit."),
        "ai_generated_tampered.jpg": ("image", "Pixels edited after signing; manifest spliced back → hash mismatch."),
        "ai_generated_stripped.jpg": ("image", "Same AI image with all metadata removed (what a screenshot leaves)."),
        "iptc_ai_tagged_no_c2pa.jpg": ("image", "Only unsigned IPTC DigitalSourceType, which can be edited either way."),
        "a1111_parameters.png": ("image", "Automatic1111-style 'parameters' PNG text chunk with prompt + model."),
        "sdxl_watermarked.png": ("image", "SDXL 48-bit DWT-DCT invisible watermark, pristine PNG."),
        "sdxl_watermarked_q75.jpg": ("image", "Same file re-saved as JPEG q75; chroma subsampling destroys the mark."),
        "plain_photo_like.jpg": ("image", "No metadata, no marks, no credential."),
        "text_clean.txt": ("text", "Ordinary meeting minutes."),
        "text_hidden_chars.txt": ("text", "Zero-width spaces, soft hyphen, NNBSP, Cyrillic homoglyph, LRM."),
        "text_greenlist_marked.txt": ("text", "Toy green-list watermark (key 'demo-key'), detectable with that key."),
        "speech_like_signed.wav": ("audio", "Synthetic speech-like WAV with Content Credential (RIFF C2PA chunk)."),
        "speech_like_plain.wav": ("audio", "Same kind of audio, no credential."),
        "clip_signed.mp4": ("video", "MP4 with Content Credential (BMFF hash) + per-frame scan."),
        "clip_plain.mp4": ("video", "Same clip, no credential."),
    }
    out = []
    for name, (mod, d) in desc.items():
        p = config.DEMO_DIR / name
        if p.exists():
            out.append({"name": name, "modality": mod, "desc": d, "size": p.stat().st_size})
    return out


# ------------------------------------------------------------------------------------------------ Svelte frontend
@app.api_route("/v1/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"], include_in_schema=False)
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"], include_in_schema=False)
def api_not_found(path: str):
    return JSONResponse({"detail": "Not Found"}, status_code=404)


@app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
def frontend_fallback(request: Request, full_path: str):
    """Serve SvelteKit assets/routes after every API route has had first claim.

    Unknown API paths deliberately remain JSON 404s; unknown browser paths receive the
    Svelte error shell with HTTP 404. Dynamic report/registry routes receive the static
    200 fallback and resolve their own API state in the browser.
    """
    reserved_prefixes = ("v1/", "api/", "demo-assets/", "static/", "health")
    if full_path.startswith(reserved_prefixes) or not _frontend_available():
        raise HTTPException(404, "not found")

    for candidate in (full_path, f"{full_path}.html", f"{full_path}/index.html"):
        response = _frontend_response(request, candidate)
        if response is not None:
            return response

    if full_path.startswith(("report/", "registry/")):
        response = _frontend_response(request, "200.html")
        if response is not None:
            return response

    if pathlib.PurePosixPath(full_path).suffix:
        raise HTTPException(404, "not found")

    response = _frontend_response(request, "200.html", status_code=404)
    if response is not None:
        return response
    raise HTTPException(404, "not found")
