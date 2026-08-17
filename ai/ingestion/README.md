# Ingestion module (Person 1)

Turns raw PDF datasheets and images into `SourceChunk` objects — the shared
contract the rest of the pipeline is built against.

## Setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Files

| File | What it does |
|---|---|
| `schemas.py` | The shared data contract — `SourceChunk`, `SourceRef`, `IdentityMatchProposal`. **Push this first.** Person 2 builds extraction against this shape without needing your other code. |
| `pdf_parser.py` | Parses a PDF into text + table chunks, page-indexed. Run directly: `python pdf_parser.py sample.pdf` |
| `source_quality.py` | Flags a document `clean` vs `low_legibility`. |
| `identity_resolver.py` | Proposes whether two documents describe the same product. Run directly: `python identity_resolver.py` for a sanity check. |

## Output contract (what Person 2 can rely on)

Every chunk your module produces looks like this:

```json
{
  "chunk_id": "doc1_c3",
  "text": "Rated voltage: 415V",
  "source_ref": { "doc_id": "doc1", "source_type": "pdf", "page": 2, "paragraph": 1 },
  "source_quality": "clean",
  "chunk_type": "text"
}
```

Person 2's Extraction Agent reads a list of these and produces field values with
citations back to `chunk_id` / `source_ref`.

## Testing without anyone else's code

```bash
# put a sample datasheet in data/samples/, then:
python pdf_parser.py ../../data/samples/your_datasheet.pdf
```

You should see extracted chunks printed with page numbers. No backend, no
frontend, no Person 2 or 3 code required to verify this works.

## Status

All core pieces are built and tested:
- [x] PDF parsing with page/paragraph indexing, table noise filtered
- [x] Image ingestion (quality check + base64 encoding), ready for Person 2's vision-based reading
- [x] Source quality flagging (clean vs low_legibility)
- [x] Identity resolution with match proposals exported to JSON for Person 3's review UI
- [x] Tested against multiple real manufacturer datasheets

Sample output is available in `data/samples/` and `data/processed/identity_proposals.json`.