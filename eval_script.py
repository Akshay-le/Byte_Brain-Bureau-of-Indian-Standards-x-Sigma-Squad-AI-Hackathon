import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict, Any


def normalize_standard_id(s: str) -> str:
    return s.strip().upper().replace(" ", "")


def hit_rate_at_k(predictions: List[Dict], ground_truth: Dict[str, List[str]], k: int = 3) -> float:
   
    hits = 0
    total = 0
    for pred in predictions:
        qid = pred["id"]
        if qid not in ground_truth:
            continue
        total += 1
        expected = {normalize_standard_id(s) for s in ground_truth[qid]}
        retrieved_top_k = [normalize_standard_id(s) for s in pred["retrieved_standards"][:k]]
        if any(s in expected for s in retrieved_top_k):
            hits += 1
    return (hits / total * 100) if total > 0 else 0.0


def mrr_at_k(predictions: List[Dict], ground_truth: Dict[str, List[str]], k: int = 5) -> float:

    rr_sum = 0.0
    total = 0
    for pred in predictions:
        qid = pred["id"]
        if qid not in ground_truth:
            continue
        total += 1
        expected = {normalize_standard_id(s) for s in ground_truth[qid]}
        retrieved_top_k = [normalize_standard_id(s) for s in pred["retrieved_standards"][:k]]
        for rank, std in enumerate(retrieved_top_k, start=1):
            if std in expected:
                rr_sum += 1.0 / rank
                break
    return (rr_sum / total) if total > 0 else 0.0


def avg_latency(predictions: List[Dict]) -> float:
    """Average latency per query in seconds."""
    latencies = [p.get("latency_seconds", 0.0) for p in predictions]
    return sum(latencies) / len(latencies) if latencies else 0.0


def evaluate(predictions_path: str, ground_truth_path: str) -> Dict[str, Any]:
    # Load predictions
    with open(predictions_path, "r", encoding="utf-8") as f:
        predictions = json.load(f)

    # Load ground truth
    with open(ground_truth_path, "r", encoding="utf-8") as f:
        gt_raw = json.load(f)

    # Build ground truth lookup
    gt: Dict[str, List[str]] = {}
    for item in gt_raw:
        gt[item["id"]] = item.get("expected_standards", [])

    hr3 = hit_rate_at_k(predictions, gt, k=3)
    mrr5 = mrr_at_k(predictions, gt, k=5)
    lat = avg_latency(predictions)

    metrics = {
        "hit_rate_at_3": round(hr3, 2),
        "mrr_at_5": round(mrr5, 4),
        "avg_latency_seconds": round(lat, 4),
        "total_queries": len(predictions),
        "graded_queries": sum(1 for p in predictions if p["id"] in gt),
    }
    return metrics


def main():
    parser = argparse.ArgumentParser(description="BIS Standards RAG Evaluation Script")
    parser.add_argument("--predictions", required=True, help="Path to predictions JSON")
    parser.add_argument("--ground-truth", required=True, help="Path to ground truth JSON")
    args = parser.parse_args()

    if not Path(args.predictions).exists():
        print(f"ERROR: Predictions file not found: {args.predictions}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.ground_truth).exists():
        print(f"ERROR: Ground truth file not found: {args.ground_truth}", file=sys.stderr)
        sys.exit(1)

    metrics = evaluate(args.predictions, args.ground_truth)

    print("\n" + "=" * 50)
    print("  BIS Standards RAG – Evaluation Results")
    print("=" * 50)
    print(f"  Hit Rate @3         : {metrics['hit_rate_at_3']:.2f}%  (target: >80%)")
    print(f"  MRR @5              : {metrics['mrr_at_5']:.4f}  (target: >0.7)")
    print(f"  Avg Latency (s)     : {metrics['avg_latency_seconds']:.4f}  (target: <5s)")
    print(f"  Total Queries       : {metrics['total_queries']}")
    print(f"  Graded Queries      : {metrics['graded_queries']}")
    print("=" * 50 + "\n")
    print(json.dumps(metrics, indent=2))
    return metrics


if __name__ == "__main__":
    main()
