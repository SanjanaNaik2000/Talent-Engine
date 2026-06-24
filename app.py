import os
import json
import csv
import re
import sys
import pandas as pd
from flask import Flask, render_template, jsonify, send_file, request

# Add local directories to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.parser import parse_docx
from models.ranking_engine import run_ranking_pipeline

app = Flask(__name__)

# File paths
CSV_PATH = "./submission.csv"
JSON_PATH = "./submission_profiles.json"
JD_PATH = "./data/job_description.docx"
CANDIDATES_PATH = "./data/candidates.jsonl"

@app.route("/")
def index():
    """Render the dashboard template."""
    return render_template("index.html")

@app.route("/api/candidates")
def get_candidates():
    """Retrieve top 100 candidate profiles."""
    if not os.path.exists(JSON_PATH) or not os.path.exists(CSV_PATH):
        return jsonify({"status": "error", "message": "Pipeline has not been initialized yet"}), 404
        
    try:
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            profiles = json.load(f)
        return jsonify({"status": "success", "candidates": profiles})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/job-description")
def get_job_description():
    """Parse and return job description text."""
    if not os.path.exists(JD_PATH):
        return jsonify({"status": "error", "message": "Job description file not found"}), 404
    try:
        jd_text = parse_docx(JD_PATH)
        return jsonify({"status": "success", "text": jd_text})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/run-pipeline", methods=["POST"])
def run_pipeline():
    """Run the candidate ranking engine pipeline."""
    try:
        # Run synchronously. development server runs multi-threaded so UI doesn't freeze.
        success = run_ranking_pipeline(CANDIDATES_PATH, JD_PATH, CSV_PATH)
        if success:
            return jsonify({"status": "success", "message": "Pipeline execution completed successfully"})
        else:
            return jsonify({"status": "error", "message": "Pipeline execution failed"}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/download-csv")
def download_csv():
    """Serve the generated submission CSV file."""
    if not os.path.exists(CSV_PATH):
        return "Submission file not found. Please run the ranking engine first.", 404
    return send_file(CSV_PATH, as_attachment=True, download_name="submission.csv", mimetype="text/csv")

@app.route("/download-xlsx")
def download_xlsx():
    """Serve the generated submission as an Excel (XLSX) file."""
    if not os.path.exists(CSV_PATH):
        return "Submission file not found. Please run the ranking engine first.", 404
    
    xlsx_path = CSV_PATH.replace(".csv", ".xlsx")
    try:
        df = pd.read_csv(CSV_PATH)
        df.to_excel(xlsx_path, index=False, sheet_name="Recommended Candidates")
        return send_file(xlsx_path, as_attachment=True, download_name="submission.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except Exception as e:
        return f"Error exporting Excel file: {e}", 500

@app.route("/validate-csv")
def validate_csv():
    """Format and constraint validator for generated submission CSV."""
    if not os.path.exists(CSV_PATH):
        return jsonify({"status": "error", "errors": ["Submission file not found."]}), 404
        
    errors = []
    try:
        with open(CSV_PATH, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                return jsonify({"status": "success", "errors": ["File is empty"]})
                
            if header != ["candidate_id", "rank", "score", "reasoning"]:
                errors.append("Header mismatch. Expected: candidate_id,rank,score,reasoning")
            
            rows = list(reader)
            if len(rows) != 100:
                errors.append(f"Expected exactly 100 rows, found {len(rows)}.")
                
            seen_ids = set()
            seen_ranks = set()
            by_rank = []
            
            for i, cells in enumerate(rows):
                row_num = 2 + i
                if len(cells) != 4:
                    errors.append(f"Row {row_num}: Expected 4 columns, got {len(cells)}")
                    continue
                cid, rank_s, score_s, reasoning = cells
                
                # Check candidate id pattern
                if not re.match(r"^CAND_[0-9]{7}$", cid):
                    errors.append(f"Row {row_num}: Invalid candidate ID: '{cid}'")
                if cid in seen_ids:
                    errors.append(f"Row {row_num}: Duplicate candidate ID: '{cid}'")
                seen_ids.add(cid)
                
                # Check rank integer
                try:
                    rank = int(rank_s)
                    if not 1 <= rank <= 100:
                        errors.append(f"Row {row_num}: Rank must be between 1 and 100")
                    if rank in seen_ranks:
                        errors.append(f"Row {row_num}: Duplicate rank: {rank}")
                    seen_ranks.add(rank)
                except ValueError:
                    errors.append(f"Row {row_num}: Rank must be an integer")
                    rank = None
                    
                # Check score float
                try:
                    score = float(score_s)
                except ValueError:
                    errors.append(f"Row {row_num}: Score must be a float")
                    score = None
                    
                if rank is not None and score is not None:
                    by_rank.append((rank, score, cid))
                    
            # Check scores non-increasing
            by_rank.sort(key=lambda x: x[0])
            for idx in range(len(by_rank) - 1):
                r1, s1, c1 = by_rank[idx]
                r2, s2, c2 = by_rank[idx+1]
                if s1 < s2:
                    errors.append(f"Score violation: Rank {r1} ({s1}) < Rank {r2} ({s2})")
                if s1 == s2 and c1 > c2:
                    errors.append(f"Tie-break violation: Rank {r1} & {r2} have score {s1} but ID {c1} is > {c2}")
                    
        return jsonify({"status": "success", "errors": errors})
    except Exception as e:
        return jsonify({"status": "error", "errors": [f"Cannot read file: {e}"]}), 500

if __name__ == "__main__":
    # Run the Flask app on localhost:5000
    app.run(host="127.0.0.1", port=5000, debug=True)
