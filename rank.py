import argparse
import sys
import os

# Add the current directory to sys.path so we can import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.ranking_engine import run_ranking_pipeline

def main():
    parser = argparse.ArgumentParser(description="Talent Matching and Candidate Ranking CLI Runner")
    parser.add_argument(
        "--candidates", 
        type=str, 
        default="./data/candidates.jsonl",
        help="Path to candidates.jsonl file"
    )
    parser.add_argument(
        "--jd", 
        type=str, 
        default="./data/job_description.docx",
        help="Path to job_description.docx file"
    )
    parser.add_argument(
        "--out", 
        type=str, 
        default="./submission.csv",
        help="Output path for the generated submission CSV"
    )

    args = parser.parse_args()

    # Ensure paths are correct and absolute if needed
    candidates_path = os.path.abspath(args.candidates)
    jd_path = os.path.abspath(args.jd)
    out_path = os.path.abspath(args.out)

    if not os.path.exists(candidates_path):
        print(f"Error: Candidate file not found at {candidates_path}")
        sys.exit(1)
        
    if not os.path.exists(jd_path):
        print(f"Error: Job Description file not found at {jd_path}")
        sys.exit(1)

    print(f"Starting Candidate Ranking Engine...")
    print(f"Input Candidates: {candidates_path}")
    print(f"Input Job Description: {jd_path}")
    print(f"Output Submission: {out_path}")
    print("-" * 50)

    success = run_ranking_pipeline(candidates_path, jd_path, out_path)
    
    if success:
        print("-" * 50)
        print("Success! Candidate ranking generated.")
        sys.exit(0)
    else:
        print("-" * 50)
        print("Error: Pipeline execution failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
