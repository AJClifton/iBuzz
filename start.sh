#!/bin/bash
. ./venv/bin/activate
gunicorn main:app --bind "127.0.0.1" --access-logfile - --error-logfile - --daemon
nginx -g "daemon off;"