import json
from datetime import datetime
from utils.parser import parse_date

# Define Consulting firms to check for the consulting-only career disqualifier
CONSULTING_FIRMS = {
    "tcs", "tata consultancy services", "infosys", "wipro", "accenture", 
    "cognizant", "capgemini", "tech mahindra", "hcltech", "hcl", 
    "mindtree", "lti", "l&t infotech", "mphasis", "cts"
}

def calculate_skills_score(candidate):
    """
    Computes a skills match score in range [0, 1] based on required/preferred skills.
    Applies penalties for consulting-only careers and pure computer vision/speech focus.
    """
    skills = candidate.get("skills", [])
    career = candidate.get("career_history", [])
    profile = candidate.get("profile", {})
    
    # Text dump for unstructured checks
    text_dump = " ".join([
        profile.get("headline", ""),
        profile.get("summary", ""),
        profile.get("current_title", "")
    ]).lower()
    for job in career:
        text_dump += " " + job.get("title", "").lower() + " " + job.get("description", "").lower()

    # Define skill categories and their keywords
    required_categories = {
        "embeddings": ["embedding", "sentence-transformers", "dense retrieval", "bge", "e5", "sentence transformer", "text embeddings", "sentence-transformer"],
        "vector_db": ["vector database", "pinecone", "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "faiss", "vector search", "vector index", "hybrid search"],
        "python": ["python", "pyspark", "numpy", "pandas", "scipy", "scikit-learn"],
        "evaluation": ["ndcg", "mrr", "map", "eval", "ab test", "a/b test", "evaluation", "metrics", "benchmark"]
    }
    
    preferred_categories = {
        "fine_tuning": ["fine-tuning", "lora", "qlora", "peft", "llm fine-tuning", "finetuning", "parameter-efficient"],
        "learning_to_rank": ["learning to rank", "xgboost", "ltr", "neural ranking", "ranker", "ranking model"],
        "recruiting_tech": ["hr-tech", "recruiting tech", "hr tech", "recruitment", "talent acquisition", "marketplace"],
        "distributed_systems": ["distributed systems", "large-scale inference", "large scale inference", "spark", "hadoop", "ray", "kubernetes", "docker", "scalability", "inference optimization"],
        "open_source": ["open-source", "open source", "github"]
    }
    
    # 1. Score Required Skills (Max 60 points: 15 points per category)
    required_score = 0.0
    for cat_name, keywords in required_categories.items():
        cat_match = 0.0
        # Check structured skills
        for s in skills:
            s_name = s.get("name", "").lower()
            if any(kw in s_name for kw in keywords):
                prof = s.get("proficiency", "beginner").lower()
                dur = s.get("duration_months", 0)
                # Multipliers
                prof_mult = {"expert": 1.0, "advanced": 0.8, "intermediate": 0.6, "beginner": 0.3}.get(prof, 0.3)
                dur_mult = 0.8 + 0.2 * min(dur, 36) / 36.0
                score = prof_mult * dur_mult
                if score > cat_match:
                    cat_match = score
        # Check unstructured text if no structured match
        if cat_match == 0.0:
            if any(kw in text_dump for kw in keywords):
                cat_match = 0.5  # Medium credit for text mention
        
        required_score += cat_match * 15.0

    # 2. Score Preferred Skills (Max 40 points: 8 points per category)
    preferred_score = 0.0
    for cat_name, keywords in preferred_categories.items():
        cat_match = 0.0
        # Check structured skills
        for s in skills:
            s_name = s.get("name", "").lower()
            if any(kw in s_name for kw in keywords):
                prof = s.get("proficiency", "beginner").lower()
                dur = s.get("duration_months", 0)
                prof_mult = {"expert": 1.0, "advanced": 0.8, "intermediate": 0.6, "beginner": 0.3}.get(prof, 0.3)
                dur_mult = 0.8 + 0.2 * min(dur, 36) / 36.0
                score = prof_mult * dur_mult
                if score > cat_match:
                    cat_match = score
        # Check unstructured text if no structured match
        if cat_match == 0.0:
            if any(kw in text_dump for kw in keywords):
                cat_match = 0.5
                
        preferred_score += cat_match * 8.0
        
    skills_match_score = (required_score + preferred_score) / 100.0
    skills_match_score = min(max(skills_match_score, 0.0), 1.0)
    
    # Apply Disqualifier: Consulting-only career
    # Check if they have work experience, and if ALL companies they worked for are consulting firms
    if career:
        all_consulting = True
        for job in career:
            company = job.get("company", "").strip().lower()
            # Check if any consulting name is a substring or equal
            is_job_consulting = False
            for firm in CONSULTING_FIRMS:
                if firm in company:
                    is_job_consulting = True
                    break
            if not is_job_consulting:
                all_consulting = False
                break
        
        if all_consulting:
            skills_match_score *= 0.1  # Severe penalty (90% reduction) per JD

    # Apply Disqualifier: CV / Speech focus without NLP/IR
    cv_keywords = ["computer vision", "image classification", "object detection", "cnn", "opencv", "speech recognition", "tts", "audio", "robotics", "speech-to-text", "text-to-speech", "yolo", "segmentation"]
    nlp_keywords = ["nlp", "information retrieval", "search", "embeddings", "llm", "rag", "retrieval", "text classification", "bert", "gpt", "transformer", "semantic search", "faiss", "vector database"]
    
    has_cv = any(kw in text_dump for kw in cv_keywords) or any(any(kw in s.get("name", "").lower() for kw in cv_keywords) for s in skills)
    has_nlp = any(kw in text_dump for kw in nlp_keywords) or any(any(kw in s.get("name", "").lower() for kw in nlp_keywords) for s in skills)
    
    if has_cv and not has_nlp:
        skills_match_score *= 0.3  # Severe penalty (70% reduction) for wrong AI domain focus
        
    return skills_match_score

def calculate_experience_score(candidate, current_date=datetime(2026, 6, 18)):
    """
    Computes an experience score in range [0, 1].
    Evaluates:
    - Total years of experience (ideal 5-9 years).
    - AI/ML specific tenure (ideal 4-5 years in applied ML/AI roles).
    - Job-hopping / title-chasing behavior (average tenure < 18 months).
    - Pure research backgrounds (academic labs, no production coding).
    - Current coding active status (written code in last 18 months).
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    
    years_exp = profile.get("years_of_experience", 0.0)
    
    # 1. Total Years of Experience Score
    if 5.0 <= years_exp <= 9.0:
        total_exp_score = 1.0
    elif 4.0 <= years_exp <= 10.0:
        total_exp_score = 0.8
    elif 3.0 <= years_exp <= 12.0:
        total_exp_score = 0.6
    else:
        total_exp_score = 0.3
        
    # 2. AI/ML specific tenure
    aiml_keywords = ["ai", "ml", "machine learning", "data scientist", "nlp", "retrieval", "search", "recommendation", "deep learning", "applied ml", "vector", "embedding"]
    aiml_months = 0
    for job in career:
        title = job.get("title", "").lower()
        desc = job.get("description", "").lower()
        if any(kw in title for kw in aiml_keywords) or any(kw in desc for kw in aiml_keywords):
            aiml_months += job.get("duration_months", 0)
            
    aiml_years = aiml_months / 12.0
    if aiml_years >= 4.0:
        aiml_score = 1.0
    elif aiml_years >= 2.0:
        aiml_score = 0.7
    elif aiml_years >= 1.0:
        aiml_score = 0.4
    else:
        aiml_score = 0.1
        
    exp_score = 0.5 * total_exp_score + 0.5 * aiml_score
    
    # Apply Penalty: Title-Chasing (Job-Hopping)
    # Average job tenure check
    if career:
        total_tenure_months = sum(job.get("duration_months", 0) for job in career)
        avg_tenure_months = total_tenure_months / len(career) if len(career) > 0 else 0
        if avg_tenure_months < 18.0:
            exp_score *= 0.7  # 30% penalty
        elif avg_tenure_months < 12.0:
            exp_score *= 0.5  # 50% penalty
            
    # Apply Penalty: Pure research (No production deployment)
    if career:
        all_research = True
        has_industry_job = False
        for job in career:
            title = job.get("title", "").lower()
            desc = job.get("description", "").lower()
            # If the job title doesn't contain pure research terms, or description indicates production
            is_research = ("research" in title or "intern" in title or "phd" in title or "academic" in title) and "engineer" not in title
            if not is_research:
                has_industry_job = True
                all_research = False
                break
        if all_research and not has_industry_job:
            exp_score *= 0.5  # 50% penalty for academic-only profile per JD
            
    # Apply Penalty: Senior engineer who hasn't coded in last 18 months
    # Check if the most recent job title suggests pure manager/architect without engineer
    if career:
        # Sort career history by start date descending to find the current/most recent job
        recent_job = sorted(career, key=lambda x: x.get("start_date", ""), reverse=True)[0]
        title = recent_job.get("title", "").lower()
        # If title matches purely manager or architect without "engineer" or "developer"
        if any(mgr in title for mgr in ["manager", "director", "vp", "president", "head"]) and not any(eng in title for eng in ["engineer", "developer", "programmer", "scientist"]):
            exp_score *= 0.8  # 20% penalty for lack of recent active coding role
            
    return min(max(exp_score, 0.0), 1.0)

def calculate_behavioral_score(candidate, current_date=datetime(2026, 6, 18)):
    """
    Computes a composite behavioral signal score in range [0, 1].
    Signals analyzed:
    - recruiter_response_rate (25% weight)
    - interview_completion_rate (25% weight)
    - last_active_date recency (20% weight)
    - profile_completeness_score (10% weight)
    - open_to_work_flag (10% weight)
    - github_activity_score (10% weight)
    """
    signals = candidate.get("redrob_signals", {})
    
    # 1. Recruiter Response Rate
    resp_rate = signals.get("recruiter_response_rate", 0.0)
    
    # 2. Interview Completion Rate
    int_comp_rate = signals.get("interview_completion_rate", 0.0)
    
    # 3. Last Active Date Recency
    active_str = signals.get("last_active_date")
    active_date = parse_date(active_str)
    if active_date:
        days_active = (current_date - active_date).days
        if days_active <= 30:
            active_score = 1.0
        elif days_active <= 90:
            active_score = 0.8
        elif days_active <= 180:
            active_score = 0.5
        else:
            active_score = 0.1
    else:
        active_score = 0.1
        
    # 4. Profile Completeness
    completeness = signals.get("profile_completeness_score", 0.0) / 100.0
    
    # 5. Open To Work Flag
    open_flag = 1.0 if signals.get("open_to_work_flag", False) else 0.5
    
    # 6. GitHub Activity
    gh_score = signals.get("github_activity_score", -1.0)
    if gh_score == -1.0:
        github_score = 0.2  # Base score for no GitHub linked
    else:
        github_score = gh_score / 100.0
        
    beh_score = (
        0.25 * resp_rate +
        0.25 * int_comp_rate +
        0.20 * active_score +
        0.10 * completeness +
        0.10 * open_flag +
        0.10 * github_score
    )
    
    return min(max(beh_score, 0.0), 1.0)

def calculate_education_score(candidate):
    """
    Computes an education score in range [0, 1].
    Evaluates:
    - Maximum institution tier (60% weight).
    - Field of study relevance (40% weight).
    """
    edu = candidate.get("education", [])
    if not edu:
        return 0.2 # Default low score if no education listed
        
    # 1. Institution Tier Score
    max_tier_score = 0.2
    for school in edu:
        tier = school.get("tier", "unknown").lower()
        tier_score = {"tier_1": 1.0, "tier_2": 0.8, "tier_3": 0.6, "tier_4": 0.4, "unknown": 0.2}.get(tier, 0.2)
        if tier_score > max_tier_score:
            max_tier_score = tier_score
            
    # 2. Field of Study Relevance
    high_rel = ["computer science", "artificial intelligence", "machine learning", "data science", 
                "software engineering", "computer engineering", "statistics", "mathematics", "cs", "it"]
    med_rel = ["electrical", "electronics", "information technology", "physics", "quantitative", "engineering", "mechanical"]
    
    max_rel_score = 0.3
    for school in edu:
        field = school.get("field_of_study", "").lower()
        degree = school.get("degree", "").lower()
        
        # Check relevance
        rel_score = 0.3
        if any(rel in field for rel in high_rel) or any(rel in degree for rel in high_rel):
            rel_score = 1.0
        elif any(rel in field for rel in med_rel) or any(rel in degree for rel in med_rel):
            rel_score = 0.7
            
        if rel_score > max_rel_score:
            max_rel_score = rel_score
            
    edu_score = 0.6 * max_tier_score + 0.4 * max_rel_score
    return min(max(edu_score, 0.0), 1.0)
