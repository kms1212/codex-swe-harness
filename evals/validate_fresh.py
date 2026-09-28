"""Score grader-only labels against one fresh native child per v2 case."""
import json
from pathlib import Path

from harness_v0.core import digest
from harness_v0.review import validate_result

ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def main():
    primary = {row["case_id"]: row for row in rows(ROOT / "evals" / "observed-results.jsonl")}
    primary.update({row["case_id"]: row for row in rows(ROOT / "eval-results" / "raw-traces" / "fresh-reruns.jsonl")})
    labels = {row["case_id"]: row["expected_criterion"] for row in json.loads((ROOT / "evals" / "grader-labels.json").read_text())}
    score = {"cases": len(labels), "defects_detected": 0, "defects_total": sum(value is not None for value in labels.values()), "clean_false_positive": 0, "invalid_final_results": 0, "details": []}
    for case_id, expected in labels.items():
        row = primary[case_id]
        package_path = ROOT / "eval-results" / "controlled" / case_id / "challenge-v2-review-1.json"
        package = json.loads(package_path.read_text())
        result = row["result"]
        try:
            validate_result(result, digest(package), "builtin_subagent", {item["criterion"] for item in package["applicable_rubric"]})
        except ValueError:
            score["invalid_final_results"] += 1
            raise
        criteria = {item["criterion"] for item in result["findings"]}
        detected = expected in criteria if expected is not None else None
        if detected:
            score["defects_detected"] += 1
        if expected is None and result["findings"]:
            score["clean_false_positive"] += len(result["findings"])
        score["details"].append({"case_id": case_id, "expected": expected, "observed": sorted(criteria), "detected": detected, "native_child": row["agent"]})
    output = ROOT / "eval-results" / "controlled" / "score.json"
    output.write_text(json.dumps(score, indent=2) + "\n")
    print(json.dumps(score, indent=2))


if __name__ == "__main__":
    main()
