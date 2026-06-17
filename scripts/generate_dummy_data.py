"""
Generates anonymized dummy data for development and testing.
Usage: python scripts/generate_dummy_data.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "encuestas-docentes"))

import pyarrow.parquet as pq

RUTA_SOURCE = Path.home() / "encuestas-docentes/processed"
OUT = Path(__file__).parent.parent / "data/comments_dummy.json"

QUESTION_MAP = {
    "OBS_PROFESOR": "TEACHER_COMMENT",
    "OBS_CURSO": "COURSE_COMMENT",
    "P10": "LEARNING",
    "P15": "FEEDBACK",
    "P16": "RECOMMENDATION",
}


def main():
    ruta_fact = RUTA_SOURCE / "fact_respuesta_texto.parquet"
    ruta_pregs = RUTA_SOURCE / "dim_pregunta.parquet"

    if not ruta_fact.exists():
        print(f"ERROR: source not found at {ruta_fact}")
        sys.exit(1)

    fact = pq.read_table(ruta_fact, columns=["texto", "id_pregunta"]).to_pandas()
    pregs = pq.read_table(
        ruta_pregs, columns=["id_pregunta", "cod_canonico"]
    ).to_pandas()

    df = fact.merge(pregs, on="id_pregunta", how="left")
    df = df[df["texto"].str.len() > 20].dropna(subset=["texto"])
    df = df.sample(min(300, len(df)), random_state=42).reset_index(drop=True)

    comments = [
        {
            "text": row["texto"],
            "question_code": QUESTION_MAP.get(
                str(row.get("cod_canonico", "")), "COURSE_COMMENT"
            ),
        }
        for _, row in df.iterrows()
    ]

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump({"comments": comments}, f, ensure_ascii=False, indent=2)

    print(f"Generated {len(comments)} dummy comments → {OUT}")
    dist = df["cod_canonico"].value_counts()
    print("Distribution by question:")
    print(dist.to_string())


if __name__ == "__main__":
    main()
