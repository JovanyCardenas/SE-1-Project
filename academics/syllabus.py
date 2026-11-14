"""Local, structured syllabus analysis. No network calls or generated facts.

Sections, table headers, and source evidence decide what a row means. Missing
dates remain missing; descriptions/counts/weights are not calendar deadlines.
"""
import re
import unicodedata
from datetime import datetime
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from .parser import (
    DATE_PATTERN, MONTH, WEEKDAY, MAX_BYTES, MAX_PAGES, MAX_TEXT,
    MAX_CANDIDATES, SyllabusParseError, _kind, _parse_date, parse_text,
)

VERSION = "local-structured-2"
DAY_FIRST = rf"\d{{1,2}}(?:st|nd|rd|th)?\s+{MONTH}\.?(?:,?\s+\d{{4}})?"
DATES = re.compile(rf"{DATE_PATTERN.pattern}|(?<!\w)(?:{DAY_FIRST})(?!\w)", re.I)
TIME = re.compile(r"\b\d{1,2}(?::\d{2})?\s*(?:[ap]\.?m\.?)?(?:\s*[-–—]|\s+to)?\s*\d{0,2}(?::\d{2})?\s*[ap]\.?m\.?\b|\b\d{1,2}:\d{2}\b", re.I)
ASSESSMENT = re.compile(r"\b(?:homework|hw\s*\d+|assignments?|quizzes|quiz|examinations?|exams?|midterms?|finals?|projects?|essays?|papers?|reports?|labs?|presentations?|problem sets?|deliverables?|portfolios?)\b", re.I)
POLICY = re.compile(r"\b(?:polic(?:y|ies)|graded|grading scale|academic integrity|plagiarism|late work|late (?:submissions?|assignments?)|bonus points|closed book|closed notes|no credit|make.?up|students (?:who|not|must|should)|final grades?|must be handwritten|must submit|should be|will be graded)\b", re.I)
PENDING = re.compile(r"\b(?:TBA|TBD|to be announced|to be determined|not yet scheduled)\b", re.I)
RELATIVE = re.compile(r"\b(?:week\s+\d+|every\s+\w+|weekly|after\s+\w+|before\s+\w+|next\s+\w+|last\s+\w+)\b", re.I)
NEGATED_EXAM = re.compile(r"\bno\s+(?:written\s+)?(final\s+)?exam(?:ination)?\b", re.I)
CLOSURE = re.compile(r"\b(?:no class|no lecture|campus closed|holiday|spring break|fall break|orientation|last day|withdraw|drop deadline)\b", re.I)
REVIEW = re.compile(r"\b(?:exam|midterm|final)\s+(?:review|revision)\b|\breview\s+(?:for|of)\s+(?:the\s+)?(?:exam|midterm|final)\b", re.I)
NUMBER = r"(?:\d+|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|a|an)"
COUNTS = re.compile(rf"\b({NUMBER})\s+((?:homework|lab|class|group|final|midterm)\s+)?(assignments?|quizzes|exams?|midterms?|projects?|labs?|essays?|papers?|reports?)\b", re.I)
NUMBER_WORDS = {word: i for i, word in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}
NUMBER_WORDS.update(a=1, an=1)


def compact(text):
    text = re.sub(r"\b(mid)[ -]*(term)(?=\d|\b)", lambda match: match.group(1) + match.group(2) + " ", unicodedata.normalize("NFKC", text), flags=re.I)
    return " ".join(text.split())


def section_kind(line):
    title = re.sub(r"^[^\w]+", "", compact(line)).strip(" :").lower()
    if re.match(r"^(?:course|class|tentative|weekly)\s+(?:schedule|calendar)\b", title):
        return "schedule"
    if len(title) > 85 or len(title.split()) > 10:
        return None
    if re.search(r"\bdue dates\b", title) and not DATES.search(title):
        return "assessments"
    for pattern, kind in (
        (r"(?:.*\b)?(?:schedule|calendar|weekly outline|course outline|tentative outline)(?:\s+.*)?", "schedule"),
        (r"(?:course\s+)?(?:requirements and assignments|assignments|assessments|assessment details|coursework|assessment overview|major assignments|examinations|exams)", "assessments"),
        (r"(?:.*\b)?(?:grading|grade breakdown|assessment weights|evaluation)(?:\s+.*)?", "grading"),
        (r".*\b(?:policies|policy|classroom protocols?|academic integrity|plagiarism|disabilities|academic dishonesty)\b.*", "policies"),
        (r"(?:contact information|instructor information|course information|meeting times)", "information"),
        (r"(?:course learning outcomes.*|course materials|learning objectives|textbooks|course description.*)", "information"),
    ):
        if re.fullmatch(pattern, title):
            return kind
    return None


