import numpy as np
from sentence_transformers import SentenceTransformer

def load_embedding_model(model_name="all-MiniLM-L6-v2"):
    """Load the Sentence-BERT model."""
    return SentenceTransformer(model_name)

def get_candidate_text(candidate):
    """
    Construct a rich, textual representation of the candidate profile
    for generating semantic embeddings.
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    edu = candidate.get("education", [])
    
    parts = []
    
    # Current role and overview
    current_title = profile.get("current_title", "")
    headline = profile.get("headline", "")
    summary = profile.get("summary", "")
    
    if current_title:
        parts.append(f"Current Professional Title: {current_title}")
    if headline:
        parts.append(f"Professional Headline: {headline}")
    if summary:
        parts.append(f"Professional Summary: {summary}")
        
    # Skills list
    skill_names = [s.get("name") for s in skills if s.get("name")]
    if skill_names:
        parts.append(f"Core Technical and Soft Skills: {', '.join(skill_names)}")
        
    # Career history titles and responsibilities
    career_list = []
    for job in career:
        title = job.get("title", "")
        company = job.get("company", "")
        desc = job.get("description", "")
        job_str = f"Role: {title} at {company}."
        if desc:
            job_str += f" Responsibilities and Achievements: {desc}"
        career_list.append(job_str)
        
    if career_list:
        parts.append("Work Experience:\n" + "\n".join(career_list))
        
    # Education
    edu_list = []
    for school in edu:
        deg = school.get("degree", "")
        field = school.get("field_of_study", "")
        inst = school.get("institution", "")
        edu_list.append(f"{deg} in {field} from {inst}")
        
    if edu_list:
        parts.append(f"Educational Background: {'; '.join(edu_list)}")
        
    return "\n\n".join(parts)

def compute_cosine_similarity(embedding1, embedding2):
    """Compute cosine similarity between two embeddings (vectors)."""
    dot_product = np.dot(embedding1, embedding2)
    norm_a = np.linalg.norm(embedding1)
    norm_b = np.linalg.norm(embedding2)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(dot_product / (norm_a * norm_b))
