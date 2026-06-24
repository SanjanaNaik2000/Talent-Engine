import os
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from utils.parser import parse_docx, load_candidates_stream, is_honeypot
from utils.embedding import load_embedding_model, get_candidate_text, compute_cosine_similarity
from utils.scoring import (
    calculate_skills_score,
    calculate_experience_score,
    calculate_behavioral_score,
    calculate_education_score
)
from utils.reasoning import generate_reasoning

def run_ranking_pipeline(candidates_file, jd_file, output_csv):
    """
    Runs the complete Talent Matching and Candidate Ranking pipeline.
    """
    print(f"1. Parsing Job Description from {jd_file}...")
    jd_text = parse_docx(jd_file)
    if "Error reading" in jd_text:
        print(f"Error parsing job description: {jd_text}")
        return False
        
    print("2. Loading and screening candidates...")
    candidates = []
    texts = []
    cids = []
    
    honeypot_count = 0
    total_count = 0
    
    # Memory-efficient streaming read
    for cand in load_candidates_stream(candidates_file):
        total_count += 1
        cid = cand.get("candidate_id")
        
        # Honeypot filtering
        if is_honeypot(cand):
            honeypot_count += 1
            continue
            
        text = get_candidate_text(cand)
        candidates.append(cand)
        texts.append(text)
        cids.append(cid)
        
    print(f"Total candidates scanned: {total_count}")
    print(f"Honeypot candidates filtered: {honeypot_count}")
    print(f"Valid candidates remaining: {len(candidates)}")
    
    if not candidates:
        print("No valid candidates found!")
        return False
        
    print("3. Running Stage 1 Retrieval (TF-IDF screening)...")
    # Compute TF-IDF cosine similarity between candidates and Job Description
    vectorizer = TfidfVectorizer(stop_words='english')
    # Fit on candidates + JD to build vocabulary
    all_texts = texts + [jd_text]
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    
    # Candidates TF-IDF and JD TF-IDF vectors
    candidates_tfidf = tfidf_matrix[:-1]
    jd_tfidf = tfidf_matrix[-1]
    
    # Cosine similarities
    from sklearn.metrics.pairwise import cosine_similarity
    similarities = cosine_similarity(candidates_tfidf, jd_tfidf).flatten()
    
    # Select top 2,000 candidates for deep Sentence-BERT ranking
    top_n = min(2000, len(candidates))
    top_indices = np.argsort(similarities)[-top_n:][::-1]
    
    print(f"Selected top {top_n} candidates for Stage 2 dense ranking.")
    
    # Subset candidates
    retrieved_candidates = [candidates[i] for i in top_indices]
    retrieved_texts = [texts[i] for i in top_indices]
    
    print("4. Running Stage 2 Dense Ranking (Sentence-BERT & Scoring)...")
    print("Loading Sentence-BERT model (all-MiniLM-L6-v2)...")
    model = load_embedding_model()
    
    # Embed JD
    jd_embedding = model.encode(jd_text, show_progress_bar=False)
    
    # Embed top candidates
    print("Generating candidate embeddings...")
    candidate_embeddings = model.encode(retrieved_texts, show_progress_bar=False, batch_size=64)
    
    print("Computing sub-scores...")
    scored_candidates = []
    for idx, (cand, emb) in enumerate(zip(retrieved_candidates, candidate_embeddings)):
        cid = cand.get("candidate_id")
        
        # 1. Semantic Similarity Score (40%)
        semantic_sim = compute_cosine_similarity(jd_embedding, emb)
        # Shift cosine similarity from [-1, 1] to [0, 1] for normalization
        semantic_score = (semantic_sim + 1.0) / 2.0
        
        # 2. Skills Match Score (25%)
        skills_score = calculate_skills_score(cand)
        
        # 3. Experience Match Score (20%)
        exp_score = calculate_experience_score(cand)
        
        # 4. Behavioral Signal Score (10%)
        beh_score = calculate_behavioral_score(cand)
        
        # 5. Education Score (5%)
        edu_score = calculate_education_score(cand)
        
        # Compute final composite score and round to 4 decimals immediately for sorting and tie-breaking
        final_score = round(
            0.40 * semantic_score +
            0.25 * skills_score +
            0.20 * exp_score +
            0.10 * beh_score +
            0.05 * edu_score,
            4
        )
        
        scored_candidates.append({
            "candidate_id": cid,
            "score": final_score,
            "semantic_score": semantic_score,
            "skills_score": skills_score,
            "experience_score": exp_score,
            "behavioral_score": beh_score,
            "education_score": edu_score,
            "candidate_data": cand
        })
        
    # Sort candidates by final score (descending)
    # Tie-breaking: if scores are equal, sort candidate_id ascending (alphabetical order)
    # In Python, sorting a list of dicts can be done by specifying key as tuple (score descending, candidate_id ascending)
    # Since we want score descending, we can use -score.
    scored_candidates.sort(key=lambda x: (-x["score"], x["candidate_id"]))
    
    # Select top 100
    top_100 = scored_candidates[:100]
    
    print("5. Generating explainable reasoning for top 100 candidates...")
    final_rows = []
    for rank_idx, item in enumerate(top_100):
        rank = rank_idx + 1
        cand_data = item["candidate_data"]
        
        reasoning = generate_reasoning(
            cand_data, 
            rank, 
            item["score"], 
            item["semantic_score"], 
            item["skills_score"], 
            item["experience_score"], 
            item["behavioral_score"]
        )
        
        final_rows.append({
            "candidate_id": item["candidate_id"],
            "rank": rank,
            "score": round(item["score"], 4),
            "reasoning": reasoning
        })
        
    print(f"6. Writing submission to {output_csv}...")
    df_out = pd.DataFrame(final_rows)
    df_out.to_csv(output_csv, index=False, encoding="utf-8")
    
    # Save top 100 profiles + sub-scores for instant dashboard loading
    import json
    profiles_out = [item["candidate_data"] for item in top_100]
    for i, profile in enumerate(profiles_out):
        profile["rank"] = i + 1
        profile["score"] = round(top_100[i]["score"], 4)
        profile["reasoning"] = final_rows[i]["reasoning"]
        profile["sub_scores"] = {
            "semantic": round(top_100[i]["semantic_score"], 4),
            "skills": round(top_100[i]["skills_score"], 4),
            "experience": round(top_100[i]["experience_score"], 4),
            "behavioral": round(top_100[i]["behavioral_score"], 4),
            "education": round(top_100[i]["education_score"], 4)
        }
        
    profiles_json_path = output_csv.replace(".csv", "_profiles.json")
    with open(profiles_json_path, "w", encoding="utf-8") as f:
        json.dump(profiles_out, f, indent=2, ensure_ascii=False)
    print(f"Saved top 100 profiles metadata to {profiles_json_path}")
    
    print("Pipeline run completed successfully.")
    return True
