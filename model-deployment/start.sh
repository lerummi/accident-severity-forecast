#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

/root/.local/bin/gunicorn -w 2 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 app.main:app
