@echo off
setlocal
cd /d %~dp0\..\..

if not exist .venv (
  py -m venv .venv
)

call .venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chrome
uvicorn app.main:app --host 127.0.0.1 --port 8765 --log-level info
