"""Build score.html, the human scoring page, from messages.jsonl and the rubric's applicability table.

Usage: python evals/build_score_page.py
"""
import json
from pathlib import Path

from lint import APPLIES, load

HERE = Path(__file__).parent
template = (HERE / "score_template.html").read_text()
page = template.replace("{{MESSAGES}}", json.dumps(load(), ensure_ascii=False)).replace("{{APPLIES}}", json.dumps(APPLIES))
(HERE / "score.html").write_text(page)
print("Wrote", HERE / "score.html")
