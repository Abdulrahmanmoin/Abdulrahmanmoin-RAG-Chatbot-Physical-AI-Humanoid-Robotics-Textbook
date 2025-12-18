
@echo off
echo Starting ingestion... > ingest_bat.log
call .venv\Scripts\activate
echo Activated venv >> ingest_bat.log
python -u simple_ingest.py >> ingest_bat.log 2>&1
echo Done. >> ingest_bat.log
type ingest_bat.log
