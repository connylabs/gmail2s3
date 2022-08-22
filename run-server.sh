#!/bin/bash
PORT=${PORT:-8000}
poetry run gunicorn gmail2s3.main:app -b :$PORT --timeout 120 -w 4 --reload -c conf/gunicorn.py
# uvicorn gmail2s3.main:app  --reload
