# Humaniti Class Quality Prototype

The first implementation stage accepts pasted transcript text or a `.txt`/`.vtt` file and shows exact phrase cues with the source segment and, for VTT, its recording timestamp.

This stage does **not** assess teaching quality or assign an overall category or score. Phrase matching is a transparent UI/API placeholder for the later semantic evaluation stage. A phrase match is not proof of effective teaching, and a missing phrase is not proof that a behavior did not occur.

## Run locally

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>.

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
```

## Data handling

The app keeps submitted transcript text in request memory only; it does not persist transcripts or reports. Do not submit identifiable or confidential classroom material to an exposed deployment. This prototype is not yet access-controlled.
