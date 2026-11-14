"""Deterministic PDF-to-review proposals; no database writes or external services."""
import re
import unicodedata
from datetime import datetime
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PyPdfError

MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 30
MAX_CANDIDATES = 100
MAX_TEXT = 250_000
MONTH = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
DATE_PATTERN = re.compile(
    rf"(?<![\w/:.-])(?:\d{{4}}-\d{{1,2}}-\d{{1,2}}|"
    rf"\d{{1,2}}[/-]\d{{1,2}}(?:[/-](?:\d{{4}}|\d{{2}}))?|"
    rf"{MONTH}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s+\d{{4}})?)(?![\w/:-]|\.\d)",
    re.IGNORECASE,
)
KEYWORDS = re.compile(
    r"\b(assignments?|homework|quizzes|quiz|exams?|midterm|final|projects?|"
    r"presentations?|deliverables?|labs?|hw\s*\d+|deadline|due|orientation|"
    r"holiday|spring break|fall break|no class|no lecture|campus closed)\b", re.IGNORECASE,
)
WEEKDAY = r"(?:Mon(?:day)?|Tue(?:sday)?|Wed(?:nesday)?|Thu(?:rsday)?|Fri(?:day)?|Sat(?:urday)?|Sun(?:day)?)"
DAY_PREFIX = re.compile(rf"^(?:(?:\d{{1,2}}|Finals?|Week\s+\d+)\s+)?{WEEKDAY}\s*,?\s*", re.I)
ITEM_START = re.compile(
    r"^(?:(?:final|midterm|group|individual|course)\s+)?"
    r"(?:assignments?|homework|hw\s*\d+|quizzes|quiz|exams?|midterm|final|projects?|"
    r"presentations?|deliverables?|labs?|orientation)\b", re.I,
)
NUMBERED_ITEM = re.compile(
    r"^(?:assignment|homework|hw|quiz|exam|project|presentation|deliverable|lab(?:\s+report)?)\s*#?\s*\d+\b", re.I,
)
POLICY = re.compile(
    r"\b(polic(?:y|ies)|graded|grading|academic integrity|extra credit|bonus points|"
    r"office hours|prerequisites?|classroom|section\s+\d+|final grades?)\b|"
    r"\b(?:late|early)\s+(?:submission|assignments?|work)\b|\d\s*%", re.I,
)
PROSE = re.compile(
    r"\b(students?|instructor|must|should|will|may|can|are|is|there|each|every|weekly|"
    r"required|points|hours?|minutes?|closed book|closed notes|make.?up)\b", re.I,
)
EVENT = re.compile(r"\b(orientation|holiday|spring break|fall break|no class|no lecture|campus closed|deadline)\b", re.I)
EXAM_REVIEW = re.compile(r"\b(?:exam|midterm|final)\s+(?:review|revision)\b|\breview\s+(?:for|of)\s+(?:the\s+)?(?:exam|midterm|final)\b", re.I)
DEADLINE = re.compile(r"\b(?:due(?:\s+(?:on|by))?|deadline|submit\b.*?\bby)\b", re.I)


def _clean_title(title):
    title = title.strip(" -–—:|•,;")
    if title.startswith("(") and title.endswith(")"):
        title = title[1:-1].strip()
    title = re.sub(r"^\d+[.)]\s+", "", title)
    title = DAY_PREFIX.sub("", title).strip(" -–—:|•,;")
    return " ".join(title.split())


def _is_candidate(title, has_date):
    """A keyword in policy prose is not evidence of an individual task."""
    if POLICY.search(title):
        return False
    if has_date:
        return bool((KEYWORDS.search(title) and (ITEM_START.search(title) or EVENT.search(title) or EXAM_REVIEW.search(title)))
                    or DEADLINE.search(title))
    if len(title.split()) > 14 or PROSE.search(title):
        return False
    # Retain identifiable undated items, not headings or meeting times.
    return bool(NUMBERED_ITEM.search(title)
                or (ITEM_START.search(title) and re.search(r"\b(TBA|TBD|to be announced|to be determined)\b", title, re.I))
                or re.fullmatch(r"(?:final\s+(?:exam|project|presentation)|midterm(?:\s+exam)?)(?:\s+review)?(?:\s*[-–—:]\s*on paper)?", title, re.I))


