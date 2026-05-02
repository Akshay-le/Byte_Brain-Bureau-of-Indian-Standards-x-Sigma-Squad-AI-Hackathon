import argparse
import json
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from src.rag_pipeline import recommend

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_inference(input_path: str, output_path: str, top_k: int = 5) -> None:
    input_file = Path(input_path)
    if not input_file.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)

    with open(input_file, "r", encoding="utf-8") as f:
        queries = json.load(f)

    if not isinstance(queries, list):
        logger.error("Input JSON must be a list of objects with 'id' and 'query' fields.")
        sys.exit(1)

    results = []
    total = len(queries)
    for i, item in enumerate(queries, 1):
        qid = item.get("id", f"q{i}")
        query = item.get("query", "")
        logger.info(f"[{i}/{total}] Processing id={qid}")

        try:
            output = recommend(query, top_k=top_k)
            standard_ids = [s["standard_id"] for s in output["retrieved_standards"]]
            results.append({
                "id": qid,
                "retrieved_standards": standard_ids,
                "latency_seconds": output["latency_seconds"],
            })
        except Exception as e:
            logger.error(f"Error on query id={qid}: {e}")
            results.append({
                "id": qid,
                "retrieved_standards": [],
                "latency_seconds": 0.0,
            })

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    logger.info(f"Results saved to {output_path}  ({total} queries processed)")


def main():
    parser = argparse.ArgumentParser(description="BIS Standards RAG Inference Script")
    parser.add_argument("--input", required=True, help="Path to input JSON file")
    parser.add_argument("--output", required=True, help="Path to output JSON file")
    parser.add_argument("--top-k", type=int, default=5, help="Number of standards to retrieve (default: 5)")
    args = parser.parse_args()
    run_inference(args.input, args.output, args.top_k)


if __name__ == "__main__":
    main()
