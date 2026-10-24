#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -c "import fastapi, c2pa, cv2, pywt" 2>/dev/null || pip install -r requirements.txt
[ -f data/certs/demo_chain.pem ] || python3 tools/dev_cert.py
[ -f demo_assets/ai_generated_signed.jpg ] || python3 tools/make_demo_assets.py
[ -f frontend/build/index.html ] || (cd frontend && npm ci && npm run build)
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" "$@"