def date_details(text, year, date_order="MDY"):
    matches = list(DATES.finditer(text))
    result = {"due_date": "", "date_text": compact(text), "date_status": "unspecified", "warnings": []}
    without_weeks = re.sub(r"\bWeeks?\s+\d+(?:\s*[-–—]\s*\d+)?", "", text, flags=re.I)
    if without_weeks != text and not DATES.search(without_weeks):
        result["date_status"] = "relative"
        result["warnings"].append("Week number or range retained as written; no calendar date was invented.")
        return result
    if re.search(rf"\b{MONTH}\.?\s+\d{{1,2}}\s*[-–—]\s*\d{{1,2}}\b", text, re.I):
        result["date_status"] = "range"
        result["warnings"].append("Date range retained as written; choose a single date only if appropriate.")
        return result
    if not matches:
        if RELATIVE.search(text):
            result["date_status"] = "relative"
            result["warnings"].append("Relative or recurring date retained as written; no calendar date was invented.")
        else:
            result["warnings"].append("No calendar date supplied. This item can be saved as undated.")
        return result
    # An explicit deadline label can disambiguate a release date from a due date.
    deadline = re.search(r"\b(?:due(?:\s+(?:on|by))?|deadline|submit\b.*?\bby)\s*[:\-]?\s*$", text[:matches[-1].start()], re.I)
    if len(matches) > 1 and deadline:
        matches = [matches[-1]]
    if len(matches) != 1:
        result["date_status"] = "ambiguous"
        result["warnings"].append("Several dates appear here. Confirm the intended date, or retain the item without a calendar date.")
        return result
    match = matches[0]
    raw = match.group()
    if re.match(r"\s*[-–—]\s*\d{1,2}(?![:\d])\b", text[match.end():]):
        result["date_status"] = "range"
        result["warnings"].append("Date range retained as written; choose a single date only if appropriate.")
        return result
    cleaned = re.sub(r"(\d)(st|nd|rd|th)\b", r"\1", raw, flags=re.I)
    cleaned = re.sub(r"\bSept\b", "Sep", cleaned, flags=re.I).replace(".", "")
    parsed, inferred = None, False
    formats = ["%d %B %Y", "%d %b %Y", "%d %B, %Y", "%d %b, %Y"]
    if date_order == "DMY" and re.fullmatch(r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?", raw):
        formats = ["%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y"]
        short_formats = ["%d/%m", "%d-%m"]
    else:
        parsed, inferred = _parse_date(raw, year)
        short_formats = ["%d %B", "%d %b"]
    for fmt in formats:
        if parsed:
            break
        try:
            parsed = datetime.strptime(cleaned, fmt).date()
        except ValueError:
            pass
    if not parsed and year:
        for fmt in short_formats:
            try:
                parsed = datetime.strptime(f"{cleaned} {year}", f"{fmt} %Y").date()
                inferred = True
                break
            except ValueError:
                pass
    if not parsed:
        result["date_status"] = "invalid"
        result["warnings"].append("The written date could not be validated. Correct it or leave the calendar date empty.")
        return result
    result.update(due_date=parsed.isoformat(), date_status="inferred_year" if inferred else "explicit")
    if inferred:
        result["warnings"].append(f"Year assumed from course ({year}); check this date.")
    elif year and parsed.year != year:
        result["warnings"].append("Date is outside the selected course year; check this date.")
    weekday = re.search(rf"\b({WEEKDAY})\s*,?\s*$", text[:match.start()], re.I)
    if weekday and weekday.group(1)[:3].lower() != parsed.strftime("%a").lower():
        result["date_status"] = "conflict"
        result["warnings"].append(f"The syllabus says {weekday.group(1)}, but {parsed.isoformat()} is {parsed.strftime('%A')}. Confirm the date.")
    return result


def cells(line):
    if "|" in line:
        return [(part.strip(), start) for start, part in _pipe_cells(line) if part.strip()]
    return [(m.group(), m.start()) for m in re.finditer(r"\S+(?: \S+)*", line.expandtabs(4))]


def _pipe_cells(line):
    start = 0
    for part in line.split("|"):
        yield start, part
        start += len(part) + 1


def header_role(value):
    value = compact(value).lower().strip(" :")
    if re.fullmatch(r"due(?: date)?|deadline|due on|timing / details|details", value):
        return "due"
    if value in ("date", "dates", "day", "when"):
        return "date"
    if value in ("week", "wk", "session", "lecture"):
        return "week"
    if value in ("weight", "weight (%)", "%", "percentage", "percent", "weighting"):
        return "weight"
    if value in ("points", "marks", "points possible"):
        return "points"
    if value in ("topic", "topics", "content", "class topic", "topics covered"):
        return "topic"
    if value in ("readings", "reading", "chapter", "chapters"):
        return "reading"
    if value in ("assignments due", "assignment due", "work due"):
        return "assessment_due"
    if value in ("assignment", "assignments", "assessment", "task", "deliverable", "activity", "item", "component", "category", "grading component"):
        return "assessment"
    return None


def table_header(line):
    parts = cells(line)
    roles = [(header_role(value), start) for value, start in parts]
    if len(roles) >= 2 and all(role for role, _ in roles):
        return roles
    return None


def infer_columns(line):
    parts = cells(line)
    if len(parts) < 2:
        return None
    if re.fullmatch(r"\d+(?:\.\d+)?%", parts[0][0]):
        return [("weight", parts[0][1]), ("assessment", parts[1][1])]
    roles = []
    for i, (value, start) in enumerate(parts):
        if i == 0 and re.fullmatch(r"\d{1,2}|Finals?|Week\s+\d+", value, re.I):
            roles.append(("week", start))
        elif DATES.search(value) and not ASSESSMENT.search(value):
            roles.append(("date", start))
        else:
            roles.append(("topic", start))
    if sum(role == "date" for role, _ in roles) == 1 and any(role == "topic" for role, _ in roles):
        return roles
    return None


def split_columns(line, columns):
    if "|" in line:
        values = [part.strip() for part in line.strip(" |").split("|")]
        return {role: values[i] if i < len(values) else "" for i, (role, _) in enumerate(columns)}
    values = {}
    for i, (role, start) in enumerate(columns):
        end = columns[i + 1][1] if i + 1 < len(columns) else len(line)
        values[role] = compact(line[0 if i == 0 else start:end])
    return values


def evidence(text, page, **values):
    return {**values, "source_text": compact(text), "source_page": page}


class Analyzer:
    def __init__(self, year=None, date_order="MDY"):
        self.year = year
        self.date_order = date_order
        self.section = "unknown"
        self.no_final_exam = False
        self.report = {"parser_version": VERSION, "items": [], "grading": [], "assessment_overview": [],
                       "meetings": [], "course_information": [], "policies": [], "warnings": [], "pages_without_text": []}

    def item(self, title, when, source, page, *, schedule=False, warnings=(), reading=""):
        title = compact(title).strip(" -–—:|•●\uf0b7,;")
        title = re.sub(r"^\d+[.)]\s+", "", title)
        if not title or title.lower() in ("none", "n/a", "tba", "tbd", "-", "—"):
            return
        if POLICY.search(title) and not ASSESSMENT.search(title):
            return
        scheduled_assessment = re.search(r"\b(?:exams?|midterms?|finals?|(?:quiz|homework|assignment|lab|project)\s*#?\s*\d+|due)\b", title, re.I)
        kind = "class_session" if schedule and not scheduled_assessment else _kind(title)
        if REVIEW.search(title) or CLOSURE.search(title):
            kind = "event"
        elif re.search(r"\b(?:essays?|papers?|reports?|problem sets?|portfolios?)\b", title, re.I) and kind == "assignment":
            kind = "assignment"
        details = date_details(when, self.year, self.date_order)
        if len(title) > 200:
            details["warnings"].append("Title shortened; the complete text is retained in the source excerpt.")
        if warnings:
            details["warnings"].extend(warnings)
        times = list(dict.fromkeys(m.group().strip() for m in TIME.finditer(source)))
        category = "class_schedule" if kind == "class_session" else "course_event" if kind == "event" else "assessment"
        self.report["items"].append(evidence(source, page, title=title[:200], item_type=kind, category=category,
            category_label={"class_schedule": "Class schedule", "course_event": "Course event", "assessment": "Assessment"}[category],
            **details, time_text="; ".join(times), reading_text=reading, section=self.section,
            include=bool(details["due_date"]) and details["date_status"] != "conflict"))

    def overview(self, text, page):
        found = False
        for match in COUNTS.finditer(text):
            raw = match.group(1).lower()
            count = int(raw) if raw.isdecimal() else NUMBER_WORDS[raw]
            label = compact((match.group(2) or "") + match.group(3))
            self.report["assessment_overview"].append(evidence(text, page, label=label, count=count))
            found = True
        if (not found and ASSESSMENT.search(text) and re.search(r"\b(?:every|weekly|each week)\b", text, re.I)
                and not re.search(r"\b(?:quiz|homework|assignment|exam|lab|project)\s*#?\s*\d+", text, re.I)):
            self.report["assessment_overview"].append(evidence(text, page, label=text, count=None))
            found = True
        return found

    def table_row(self, row, source, page):
        label = row.get("assessment", row.get("topic", ""))
        if "weight" in row or "points" in row:
            weight = re.search(r"\d+(?:\.\d+)?", row.get("weight", ""))
            points = re.search(r"\d+(?:\.\d+)?", row.get("points", ""))
            if re.fullmatch(r"Total|[ABCDF][+\-]?|[ABCDF]\s+(?:plus|minus)", label, re.I):
                return
            details = row.get("due", "")
            split = re.search(r"\b(?:Approximately|Each\s+project|Students\s+who|Week\s+\d+|" + WEEKDAY + r",|" + MONTH + r"\s+\d+)", label, re.I)
            if split:
                details = label[split.start():]
                label = label[:split.start()].strip()
            if label and (weight or points):
                self.report["grading"].append(evidence(source, page, label=label,
                    weight=float(weight.group()) if weight else None, points=float(points.group()) if points else None))
                if details and ASSESSMENT.search(label) and not re.search(r"\b(?:combined|participation)\b", label, re.I):
                    self.item(label, details, source, page)
            return
        when = row.get("due") or row.get("date") or row.get("week", "")
        if row.get("week") and not DATES.search(when) and "week" not in when.lower():
            when = "Week " + when
        # Parenthetical holiday dates belong to the closure, not that day's lecture.
        for note in re.findall(r"\(([^()]*)\)", when):
            if CLOSURE.search(note) and DATES.search(note):
                title = DATES.sub("", note)
                title = re.sub(rf"^{WEEKDAY}\s*,?\s*", "", title, flags=re.I)
                self.item(title, note, note, page)
                when = when.replace(f"({note})", "")
        topic = row.get("topic")
        if ASSESSMENT.search(row.get("week", "")) and not ASSESSMENT.search(topic or ""):
            topic = row["week"] + (": " + topic if topic else "")
        if topic and DATES.search(topic):
            when += " " + topic
        if topic:
            self.item(topic, when, source, page, schedule=True, reading=row.get("reading", ""))
        assessment = row.get("assessment_due") or row.get("assessment")
        if assessment:
            uncertain = topic and "due" not in row and "assessment_due" not in row and not re.search(r"\bdue\b", assessment, re.I)
            self.item(assessment, "" if uncertain else when, source, page,
                      warnings=["Listed beside a class date, but not labeled due. Confirm the deadline."] if uncertain else [])

    def paragraph(self, text, page):
        text = compact(text).strip(" •●\uf0b7")
        if not text:
            return
        # Ignore repeated running page numbers and document metadata dates.
        if re.fullmatch(r"(?:page\s+)?\d+(?:\s+of\s+\d+)?", text, re.I):
            return
        info = re.match(r"^(Instructor(?:\(s\))?|Professor|Email|Office(?: Hours| Location)?|Prerequisites?|Course Code|Course Title|Classroom)\s*:\s*(.+)", text, re.I)
        if info:
            self.report["course_information"].append(evidence(text, page, label=info.group(1), value=info.group(2)))
            return
        if (re.search(r"\b(?:Mon(?:day)?|Tue(?:sday)?|Wed(?:nesday)?|Thu(?:rsday)?|Fri(?:day)?|MW|MWF|TTh)\b", text, re.I)
                and TIME.search(text) and not DATES.search(text)):
            self.report["meetings"].append(evidence(text, page, label=text))
            return
        negated = NEGATED_EXAM.search(text)
        if negated:
            self.no_final_exam = self.no_final_exam or bool(negated.group(1))
            self.report["assessment_overview"].append(evidence(text, page, label="Final exam" if negated.group(1) else "Written exam", count=0))
            return
        week = re.match(r"Weeks?\s+(\d+(?:\s*[-–—]\s*\d+)?)\s*:\s*(.+)", text, re.I)
        if week and self.section == "schedule":
            parts = re.split(r"\b(?:o\s+)?Assessment\s*:\s*", week.group(2), flags=re.I)
            self.item(parts[0], "Week " + week.group(1), text, page, schedule=True)
            for task in parts[1:]:
                self.item(task, "Week " + week.group(1), text, page)
            return
        overview = self.overview(text, page)
        explicit_submission = DATES.search(text) and re.search(r"\bmust submit\b.*\b(?:by|on)\b", text, re.I)
        if self.section == "policies" or (POLICY.search(text) and not explicit_submission):
            self.report["policies"].append(evidence(text, page, label=text[:100]))
            return
        weight = re.match(r"^(.+?)\s*[:–—-]?\s+(\d+(?:\.\d+)?)\s*%(.*)$", text)
        if weight and not DATES.search(text) and (ASSESSMENT.search(weight.group(1)) or self.section == "grading"):
            if re.match(r"^(?:Total|Note|Ex\b|Rounding|At least)\b", weight.group(1), re.I):
                self.report["policies"].append(evidence(text, page, label=text[:100]))
                return
            self.report["grading"].append(evidence(text, page, label=weight.group(1), weight=float(weight.group(2)), points=None))
            return
        if overview and not DATES.search(text):
            return
        # A paragraph may describe two independently dated assessments.
        sentences = re.split(r"(?<=[.;])\s+(?=(?:The\s+)?(?:final|midterm|exam|quiz|project|assignment|homework|paper|essay)\b)", text, flags=re.I)
        if len(sentences) > 1:
            for sentence in sentences:
                self.paragraph(sentence, page)
            return
        matches = list(DATES.finditer(text))
        assessment = ASSESSMENT.search(text)
        if matches and (assessment or CLOSURE.search(text) or re.search(r"\b(?:due|submit|deadline)\b", text, re.I)):
            title = DATES.sub("", text)
            title = re.sub(rf"^(?:\d+\s+)?{WEEKDAY}\s*,?\s*", "", title, flags=re.I)
            if assessment and assessment.start() > 0 and re.match(r"^(?:The|There|We|You|A|An)\b", title, re.I):
                title = title[ASSESSMENT.search(title).start():]
            title = re.sub(r"\s+(?:assigned|released|will be held|will take place|takes place|is scheduled|is due|due)\b.*$", "", title, flags=re.I)
            title = re.sub(r"\s+(?:on|by|at)\s*[:,.\-]?\s*$", "", title, flags=re.I).strip(" .;")
            self.item(title, text, text, page)
            return
        # Preserve concrete undated assessments and named tasks under assessment headings.
        concrete_start = re.match(r"^(?:(?:final|midterm|term|research|design|individual|group|written)\s+)?(?:examination|exam|midterm|final|project|essay|paper|report|quiz|homework|assignment|lab|presentation|portfolio|problem set)\b", text, re.I)
        if (assessment and concrete_start and not re.search(r"\b(?:students|will|must|should|their|except|include|posted)\b", text, re.I)
                and (self.section == "assessments" or PENDING.search(text) or RELATIVE.search(text)) and len(text.split()) < 24):
            self.item(text, text, text, page)
            return
        for candidate in parse_text(text, self.year, page):
            self.item(candidate["title"], text, text, page)

    def page(self, text, page):
        text = unicodedata.normalize("NFKC", text).expandtabs(4)
        columns, pending, sources = None, None, []

        def flush():
            nonlocal pending, sources
            if pending:
                self.table_row(pending, " | ".join(sources), page)
            pending, sources = None, []

        lines = text.splitlines()
        index = 0
        while index < len(lines):
            line = lines[index]
            index += 1
            if not line.strip():
                flush()
                continue
            heading = section_kind(line)
            header = table_header(line)
            inferred = infer_columns(line) if self.section != "policies" else None
            if columns and columns[0][0] == "week" and not any(role in ("date", "due") for role, _ in columns):
                parts = cells(line)
                if len(parts) >= 2 and re.fullmatch(r"\d+(?:\s*[-–—]\s*\d+)?", parts[0][0]):
                    # Under a Lecture/Week heading, 1-4 is a sequence range,
                    # not January 4. Allow the title column's indentation to vary.
                    inferred = [("week", parts[0][1]), ("topic", parts[1][1])]
            if header:
                flush()
                columns = header
                continue
            if heading:
                flush()
                self.section = heading
                columns = None
                continue
            # Check continuation against the existing columns before inferring a
            # new table. A parenthetical closure date in a wrapped date cell must
            # not become the date of the neighboring wrapped lecture title.
            if columns and pending:
                continuation = split_columns(line, columns)
                if not continuation.get(columns[0][0]):
                    for key, value in continuation.items():
                        pending[key] = compact(pending.get(key, "") + " " + value)
                    sources.append(compact(line))
                    continue
            weak_header = columns and all(role in ("week", "date", "topic") for role, _ in columns)
            if inferred and (columns is None or weak_header or any(role in ("week", "weight") for role, _ in inferred)):
                flush()
                columns = inferred
            if columns:
                row = split_columns(line, columns)
                first_role = columns[0][0]
                if pending and not row.get(first_role):
                    for key, value in row.items():
                        pending[key] = compact(pending.get(key, "") + " " + value)
                    sources.append(compact(line))
                    continue
                # Use the table only while rows still have a date/week/weight or
                # a named assessment in a header-identified assessment column.
                valid = (DATES.search(row.get("date", "") + " " + row.get("due", ""))
                         or RELATIVE.search(row.get("date", "") + " " + row.get("due", ""))
                         or re.fullmatch(r"\d{1,2}(?:\s*[-–—]\s*\d{1,2})?|Week\s+\d+|Finals?", row.get("week", ""), re.I)
                         or ASSESSMENT.search(row.get("week", ""))
                         or re.search(r"\d", row.get("weight", "") + row.get("points", ""))
                         or (row.get("assessment") and ("due" in row or PENDING.search(" ".join(row.values())))))
                if valid:
                    flush()
                    pending, sources = row, [compact(line)]
                    continue
                flush()
                if not (self.section == "schedule" and first_role == "week"):
                    columns = None
            # Join wrapped prose, but stop at headings, table rows, blank lines,
            # bullets, or the beginning of a new identifiable assessment.
            paragraph = compact(line)
            while index < len(lines) and lines[index].strip():
                following = compact(lines[index])
                weight_continuation = (self.section == "grading" and "%" not in paragraph and "%" in following
                                       and (following.startswith("(") or following[:1].islower()))
                if (section_kind(following) or table_header(lines[index]) or infer_columns(lines[index])
                        or re.match(r"^[•●\uf0b7*–—-]|^\d+[.)]\s|^(?:Weeks?\s+\d|Homework|Assignments?|Quiz(?:zes)?|Exams?|Final|Midterm|Labs?|Projects?|Presentations?|Instructor|Professor|Email|Office|Class|Lecture|Grading)\b", following, re.I)
                        or DATES.search(following) or (re.search(r"\d\s*%", following) and not weight_continuation)):
                    break
                if DATES.search(paragraph) or PENDING.search(paragraph):
                    break
                paragraph += " " + following
                index += 1
            # A title and standalone date on neighboring lines are one item.
            if index < len(lines) and ASSESSMENT.search(paragraph) and DATES.fullmatch(compact(lines[index])):
                paragraph += " " + compact(lines[index])
                index += 1
            self.paragraph(paragraph, page)
        flush()

    def finish(self):
        if self.no_final_exam:
            kept = []
            for item in self.report["items"]:
                if item["item_type"] == "exam" and re.search(r"\bfinal\b", item["title"], re.I):
                    if not item["due_date"]:
                        continue
                    item["include"] = False
                    item["warnings"].append("Another passage says there is no final exam. Resolve this conflict before including the item.")
                kept.append(item)
            self.report["items"] = kept
        for group in ("items", "grading", "assessment_overview", "meetings", "course_information", "policies"):
            unique, seen = [], set()
            for entry in self.report[group]:
                if group == "items":
                    key = (entry["title"].casefold(), entry["due_date"], entry["date_text"] if not entry["due_date"] else "", entry["item_type"])
                else:
                    key = tuple((key, str(value).casefold()) for key, value in entry.items() if key not in ("source_text", "source_page"))
                if key not in seen:
                    unique.append(entry)
                    seen.add(key)
            self.report[group] = unique
        # An assessment heading is not a second undated assessment when a later
        # passage supplies its date. Only merge narrowly equivalent exam names.
        def exam_key(item):
            title = item["title"].lower().strip(" .")
            title = re.sub(r"\bexaminations?\b", "exam", title)
            title = re.sub(r"\s+for the class$", "", title)
            return title if re.fullmatch(r"(?:final exam|midterm(?: exam)?(?: \d+)?)", title) else None

        dated_exams = {exam_key(item) for item in self.report["items"] if item["due_date"] and exam_key(item)}
        self.report["items"] = [item for item in self.report["items"] if item["due_date"] or exam_key(item) not in dated_exams]
        if len(self.report["items"]) > MAX_CANDIDATES:
            raise SyllabusParseError(f"More than {MAX_CANDIDATES} items found. Upload smaller syllabus sections.")
        self.report["coverage"] = {
            "dated_items": sum(bool(item["due_date"]) for item in self.report["items"]),
            "undated_items": sum(not item["due_date"] for item in self.report["items"]),
            "class_sessions": sum(item["item_type"] == "class_session" for item in self.report["items"]),
        }
        if not self.report["items"]:
            self.report["warnings"].append("No individual tasks or dated schedule rows were identified. This does not prove the document contains none; review the other information and original syllabus.")
        return self.report


def analyze_pages(pages, year=None, date_order="MDY"):
    if date_order not in ("MDY", "DMY"):
        raise ValueError("date_order must be MDY or DMY")
    analyzer = Analyzer(year, date_order)
    for number, text in enumerate(pages, 1):
        if not text.strip():
            analyzer.report["pages_without_text"].append(number)
        analyzer.page(text, number)
    if analyzer.report["pages_without_text"]:
        analyzer.report["warnings"].append("Some pages contain no readable text. Scanned pages need local OCR; extraction may be incomplete.")
    return analyzer.finish()


def analyze_syllabus(upload, year=None, date_order="MDY"):
    upload.seek(0)
    data = upload.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise SyllabusParseError("Choose a PDF no larger than 10 MB.")
    if not data.startswith(b"%PDF-"):
        raise SyllabusParseError("This does not appear to be a valid PDF.")
    pages = []
    try:
        reader = PdfReader(BytesIO(data))
        if reader.is_encrypted:
            raise SyllabusParseError("Password-protected PDFs are not supported. Upload an unlocked copy.")
        if len(reader.pages) > MAX_PAGES:
            raise SyllabusParseError("Please upload a syllabus with 30 pages or fewer.")
        total = 0
        for page in reader.pages:
            contents = page.get_contents()
            if contents is not None and len(contents.get_data()) > 5 * 1024 * 1024:
                raise SyllabusParseError("This PDF page is too complex. Export a simpler text-based PDF.")
            text = page.extract_text(extraction_mode="layout") or ""
            total += len(text)
            if total > MAX_TEXT:
                raise SyllabusParseError("This PDF contains too much text. Upload only the syllabus pages.")
            pages.append(text)
    except SyllabusParseError:
        raise
    except (PyPdfError, ValueError, TypeError, KeyError, IndexError, RecursionError, OSError) as exc:
        raise SyllabusParseError("The PDF could not be read. Try exporting it as a new text-based PDF.") from exc
    if not any(text.strip() for text in pages):
        raise SyllabusParseError("No readable text found. Scanned/image PDFs need local OCR before uploading.")
    return analyze_pages(pages, year=year, date_order=date_order)
