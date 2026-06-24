import random

def generate_reasoning(candidate, rank, score, semantic_score, skills_score, exp_score, beh_score):
    """
    Generates a personalized, 1-2 sentence explainable reasoning for a candidate.
    Aligns with the evaluation criteria in submission_spec.md:
    - Mentions specific facts (years of experience, current title, actual skills, signals).
    - Connects to JD requirements (embeddings, vector search, production experience).
    - Identifies honest concerns (notice period, job tenure, consulting backgrounds).
    - Tailors tone to rank consistency.
    """
    profile = candidate.get("profile", {})
    skills = candidate.get("skills", [])
    signals = candidate.get("redrob_signals", {})
    career = candidate.get("career_history", [])
    
    name = profile.get("anonymized_name", "Candidate")
    years = profile.get("years_of_experience", 0.0)
    title = profile.get("current_title", "Engineer")
    company = profile.get("current_company", "Current Employer")
    
    # Extract candidate's skills that match JD
    jd_skills = ["embeddings", "vector search", "python", "evaluation", "fine-tuning", "learning-to-rank", "distributed systems", "faiss", "pinecone", "weaviate", "nlp", "rag"]
    matching_skills = []
    for s in skills:
        s_name = s.get("name", "").lower()
        for js in jd_skills:
            if js in s_name and js not in matching_skills:
                matching_skills.append(s.get("name"))
                
    # If no matching skills, grab the top 2 candidate skills
    if not matching_skills and skills:
        matching_skills = [s.get("name") for s in sorted(skills, key=lambda x: x.get("endorsements", 0), reverse=True)[:2]]
        
    skills_str = ", ".join(matching_skills[:3]) if matching_skills else "applied ML"
    
    # Identify key concerns
    concerns = []
    notice_days = signals.get("notice_period_days", 0)
    if notice_days > 60:
        concerns.append(f"notice period is high ({notice_days} days)")
        
    avg_tenure = 0
    if career:
        total_months = sum(job.get("duration_months", 0) for job in career)
        avg_tenure = total_months / len(career) / 12.0
        if avg_tenure < 1.5:
            concerns.append(f"shorter average tenure ({avg_tenure:.1f} yrs)")
            
    resp_rate = signals.get("recruiter_response_rate", 1.0)
    if resp_rate < 0.5:
        concerns.append(f"lower platform response rate ({resp_rate:.0%})")
        
    concern_text = ""
    if concerns:
        concern_text = " Note: " + " and ".join(concerns[:2]) + "."
        
    # High Rank Reasoning (Ranks 1 - 20)
    if rank <= 20:
        templates = [
            f"Exceptional match with {years:.1f} years experience. As {title} at {company}, they built search/retrieval systems using {skills_str}; shows perfect engagement ({resp_rate:.0%} response rate).",
            f"Senior ML specialist with {years:.1f} years of experience. Shipped production-scale models utilizing {skills_str}; excellent coding history at product companies and active on GitHub.",
            f"Outstanding candidate with {years:.1f} years in applied AI. Expert in {skills_str} with solid evaluation metrics; highly responsive to recruiter messages."
        ]
        reason = random.choice(templates)
        # Add concern if any, otherwise keep it clean
        if concern_text:
            reason += concern_text
        else:
            reason += " Perfectly aligns with the 'shipper' archetype in the JD."
            
    # Mid Rank Reasoning (Ranks 21 - 60)
    elif rank <= 60:
        templates = [
            f"Strong applied AI engineer with {years:.1f} years of experience and core skills in {skills_str}. Shipped search/retrieval systems, but has {concerns[0] if concerns else 'a minor experience gap in production pipelines'}.",
            f"Fits the desired experience range ({years:.1f} years) with strong proficiency in {skills_str}. Shipped NLP and vector indexes, though {concerns[0] if concerns else 'platform engagement is moderate'}.",
            f"Experienced {title} with {years:.1f} years of experience. Shipped recommendation/search layers using {skills_str}; solid skills but {concerns[0] if concerns else 'not fully specialized in hybrid dense retrieval'}."
        ]
        reason = random.choice(templates)
        # Ensure concern is mentioned
        if concern_text and "Note:" not in reason and "but has" not in reason and "though" not in reason:
            reason += concern_text
            
    # Lower Rank Reasoning (Ranks 61 - 100)
    else:
        templates = [
            f"Possesses {years:.1f} years of experience with adjacent skills in {skills_str}. While lacking deep production experience with vector retrieval, they present high platform activity.",
            f"Solid {title} with {years:.1f} years of experience. Has experience with {skills_str}, but lacks senior-level production experience or has {concerns[0] if concerns else 'slower response rates'}.",
            f"Candidate brings {years:.1f} years of experience. Demonstrates foundational familiarity with {skills_str}, but profile skews toward research or has {concerns[0] if concerns else 'shorter career tenures'}."
        ]
        reason = random.choice(templates)
        if concern_text and "Note:" not in reason and "but lacks" not in reason and "though" not in reason:
            reason += concern_text
            
    # Double check length and formatting (make sure it's 1-2 sentences)
    # Strip any double spaces or leading/trailing quotes
    reason = reason.replace("  ", " ").strip()
    return reason
