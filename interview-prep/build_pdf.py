"""Builds the Java interview guide PDF from the markdown-like files in content/.

Format: '# ' chapter, '## ' question, '- ' bullet, '> ' tip, ``` code fences,
anything else is an answer paragraph. Inline: **bold** and `code`.
Run: python3 build_pdf.py  ->  Java_Senior_Interview_Guide.pdf
"""
import glob
import os
import re
import textwrap

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, KeepTogether, PageBreak, PageTemplate,
                                Paragraph, Spacer, Table, TableStyle, XPreformatted)
from reportlab.platypus.tableofcontents import TableOfContents

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("Sans", f"{FONT_DIR}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("Sans-Bold", f"{FONT_DIR}/DejaVuSans-Bold.ttf"))

pdfmetrics.registerFont(TTFont("Mono", f"{FONT_DIR}/DejaVuSansMono.ttf"))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-Bold", italic="Sans",
                              boldItalic="Sans-Bold")

NAVY = colors.HexColor("#1F3A5F")
ACCENT = colors.HexColor("#E07A1F")
CODE_BG = colors.HexColor("#F4F6F8")
TIP_BG = colors.HexColor("#FFF6E5")
MUTED = colors.HexColor("#5B6770")

S = {
    "cover_title": ParagraphStyle("ct", fontName="Sans-Bold", fontSize=30, leading=38,
                                  textColor=NAVY, alignment=TA_CENTER),
    "cover_sub": ParagraphStyle("cs", fontName="Sans", fontSize=14, leading=20,
                                textColor=MUTED, alignment=TA_CENTER),
    "chapter": ParagraphStyle("ch", fontName="Sans-Bold", fontSize=22, leading=28,
                              textColor=colors.white, backColor=NAVY, borderPadding=(10, 10, 10),
                              spaceAfter=18),
    "question": ParagraphStyle("q", fontName="Sans-Bold", fontSize=11.5, leading=15,
                               textColor=NAVY, spaceBefore=14, spaceAfter=5),
    "body": ParagraphStyle("b", fontName="Sans", fontSize=9.5, leading=13.5, spaceAfter=4),
    "bullet": ParagraphStyle("bl", fontName="Sans", fontSize=9.5, leading=13.5, leftIndent=14,
                             bulletIndent=4, spaceAfter=2),
    "code": ParagraphStyle("c", fontName="Mono", fontSize=7.6, leading=10, backColor=CODE_BG,
                           borderColor=colors.HexColor("#D5DBE1"), borderWidth=0.5,
                           borderPadding=6, leftIndent=6, rightIndent=6, spaceBefore=6,
                           spaceAfter=10),
    "tip": ParagraphStyle("t", fontName="Sans", fontSize=9, leading=12.5),
    "toc1": ParagraphStyle("toc1", fontName="Sans-Bold", fontSize=11, leading=18, textColor=NAVY),
    "toc2": ParagraphStyle("toc2", fontName="Sans", fontSize=8.5, leading=11.5, leftIndent=16,
                           textColor=MUTED),
}
CODE_WRAP = 98


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def inline(text):
    text = esc(text)
    text = re.sub(r"`([^`]+)`",
                  r'<font name="Mono" size="8.6" color="#B03A2E">\1</font>', text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return text


def code_block(lines):
    wrapped = []
    for line in lines:
        if len(line) <= CODE_WRAP:
            wrapped.append(line)
        else:
            indent = len(line) - len(line.lstrip())
            wrapped.extend(textwrap.wrap(line, CODE_WRAP, subsequent_indent=" " * (indent + 4),
                                         drop_whitespace=False) or [line])
    return XPreformatted(esc("\n".join(wrapped)), S["code"])


def tip_box(text):
    t = Table([[Paragraph("<b>Interview tip:</b> " + inline(text), S["tip"])]],
              colWidths=[A4[0] - 4.4 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), TIP_BG),
        ("LINEBEFORE", (0, 0), (0, -1), 3, ACCENT),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return [Spacer(1, 3), t, Spacer(1, 6)]


class GuideDoc(BaseDocTemplate):
    def __init__(self, path):
        super().__init__(path, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                         topMargin=2 * cm, bottomMargin=2 * cm,
                         title="Java Senior Interview Guide (9+ Years)",
                         author="Interview Prep", subject="Java, Spring Boot, Microservices, "
                         "System Design, Kafka, Azure, DevOps")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate("main", [frame], onPage=self.decorate)])

    @staticmethod
    def decorate(canvas, doc):
        if doc.page == 1:
            return
        canvas.saveState()
        canvas.setFont("Sans", 8)
        canvas.setFillColor(MUTED)
        canvas.drawString(2 * cm, A4[1] - 1.3 * cm, "Java Senior Interview Guide  |  9+ Years")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
        canvas.setStrokeColor(ACCENT)
        canvas.setLineWidth(0.8)
        canvas.line(2 * cm, A4[1] - 1.45 * cm, A4[0] - 2 * cm, A4[1] - 1.45 * cm)
        canvas.restoreState()

    def afterFlowable(self, f):
        level = getattr(f, "toc_level", None)
        if level is not None:
            key = f"k{id(f)}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(f.toc_text, key, level=level, closed=level == 0)
            self.notify("TOCEntry", (level, f.toc_text, self.page, key))


