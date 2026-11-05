"""Conservative PDF importer: propose rows only, never silently save them."""
import re
from datetime import datetime
from io import BytesIO
from pypdf import PdfReader

DATE_PATTERN = re.compile(r'(?<!\d)(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4})(?!\d)', re.I)
KEYWORDS = re.compile(r'\b(assignment|homework|quiz|exam|midterm|final|project|presentation|deliverable|lab|hw\s*\d+)\b', re.I)

def extract_candidates(upload):
    reader = PdfReader(BytesIO(upload.read()))
    if len(reader.pages) > 30:
        raise ValueError('Please upload a syllabus with 30 pages or fewer.')
    text = '\n'.join(page.extract_text() or '' for page in reader.pages)
    candidates = []
    for raw in text.splitlines():
        line = ' '.join(raw.split())
        if not KEYWORDS.search(line):
            continue
        match = DATE_PATTERN.search(line)
        if not match:
            continue
        date = None
        for fmt in ('%m/%d/%Y','%m/%d/%y','%m-%d-%Y','%m-%d-%y','%B %d, %Y','%b %d, %Y','%B %d %Y','%b %d %Y'):
            try:
                date = datetime.strptime(match.group(1), fmt).date()
                break
            except ValueError:
                continue
        if not date:
            continue
        title = (line[:match.start()] + ' ' + line[match.end():]).strip(' -–:|')[:180]
        if not title:
            continue
        kind = 'exam' if re.search(r'\b(exam|midterm|final)\b',title,re.I) else 'assignment'
        candidate = {'title':title, 'due_date':date.isoformat(), 'task_type':kind}
        if candidate not in candidates:
            candidates.append(candidate)
        if len(candidates) >= 75:
            break
    return candidates