def _table_start(line):
    """Recognize date/topic or week/date/topic columns in layout-mode text."""
    cells = list(re.finditer(r"\S+(?: \S+)*", line))
    date_index = 0
    if cells and re.fullmatch(r"\d{1,2}|Finals?|Week\s+\d+", cells[0].group(), re.I):
        date_index = 1
    if len(cells) <= date_index + 1:
        return None
    when = cells[date_index].group()
    if not DATE_PATTERN.match(re.sub(rf"^{WEEKDAY}\s*,?\s*", "", when, flags=re.I)):
        return None
    return cells[date_index].start(), cells[date_index + 1].start()


def _rows(text):
    """Reconstruct contiguous table cells before flattening PDF whitespace."""
    lines = text.expandtabs(4).splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        columns = _table_start(line)
        if columns:
            date_start, title_start = columns
            when, title = [], []
            while True:
                when.append(lines[index][date_start:title_start].strip())
                title.append(lines[index][title_start:].strip())
                index += 1
                if index >= len(lines) or not lines[index].strip() or _table_start(lines[index]):
                    break
                indent = len(lines[index]) - len(lines[index].lstrip())
                date_continuation = re.match(r"\s*[(–—-]|\s*\d{1,2}:\d{2}", lines[index])
                if indent < date_start or (date_start == 0 and indent < title_start and not date_continuation):
                    break
            when = " ".join(part for part in when if part)
            title = " ".join(part for part in title if part)
            # A closure note in the date cell has its own date, not the lecture's.
            for annotation in re.findall(r"\(([^()]*)\)", when):
                if DATE_PATTERN.search(annotation) and EVENT.search(annotation):
                    yield annotation, None
                    when = when.replace(f"({annotation})", "")
            yield f"{when.strip()} | {title}", title
            continue
        line = " ".join(line.split())
        index += 1
        if not line:
            continue
        # Only pair adjacent standalone dates and plausible titles. Never carry
        # a lecture date across unrelated rows or a blank line.
        if index < len(lines):
            following = " ".join(lines[index].split())
            if ((_is_candidate(_clean_title(line), False) and DATE_PATTERN.fullmatch(following))
                    or (DATE_PATTERN.fullmatch(line) and _is_candidate(_clean_title(following), False))):
                line = f"{line} {following}"
                index += 1
        yield line, None


class SyllabusParseError(ValueError):
    pass


def _parse_date(value, year):
    value = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", value, flags=re.I)
    value = re.sub(r"\bSept\b", "Sep", value, flags=re.I).replace(".", "")
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m/%d/%y", "%m-%d-%Y", "%m-%d-%y",
                "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(value, fmt).date(), False
        except ValueError:
            pass
    if year is not None:
        for fmt in ("%m/%d", "%m-%d", "%B %d", "%b %d"):
            try:
                return datetime.strptime(f"{value} {year}", f"{fmt} %Y").date(), True
            except ValueError:
                pass
    return None, False


def _kind(title):
    if EXAM_REVIEW.search(title):
        return "event"
    for pattern, kind in (
        (r"\b(exams?|midterm)\b", "exam"), (r"\b(quiz|quizzes)\b", "quiz"),
        (r"\bprojects?\b", "project"), (r"\blabs?\b", "lab"),
        (r"\bpresentations?\b", "presentation"),
        (r"\bfinal\b", "exam"),
        (r"\b(orientation|holiday|break|no class|no lecture|campus closed|deadline)\b", "event"),
    ):
        if re.search(pattern, title, re.I):
            return kind
    return "assignment"