def heading(text, style, level):
    p = Paragraph(text, style)
    p.toc_level = level
    p.toc_text = re.sub(r"<[^>]+>", "", text)
    return p


def parse(path, chapter_no, q_counter, story):
    lines = open(path, encoding="utf-8").read().splitlines()
    i = 0
    q_no = 0
    pending_q = None  # keep a question heading with its first answer element

    def add(flow):
        nonlocal pending_q
        if pending_q is not None:
            story.append(KeepTogether([pending_q] + (flow if isinstance(flow, list) else [flow])))
            pending_q = None
        elif isinstance(flow, list):
            story.extend(flow)
        else:
            story.append(flow)

    while i < len(lines):
        line = lines[i].rstrip()
        if line.startswith("```"):
            block = []
            i += 1
            while not lines[i].startswith("```"):
                block.append(lines[i].rstrip())
                i += 1
            add(code_block(block))
        elif line.startswith("## "):
            q_no += 1
            q_counter[0] += 1
            pending_q = heading(f"Q{q_counter[0]}. {inline(line[3:])}", S["question"], 1)
        elif line.startswith("# "):
            if story:
                story.append(PageBreak())
            chapter_no[0] += 1
            story.append(heading(f"{chapter_no[0]}. {inline(line[2:])}", S["chapter"], 0))
        elif line.startswith("- "):
            add(Paragraph(inline(line[2:]), S["bullet"], bulletText="•"))
        elif line.startswith("> "):
            add(tip_box(line[2:]))
        elif line.strip():
            add(Paragraph(inline(line), S["body"]))
        i += 1


def cover(total_q, chapters):
    items = [Spacer(1, 5 * cm),
             Paragraph("Java Senior Interview Guide", S["cover_title"]), Spacer(1, 0.6 * cm),
             Paragraph("Questions &amp; Explained Answers for 9+ Years Experience", S["cover_sub"]),
             Spacer(1, 1.2 * cm)]
    topics = "<br/>".join(chapters)
    items.append(Paragraph(topics, ParagraphStyle("tp", parent=S["cover_sub"], fontSize=11.5,
                                                  leading=19, textColor=NAVY)))
    items += [Spacer(1, 1.5 * cm),
              Paragraph(f"{total_q} questions with explanations, code samples and interview tips",
                        ParagraphStyle("n", parent=S["cover_sub"], fontSize=10)),
              PageBreak()]
    return items


def main():
    files = sorted(glob.glob(os.path.join(HERE, "content", "*.md")))
    body, chapter_no, q_counter = [], [0], [0]
    for f in files:
        parse(f, chapter_no, q_counter, body)

    chapter_titles = [re.sub(r"^\d+\. ", "", f.toc_text) for f in body
                      if getattr(f, "toc_level", None) == 0]
    toc = TableOfContents(levelStyles=[S["toc1"], S["toc2"]], dotsMinLevel=0)
    story = cover(q_counter[0], chapter_titles)
    story += [Paragraph("Contents", ParagraphStyle("cth", parent=S["question"], fontSize=18,
                                                   leading=24)), toc, PageBreak()]
    story += body

    out = os.path.join(HERE, "Java_Senior_Interview_Guide.pdf")
    GuideDoc(out).multiBuild(story)
    print(f"Wrote {out}: {chapter_no[0]} chapters, {q_counter[0]} questions")


if __name__ == "__main__":
    main()
