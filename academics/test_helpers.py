"""Small real PDFs for integration tests, with no PDF-generation dependency."""
from io import BytesIO

from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def syllabus_pdf(text="Homework 1 - September 15, 2026", pages=1, password=None):
    writer = PdfWriter()
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    for _ in range(pages):
        page = writer.add_blank_page(width=612, height=792)
        page[NameObject("/Resources")] = DictionaryObject({
            NameObject("/Font"): DictionaryObject({NameObject("/F1"): font}),
        })
        lines = []
        for line in text.splitlines():
            escaped = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            lines.append(f"({escaped}) Tj T*")
        stream = DecodedStreamObject()
        stream.set_data(("BT /F1 12 Tf 14 TL 40 750 Td " + " ".join(lines) + " ET").encode("latin-1"))
        page[NameObject("/Contents")] = stream
    if password:
        writer.encrypt(password)
    output = BytesIO()
    writer.write(output)
    return output.getvalue()
