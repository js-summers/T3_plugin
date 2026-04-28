from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import requests
from Bio.SeqUtils.ProtParam import ProteinAnalysis
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, model_validator


UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"
VALID_AMINO_ACIDS = set("ACDEFGHIKLMNPQRSTVWY")


class AnalyzeRequest(BaseModel):
    protein_name: Optional[str] = None
    sequence: Optional[str] = None

    @model_validator(mode="after")
    def check_one_input(self) -> "AnalyzeRequest":
        has_name = bool(self.protein_name and self.protein_name.strip())
        has_sequence = bool(self.sequence and self.sequence.strip())
        if not has_name and not has_sequence:
            raise ValueError("Provide either protein_name or sequence.")
        return self


app = FastAPI(title="Protein Evaluation Demo", version="0.1.0")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


def normalize_sequence(raw_sequence: str) -> str:
    cleaned = "".join(raw_sequence.upper().split())
    invalid = sorted(set(cleaned) - VALID_AMINO_ACIDS)
    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Sequence contains invalid amino acids: {', '.join(invalid)}",
        )
    if not cleaned:
        raise HTTPException(status_code=400, detail="Sequence is empty after cleanup.")
    return cleaned


def fetch_uniprot_sequence(protein_name: str) -> Dict[str, str]:
    params = {
        "query": f"(protein_name:{protein_name}) AND (reviewed:true)",
        "fields": "accession,protein_name,organism_name,sequence",
        "size": 1,
        "format": "json",
    }

    response = requests.get(UNIPROT_SEARCH_URL, params=params, timeout=15)
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail="Failed to query UniProt. Try again later.",
        )

    results = response.json().get("results", [])
    if not results:
        raise HTTPException(
            status_code=404,
            detail="No reviewed UniProt entry found for that protein name.",
        )

    entry = results[0]
    sequence = entry.get("sequence", {}).get("value", "")
    if not sequence:
        raise HTTPException(
            status_code=404,
            detail="UniProt entry found, but sequence was missing.",
        )

    return {
        "accession": entry.get("primaryAccession", "N/A"),
        "entry_name": entry.get("proteinDescription", {})
        .get("recommendedName", {})
        .get("fullName", {})
        .get("value", protein_name),
        "organism": entry.get("organism", {}).get("scientificName", "N/A"),
        "sequence": normalize_sequence(sequence),
    }


def build_protparam_metrics(sequence: str) -> Dict[str, Any]:
    analyzer = ProteinAnalysis(sequence)
    return {
        "length": len(sequence),
        "molecular_weight": round(analyzer.molecular_weight(), 2),
        "isoelectric_point": round(analyzer.isoelectric_point(), 3),
        "gravy": round(analyzer.gravy(), 3),
        "aromaticity": round(analyzer.aromaticity(), 4),
        "instability_index": round(analyzer.instability_index(), 3),
        "amino_acid_composition": {
            aa: round(frac, 4) for aa, frac in analyzer.get_amino_acids_percent().items()
        },
    }


def secretion_prediction_placeholder(sequence: str) -> Dict[str, Any]:
    return {
        "module": "Secretion Prediction (Placeholder)",
        "status": "placeholder",
        "message": "No ML model integrated yet. This is a stub for future secretion scoring.",
        "sequence_length": len(sequence),
    }


def golden_gate_placeholder(sequence: str) -> Dict[str, Any]:
    return {
        "module": "Golden Gate Primer Design (Placeholder)",
        "status": "placeholder",
        "message": "Primer design logic not implemented yet. Add BsaI/BsmBI strategy in next iteration.",
        "sequence_length": len(sequence),
    }


@app.get("/")
def read_index() -> FileResponse:
    return FileResponse(static_dir / "index.html")


@app.get("/demo")
def read_demo() -> FileResponse:
    return FileResponse(static_dir / "demo.html")


@app.post("/analyze")
def analyze_protein(payload: AnalyzeRequest) -> Dict[str, Any]:
    source_info: Dict[str, Any] = {"source": "manual_sequence"}

    if payload.sequence and payload.sequence.strip():
        sequence = normalize_sequence(payload.sequence)
    else:
        uniprot_data = fetch_uniprot_sequence(payload.protein_name.strip())
        sequence = uniprot_data["sequence"]
        source_info = {
            "source": "uniprot",
            "protein_name": payload.protein_name,
            "accession": uniprot_data["accession"],
            "entry_name": uniprot_data["entry_name"],
            "organism": uniprot_data["organism"],
        }

    metrics = build_protparam_metrics(sequence)
    return {
        "input": source_info,
        "sequence": sequence,
        "protparam": metrics,
        "secretion_prediction": secretion_prediction_placeholder(sequence),
        "golden_gate_primer_design": golden_gate_placeholder(sequence),
    }
