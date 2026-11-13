"""Deterministic PDF-to-review proposals; no database writes or external services."""
import re
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
    rf"(?<![\w/.-])(?:\d{{4}}-\d{{1,2}}-\d{{1,2}}|"
    rf"\d{{1,2}}[/-]\d{{1,2}}(?:[/-](?:\d{{4}}|\d{{2}}))?|"
    rf"{MONTH}\.?\s+\d{{1,2}}(?:st|nd|rd|th)?(?:,?\s+\d{{4}})?)(?![\w/-]|\.\d)",
    re.IGNORECASE,
)
KEYWORDS = re.compile(
    r"\b(assignments?|homework|quizzes|quiz|exams?|midterm|final|projects?|"
    r"presentations?|deliverables?|labs?|hw\s*\d+|deadline|due|orientation|"
    r"holiday|spring break|fall break|no class)\b", re.IGNORECASE,
)


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
    for pattern, kind in (
        (r"\b(exams?|midterm)\b", "exam"), (r"\b(quiz|quizzes)\b", "quiz"),
        (r"\bprojects?\b", "project"), (r"\blabs?\b", "lab"),
        (r"\bpresentations?\b", "presentation"),
        (r"\bfinal\b", "exam"),
        (r"\b(orientation|holiday|break|no class|deadline)\b", "event"),
    ):
        if re.search(pattern, title, re.I):
            return kind
    return "assignment"


def parse_text(text, year=None, page=1):
    """Keep uncertain rows for review; never choose between multiple dates."""
    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    candidates = []
    index = 0
    while index < len(lines):
        line = lines[index]
        # Handle a title and a date on adjacent lines, in either order. Do not
        # carry a date across unrelated rows, columns, or page boundaries.
        if index + 1 < len(lines):
            following = lines[index + 1]
            if ((KEYWORDS.search(line) and not DATE_PATTERN.search(line) and DATE_PATTERN.fullmatch(following))
                    or (DATE_PATTERN.fullmatch(line) and KEYWORDS.search(following) and not DATE_PATTERN.search(following))):
                line = f"{line} {following}"
                index += 1
        index += 1
        if not KEYWORDS.search(line):
            continue
        matches = list(DATE_PATTERN.finditer(line))
        if not matches and re.search(r"\d\s*%", line):
            continue
        warnings = []
        due_date = None
        title = line
        if len(matches) == 1:
            match = matches[0]
            compact_range = re.match(r"\s*[-–—]\s*\d{1,2}\b", line[match.end():])
            due_date, inferred_year = (None, False) if compact_range else _parse_date(match.group(), year)
            if due_date:
                title = (line[:match.start()] + " " + line[match.end():]).strip(" -–—:|•")
                if inferred_year:
                    warnings.append(f"Year assumed from course ({year}); check this date.")
                elif year and due_date.year != year:
                    warnings.append("Date is outside the course year; check this date.")
            else:
                warnings.append("Unrecognized, invalid, or ranged date; enter the correct date before including this row.")
        elif len(matches) > 1:
            warnings.append("Multiple dates found; enter the correct deadline before including this row.")
        else:
            warnings.append("No supported date found; enter a date before including this row.")
        if re.search(r"\d{1,2}:\d{2}|\b[ap]\.?m\.?\b", line, re.I):
            warnings.append("Only the date is imported. Check the original syllabus for the time.")
        title = " ".join(title.split()) or line
        if len(title) > 200:
            warnings.append("Title shortened; check the original text below.")
        candidates.append({
            "title": title[:200], "due_date": due_date.isoformat() if due_date else "",
            "item_type": _kind(line), "source_text": line, "source_page": page,
            "warnings": warnings, "include": due_date is not None,
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
            text = page.extract_text() or ""
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
