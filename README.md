# T3_plugin MVP: Protein Evaluation Demo

A minimal local demo with:
- **FastAPI backend** (`POST /analyze`)
- **Single-page HTML frontend**
- UniProt lookup by protein name
- Biopython ProtParam metrics
- Placeholder modules for secretion prediction and Golden Gate primer design

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --reload
```

Then open:
- http://127.0.0.1:8000

## API Usage

### 1) Analyze by sequence

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"sequence": "MKWVTFISLLFLFSSAYSRGVFRRDTHKSEIAHRFKDLGE"}'
```

### 2) Analyze by protein name (UniProt reviewed top hit)

```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"protein_name": "hemoglobin subunit beta"}'
```

## Notes

- If both `sequence` and `protein_name` are supplied, the backend prioritizes `sequence`.
- Sequence validation allows only standard 20 amino acid letters: `ACDEFGHIKLMNPQRSTVWY`.
- Secretion prediction and Golden Gate primer design are clearly labeled placeholders for future implementation.

## HTML-only Demo

If you want a quick front-end-only demo, open `static/demo.html` directly in your browser.

- **Mock mode** works with no backend and shows demo output cards.
- **Live API mode** calls `POST /analyze` when the FastAPI server is running.
