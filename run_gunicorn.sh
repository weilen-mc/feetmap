#!/usr/bin/env bash

/home/weilenmc/Documents/feetmap/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 feetmap.wsgi:application
