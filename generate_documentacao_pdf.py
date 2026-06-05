from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Preformatted, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "DOCUMENTACAO_EBF_PIBVP.md"
TARGET = ROOT / "DOC" / "documentacao_ebf_pibvp.pdf"


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_story(markdown):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="DocTitle",
        parent=styles["Title"],
        fontSize=18,
        leading=22,
        spaceAfter=14,
        textColor=colors.HexColor("#123f4f"),
    ))
    styles.add(ParagraphStyle(
        name="H2x",
        parent=styles["Heading2"],
        fontSize=14,
        leading=18,
        spaceBefore=12,
        spaceAfter=8,
        textColor=colors.HexColor("#175c72"),
    ))
    styles.add(ParagraphStyle(
        name="H3x",
        parent=styles["Heading3"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=6,
        textColor=colors.HexColor("#247a5a"),
    ))
    styles.add(ParagraphStyle(
        name="Bodyx",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        spaceAfter=5,
    ))
    styles.add(ParagraphStyle(
        name="Bulletx",
        parent=styles["BodyText"],
        fontSize=9.2,
        leading=12,
        leftIndent=14,
        firstLineIndent=-8,
        spaceAfter=3,
    ))
    styles.add(ParagraphStyle(
        name="Codex",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=7.5,
        leading=9,
        backColor=colors.HexColor("#f3f6f7"),
        borderPadding=5,
    ))

    story = []
    in_code = False
    code = []

    def flush_code():
        if code:
            story.append(Preformatted("\n".join(code), styles["Codex"]))
            story.append(Spacer(1, 6))
            code.clear()

    for raw in markdown.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            if in_code:
                flush_code()
                in_code = False
            else:
                in_code = True
                code.clear()
            continue

        if in_code:
            code.append(line)
            continue

        if not line:
            story.append(Spacer(1, 4))
        elif line.startswith("# "):
            story.append(Paragraph(escape(line[2:]), styles["DocTitle"]))
        elif line.startswith("## "):
            story.append(Paragraph(escape(line[3:]), styles["H2x"]))
        elif line.startswith("### "):
            story.append(Paragraph(escape(line[4:]), styles["H3x"]))
        elif line.startswith("- "):
            story.append(Paragraph("- " + escape(line[2:]), styles["Bulletx"]))
        elif re.match(r"^\d+\. ", line):
            story.append(Paragraph(escape(line), styles["Bulletx"]))
        elif line.startswith("|"):
            story.append(Preformatted(line, styles["Codex"]))
        else:
            story.append(Paragraph(escape(line), styles["Bodyx"]))

    if in_code:
        flush_code()

    return story


def main():
    TARGET.parent.mkdir(exist_ok=True)
    markdown = SOURCE.read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(TARGET),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.4 * cm,
        bottomMargin=1.4 * cm,
        title="Documentacao EBF PIBVP",
    )
    doc.build(build_story(markdown))
    print(TARGET)


if __name__ == "__main__":
    main()
