"""PDF engine for the backend learning course.

Content modules (m1.py ... m7.py) expose MODULE = {title, intro, topics:[...]}.
Each topic: {title, blocks:[(kind, ...)], questions:[md], answer: md}
Block kinds: p, h, ul, ol, code, table, analogy, key, warn
Inline markdown: **bold**, `code`, *italic*
"""
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table,
                                TableStyle, Preformatted, KeepTogether, PageBreak, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

D = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("DV", D + "DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DVB", D + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DVM", D + "DejaVuSansMono.ttf"))
registerFontFamily("DV", normal="DV", bold="DVB", italic="DV", boldItalic="DVB")

ACCENT = colors.HexColor("#1f4e79")
MUTED = colors.HexColor("#5f6b76")
PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
W = PAGE_W - 2 * MARGIN

S = {
    "cover_t": ParagraphStyle("ct", fontName="DVB", fontSize=28, leading=34, textColor=ACCENT, alignment=1),
    "cover_s": ParagraphStyle("cs", fontName="DV", fontSize=13, leading=18, textColor=MUTED, alignment=1),
    "mod": ParagraphStyle("mod", fontName="DVB", fontSize=22, leading=27, textColor=ACCENT, spaceAfter=8),
    "topic": ParagraphStyle("topic", fontName="DVB", fontSize=15, leading=19, textColor=ACCENT,
                            spaceBefore=6, spaceAfter=8, keepWithNext=1),
    "h": ParagraphStyle("h", fontName="DVB", fontSize=11.5, leading=15, textColor=ACCENT,
                        spaceBefore=8, spaceAfter=4, keepWithNext=1),
    "p": ParagraphStyle("p", fontName="DV", fontSize=9.6, leading=13.6, spaceAfter=5),
    "li": ParagraphStyle("li", fontName="DV", fontSize=9.6, leading=13.4, leftIndent=12, bulletIndent=2,
                         spaceAfter=2),
    "cell": ParagraphStyle("cell", fontName="DV", fontSize=8.6, leading=11.4),
    "code": ParagraphStyle("code", fontName="DVM", fontSize=7.5, leading=9.4),
    "toc0": ParagraphStyle("toc0", fontName="DVB", fontSize=10, leading=12, spaceBefore=0),
    "toc1": ParagraphStyle("toc1", fontName="DV", fontSize=8.6, leading=9.8, leftIndent=14),
}


def md(t):
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    spans = []                                   # protect `code` from bold/italic parsing

    def stash(m):
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"
    t = re.sub(r"`([^`]+)`", stash, t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*([^*]+)\*(?![\w*])", r"<i>\1</i>", t)
    return re.sub("\x00(\\d+)\x00",
                  lambda m: f"<font name='DVM' color='#7a2e0e'>{spans[int(m.group(1))]}</font>", t)


def P(t, style="p"):
    return Paragraph(md(t), S[style])


def boxed(content, bg, border, label=None, label_color=None):
    inner = []
    if label:
        inner.append(Paragraph(f"<b>{label}</b>", ParagraphStyle("lbl", parent=S["p"], textColor=label_color,
                                                                  spaceAfter=2)))
    inner += content
    t = Table([[inner]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), bg),
        ("LINEBEFORE", (0, 0), (0, -1), 3, border),
        ("BOX", (0, 0), (-1, -1), 0.4, border),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def code(text):
    pre = Preformatted(text.strip("\n"), S["code"])
    t = Table([[pre]], colWidths=[W])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f6f8")),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d1d9")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    t.spaceBefore, t.spaceAfter = 3, 8
    return t


def table(rows, ratios):
    data = [[Paragraph(("<b>%s</b>" if i == 0 else "%s") % md(c), S["cell"]) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=[W * r for r in ratios], repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dce6f0")),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b0b8c0")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    t.spaceBefore, t.spaceAfter = 3, 8
    return t


def render_block(b):
    k = b[0]
    if k == "p":
        return [P(b[1])]
    if k == "h":
        return [P(b[1], "h")]
    if k in ("ul", "ol"):
        out = []
        for i, item in enumerate(b[1], 1):
            bullet = "•" if k == "ul" else f"{i}."
            out.append(Paragraph(md(item), S["li"], bulletText=bullet))
        out.append(Spacer(1, 4))
        return out
    if k == "code":
        return [code(b[1])]
    if k == "table":
        return [table(b[1], b[2])]
    if k == "analogy":
        return [boxed([P(b[1])], colors.HexColor("#eef5ec"), colors.HexColor("#4f8a3c"),
                      "Real-world analogy", colors.HexColor("#2f6420")), Spacer(1, 8)]
    if k == "key":
        return [boxed([P(x) for x in b[1]] if isinstance(b[1], list) else [P(b[1])],
                      colors.HexColor("#eaf1f8"), ACCENT, "Key takeaways", ACCENT), Spacer(1, 8)]
    if k == "warn":
        return [boxed([P(b[1])], colors.HexColor("#fff4e5"), colors.HexColor("#d98a1c"),
                      "Common mistake", colors.HexColor("#9a5a00")), Spacer(1, 8)]
    raise ValueError(k)


class Doc(BaseDocTemplate):
    def __init__(self, path, **kw):
        super().__init__(path, pagesize=A4, leftMargin=MARGIN, rightMargin=MARGIN,
                         topMargin=16 * mm, bottomMargin=18 * mm, **kw)
        frame = Frame(MARGIN, 18 * mm, W, PAGE_H - 34 * mm, id="f")
        self.addPageTemplates([PageTemplate("all", [frame], onPageEnd=self._footer)])
        self.current_module = ""

    def _footer(self, c, d):
        if d.page == 1:
            return
        c.saveState()
        c.setFont("DV", 7.5)
        c.setFillColor(colors.grey)
        c.drawString(MARGIN, 10 * mm, self.current_module)
        c.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Page {d.page}")
        c.restoreState()

    def beforeDocument(self):
        self.current_module = "Java & Cloud-Native Backend Course"

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and hasattr(f, "_toc"):
            level, text, key = f._toc
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=level == 0)
            self.notify("TOCEntry", (level, text, self.page, key))
            if level == 0:
                self.current_module = text


def toc_para(text, style, level, key):
    p = Paragraph(md(text), S[style])
    p._toc = (level, text, key)
    return p


def build(path, modules, front, back=(), answers_title="Answer Key"):
    story = []
    story += front
    toc = TableOfContents()
    toc.levelStyles = [S["toc0"], S["toc1"]]
    story += [P("Contents", "mod"), toc, PageBreak()]

    for mi, m in enumerate(modules, 1):
        story.append(toc_para(f"Module {mi}: {m['title']}", "mod", 0, f"m{mi}"))
        story += [P(m["intro"]), Spacer(1, 6)]
        for ti, t in enumerate(m["topics"], 1):
            if ti > 1:
                story.append(CondPageBreak(90 * mm))
            story.append(toc_para(f"{mi}.{ti}  {t['title']}", "topic", 1, f"t{mi}_{ti}"))
            for b in t["blocks"]:
                story += render_block(b)
            qs = [Paragraph(md(q), S["li"], bulletText=f"Q{i}.") for i, q in enumerate(t["questions"], 1)]
            story.append(Spacer(1, 6))
            story.append(KeepTogether(boxed(qs, colors.HexColor("#f3effa"), colors.HexColor("#6b4fa0"),
                                            "Check for understanding", colors.HexColor("#4b2f80"))))
            story.append(Spacer(1, 10))
        story.append(PageBreak())

    story += list(back)
    story.append(toc_para(answers_title, "mod", 0, "answers"))
    story.append(P("Try each question yourself before reading the answer. Struggling first is how it sticks."))
    for mi, m in enumerate(modules, 1):
        story.append(P(f"Module {mi}: {m['title']}", "topic"))
        for ti, t in enumerate(m["topics"], 1):
            story.append(P(f"**{mi}.{ti} {t['title']}**"))
            for a in (t["answer"] if isinstance(t["answer"], list) else [t["answer"]]):
                story += render_block(a) if isinstance(a, tuple) else [P(a, "li")]
            story.append(Spacer(1, 4))

    doc = Doc(path, title="Java & Cloud-Native Backend: Complete Course", author="Learning Notes")
    doc.multiBuild(story)
