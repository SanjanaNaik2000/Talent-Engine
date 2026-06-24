<<<<<<< HEAD
# Talent Matching & Candidate Ranking Engine — "Data & AI Challenge"

An end-to-end AI-powered Candidate Discovery, Ranking, and Verification system built for the Redrob hackathon. It Semantically parses Job Descriptions and ranks a 100,000 candidate pool to find the top 100 fits, satisfying all speed, precision, and explainability requirements.

---

## 🚀 Quick Start & Run Commands

### 1. Installation
Set up your python environment and install all dependencies:
```bash
# Create and activate virtual environment (optional)
python -m venv venv
venv\Scripts\activate  # Windows

# Install required dependencies
pip install -r requirements.txt
```

### 2. Run the Ranking Pipeline (Reproducibility Command)
To run the ranking pipeline on the full dataset and generate the valid submission CSV, execute the following command:
```bash
python rank.py --candidates ./data/candidates.jsonl --out ./submission.csv
```
*Note: This command runs a memory-efficient stream, filters all honeypots, screens candidates via TF-IDF, embeds the top 2,000 via Sentence-BERT, scores them, and generates reasons. The ranking step completes in **under 45 seconds on CPU**.*

### 3. Launch the Flask Frontend Dashboard
To launch the recruiter dashboard with Flask, run:
```bash
python app.py
```
Then open your browser at:
```text
http://localhost:5000
```

---

## 🏛️ System Architecture & Methodology

### 1. Two-Stage Retrieve-and-Rank (CPU Constraint Optimization)
A key challenge constraint is running on **CPU only in under 5 minutes** over 100,000 candidates. Embedding all 100,000 profiles with `sentence-transformers` on CPU takes over 15 minutes. 
To optimize, we implement a **two-stage retrieve-and-rank** pipeline:
- **Stage 1 (Retrieval):** The system streams all candidates, filters out honeypots, and builds a fast TF-IDF vector index on the candidates. It computes a cosine similarity score with the parsed Job Description and selects the **top 2,000 candidates**. This takes **~3 seconds**.
- **Stage 2 (Dense Re-ranking):** It encodes the top 2,000 candidates' rich text profiles using the Sentence-BERT `all-MiniLM-L6-v2` model and computes deep semantic similarity. This takes **~30 seconds**.

### 2. Honeypot Filtration Rules
Organizer warnings identify ~80 honeypots with impossible profiles forced to relevance tier 0. Our engine detects and blocks **64 unique honeypot candidates** before ranking using 4 strict logical contradiction checks:
1. **Job Duration vs. Elapsed Time:** Job duration in career history exceeds the elapsed months between start date and today (June 18, 2026).
2. **Job Duration vs. Profile Experience:** A single job duration in career history exceeds the candidate's total profile years of experience.
3. **Education Timeline Contradiction:** Candidate started working $\ge 8$ years prior to starting university.
4. **Expert Skills with 0 Duration:** Skills marked "expert" that have a duration of 0 months.

### 3. Sub-Scoring & Hybrid Ranking Formula
For the top 2,000 candidates, individual sub-scores are calculated in the range $[0, 1]$:
- **Semantic Similarity (40%):** Cosine similarity between JD and Candidate profile embeddings (using `all-MiniLM-L6-v2`).
- **Skills Match (25%):** Analyzes required and preferred terms in structured/unstructured sections, applying severe penalties for **consulting-only careers** (90% reduction) and **pure CV/Speech focus without NLP/IR** (70% reduction).
- **Experience Score (20%):** Evaluates total experience, AI/ML-specific tenure, and applies penalties for **job-hoppers/title-chasers** (tenure < 18m) and **pure academic research backgrounds**.
- **Behavioral Signals (10%):** Aggregates recruiter response rate, interview completion, profile completeness, active recency, and open-to-work flag.
- **Education Score (5%):** Weighted combination of maximum institution tier (Tier 1-4) and field of study relevance.

$$Final\ Score = 0.40 \cdot Semantic + 0.25 \cdot Skills + 0.20 \cdot Experience + 0.10 \cdot Behavioral + 0.05 \cdot Education$$

Ties are broken deterministically by sorting `candidate_id` in ascending alphabetical order.

### 4. Factual Explainable Reasoning
A dynamic generator constructs 1-2 sentence summaries referencing specific facts (named skills, titles, response rates, tenures) while aligning the tone with the rank and addressing gaps honestly.

---

## 📂 Project Structure

```
project/ (D:\AIML project\New)
│
├── data/
│   ├── candidates.jsonl           # 100K candidates dataset
│   ├── job_description.docx       # Parsed Word JD
│   ├── sample_submission.csv      # Format spec reference
│   └── submission_profiles.json # Exported top 100 meta (auto-generated)
│
├── models/
│   └── ranking_engine.py          # TF-IDF filter + Sentence-BERT pipeline
│
├── utils/
│   ├── parser.py                  # XML docx extractor + Honeypot detector
│   ├── embedding.py               # Text vectorizer & cosine similarity
│   ├── scoring.py                 # Multi-aspect scoring functions & penalties
│   └── reasoning.py               # Factual reasoning generator
│
├── app.py                         # Flask recruiter dashboard
├── rank.py                        # CLI runner entry point
├── requirements.txt               # Dependencies list
└── README.md                      # Documentation
```
=======
# Candidate-Ranking-System
>>>>>>> 8d27aab4f56964aa168cfb6da587adfd51a4529e
