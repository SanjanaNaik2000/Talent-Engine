import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
import os

def parse_docx(docx_path):
    """
    Extract all text, including tables and paragraphs, from a Word docx file in order.
    Does not depend on external python-docx library.
    """
    try:
        with zipfile.ZipFile(docx_path) as docx:
            xml_content = docx.read('word/document.xml')
            root = ET.fromstring(xml_content)
            
            # XML Namespaces
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            def get_text(elem):
                return ''.join(t.text for t in elem.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if t.text)
            
            body = root.find('.//w:body', ns)
            if body is None:
                body = root
            
            lines = []
            for child in body:
                tag = child.tag.split('}')[-1]
                if tag == 'p':
                    txt = get_text(child)
                    if txt:
                        lines.append(txt)
                elif tag == 'tbl':
                    for row in child.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tr'):
                        row_cells = []
                        for cell in row.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}tc'):
                            cell_text = " ".join(get_text(p) for p in cell.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/p}') or cell.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'))
                            if not cell_text:
                                cell_text = get_text(cell)
                            row_cells.append(cell_text.strip())
                        lines.append(" | ".join(row_cells))
            return '\n'.join(lines)
    except Exception as e:
        return f"Error reading {docx_path}: {e}"

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except:
        return None

def is_honeypot(candidate, current_date=datetime(2026, 6, 18)):
    """
    Detects honeypot candidates based on logical contradictions:
    1. Expert skills with 0 duration.
    2. Job duration > elapsed time since start date.
    3. Education timeline contradiction (Started working >= 8 years before university).
    4. Job duration in career history > profile years of experience.
    """
    profile = candidate.get("profile", {})
    career = candidate.get("career_history", [])
    skills = candidate.get("skills", [])
    edu = candidate.get("education", [])
    
    # 1. Expert skills with 0 duration
    expert_0_dur = [s.get("name") for s in skills if s.get("proficiency") == "expert" and s.get("duration_months", 0) == 0]
    if len(expert_0_dur) > 0:
        return True
        
    # 2. Job duration > elapsed time since start date
    for job in career:
        start_s = job.get("start_date")
        dur = job.get("duration_months", 0)
        start_d = parse_date(start_s)
        if start_d:
            elapsed_months = (current_date.year - start_d.year) * 12 + (current_date.month - start_d.month)
            if dur > elapsed_months + 2:
                return True
                
    # 3. Education timeline contradiction (Started working >= 8 years before university)
    earliest_edu_start = min([e.get("start_year") for e in edu if e.get("start_year")], default=None)
    earliest_job_start = None
    for job in career:
        start_s = job.get("start_date")
        start_d = parse_date(start_s)
        if start_d:
            if earliest_job_start is None or start_d < earliest_job_start:
                earliest_job_start = start_d
    if earliest_edu_start and earliest_job_start:
        if earliest_edu_start - earliest_job_start.year >= 8:
            return True
            
    # 4. Job duration in career history > profile years of experience
    years_exp = profile.get("years_of_experience", 0)
    for job in career:
        dur = job.get("duration_months", 0)
        if dur / 12.0 > years_exp + 0.1:
            return True
            
    return False

def load_candidates_stream(file_path):
    """Generator to load candidates from JSONL file line-by-line (memory-efficient)."""
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)