def parse_text(text, year=None, page=1):
    """Propose individual tasks/events, retaining uncertainty for human review."""
    text = unicodedata.normalize("NFKC", text)
    candidates = []
    for line, table_title in _rows(text):
        matches = list(DATE_PATTERN.finditer(line))
        title = _clean_title(table_title if table_title is not None else DATE_PATTERN.sub("", line))
        if not _is_candidate(title, bool(matches)):
            continue
        warnings = []
        due_date = None
        conflicting_weekday = False
        if len(matches) == 1:
            match = matches[0]
            compact_range = re.match(r"\s*[-–—]\s*\d{1,2}\b", line[match.end():])
            due_date, inferred_year = (None, False) if compact_range else _parse_date(match.group(), year)
            if due_date:
                if inferred_year:
                    warnings.append(f"Year assumed from course ({year}); check this date.")
                elif year and due_date.year != year:
                    warnings.append("Date is outside the course year; check this date.")
                weekday = re.search(rf"\b({WEEKDAY})\s*,?\s*$", line[:match.start()], re.I)
                if weekday and weekday.group(1)[:3].lower() != due_date.strftime("%a").lower():
                    conflicting_weekday = True
                    warnings.append(f"The syllabus says {weekday.group(1)}, but {due_date.isoformat()} is {due_date.strftime('%A')}. Confirm with your instructor before including this item.")
            else:
                warnings.append("Unrecognized, invalid, or ranged date; enter the correct date before including this row.")
        elif len(matches) > 1:
            warnings.append("Multiple dates found; enter the correct deadline before including this row.")
        else:
            warnings.append("No supported date found; enter a date before including this row.")
        if re.search(r"\d{1,2}:\d{2}|\b[ap]\.?m\.?\b", line, re.I):
            warnings.append("Only the date is imported. Check the original syllabus for the time.")
        if len(title) > 200:
            warnings.append("Title shortened; check the original text below.")
        candidates.append({
            "title": title[:200], "due_date": due_date.isoformat() if due_date else "",
            "item_type": _kind(title), "source_text": line, "source_page": page,
            "warnings": warnings, "include": due_date is not None and not conflicting_weekday,
        })
    return candidates


def extract_candidates(upload, year=None):
    upload.seek(0)
    data = upload.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SyllabusParseError("Choose a PDF no larger than 10 MB.")
    if not data.startswith(b"%PDF-"):
        raise SyllabusParseError("This does not appear to be a valid PDF.")
    candidates, seen = [], set()
    text_size = 0
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise SyllabusParseError("Password-protected PDFs are not supported. Upload an unlocked copy.")
        if len(reader.pages) > MAX_PAGES:
            raise SyllabusParseError("Please upload a syllabus with 30 pages or fewer.")
        for number, page in enumerate(reader.pages, start=1):
            contents = page.get_contents()
            if contents is not None and len(contents.get_data()) > 5 * 1024 * 1024:
                raise SyllabusParseError("This PDF page is too complex. Export a simpler text-based PDF.")
            text = page.extract_text(extraction_mode="layout") or ""
            text_size += len(text.strip())
            if text_size > MAX_TEXT:
                raise SyllabusParseError("This PDF contains too much text. Upload only the syllabus pages.")
            for candidate in parse_text(text, year=year, page=number):
                key = (candidate["title"].casefold(), candidate["due_date"], candidate["item_type"])
                if key not in seen:
                    seen.add(key)
                    candidates.append(candidate)
                if len(candidates) > MAX_CANDIDATES:
                    raise SyllabusParseError("More than 100 possible items found. Upload a shorter syllabus section.")
    except SyllabusParseError:
        raise
    except (PyPdfError, ValueError, TypeError, KeyError, IndexError, RecursionError, OSError) as exc:
        raise SyllabusParseError("The PDF could not be read. Try exporting it as a new text-based PDF.") from exc
    if not text_size:
        raise SyllabusParseError("No readable text found. Scanned/image PDFs need OCR before uploading.")
    return candidates
