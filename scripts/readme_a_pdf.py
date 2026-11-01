# -*- coding: utf-8 -*-
"""Convierte el README.md del estudio en un PDF maquetado (reportlab).

Uso: python3 readme_a_pdf.py README.md salida.pdf
Las figuras locales (figs/*.png) se incrustan. Las fotos remotas de Wikimedia
se sustituyen por una nota con su pie de foto (se ven en la versión de GitHub).
"""
import re, sys, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table, TableStyle,
                                PageBreak, KeepTogether, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents
from PIL import Image as PILImage

SRC = sys.argv[1] if len(sys.argv) > 1 else "README.md"
OUT = sys.argv[2] if len(sys.argv) > 2 else "estudio.pdf"
BASE = os.path.dirname(os.path.abspath(SRC))

F = "/usr/share/fonts/truetype/dejavu/"
for n, f in [("DV", "DejaVuSans.ttf"), ("DV-B", "DejaVuSans-Bold.ttf"), ("DV-I", "DejaVuSans-Oblique.ttf"),
             ("DV-BI", "DejaVuSans-BoldOblique.ttf"), ("DVS-B", "DejaVuSerif-Bold.ttf"), ("DVM", "DejaVuSansMono.ttf")]:
    pdfmetrics.registerFont(TTFont(n, F + f))
addMapping("DV", 0, 0, "DV"); addMapping("DV", 1, 0, "DV-B"); addMapping("DV", 0, 1, "DV-I"); addMapping("DV", 1, 1, "DV-BI")

DEEP = colors.HexColor("#0b3d5c"); INK = colors.HexColor("#1f2d3a"); SOFT = colors.HexColor("#eaf3f8")
LINE = colors.HexColor("#a9c3d3"); WARN = colors.HexColor("#f08a24"); ACC = colors.HexColor("#d64545")
ss = {
    "body": ParagraphStyle("body", fontName="DV", fontSize=9.4, leading=13.2, alignment=TA_JUSTIFY, textColor=INK, spaceAfter=5),
    "h1": ParagraphStyle("h1", fontName="DVS-B", fontSize=16, leading=20, textColor=DEEP, spaceBefore=6, spaceAfter=8),
    "h2": ParagraphStyle("h2", fontName="DV-B", fontSize=11.5, leading=14.5, textColor=DEEP, spaceBefore=8, spaceAfter=4),
    "cap": ParagraphStyle("cap", fontName="DV-I", fontSize=7.8, leading=10.2, textColor=colors.HexColor("#4a5a68"), alignment=TA_CENTER, spaceAfter=8),
    "cell": ParagraphStyle("cell", fontName="DV", fontSize=7.8, leading=10, textColor=INK),
    "cellb": ParagraphStyle("cellb", fontName="DV-B", fontSize=7.8, leading=10, textColor=colors.white),
    "bul": ParagraphStyle("bul", fontName="DV", fontSize=9.4, leading=13, leftIndent=14, bulletIndent=3, textColor=INK, spaceAfter=2),
    "note": ParagraphStyle("note", fontName="DV", fontSize=8.8, leading=12.4, textColor=INK),
    "photo": ParagraphStyle("photo", fontName="DV-I", fontSize=7.8, leading=10.2, textColor=colors.HexColor("#4a5a68")),
    "toc1": ParagraphStyle("toc1", fontName="DV-B", fontSize=9.6, leading=14, textColor=DEEP),
    "toc2": ParagraphStyle("toc2", fontName="DV", fontSize=8.8, leading=12, leftIndent=14, textColor=INK),
}

EMOJI = re.compile("[\U0001F000-\U0001FFFF☀-⛿✀-➿️⃣]")
def clean(t):
    return EMOJI.sub("", t).strip()

def inline(t):
    t = clean(t)
    t = t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    t = re.sub(r"`([^`]+)`", r"<font name='DVM'>\1</font>", t)
    t = re.sub(r"\[([^\]]+)\]\((#[^)]*)\)", r"\1", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: m.group(1) if not m.group(2).startswith("http") else f"<link href='{m.group(2)}' color='#1a5fa8'>{m.group(1)}</link>", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"(https?://[^\s<]+)", lambda m: m.group(1) if "href=" in t[max(0, m.start() - 6):m.start()] else f"<link href='{m.group(1)}' color='#1a5fa8'>{m.group(1)}</link>", t)
    return t

story = []
def box(paras, bg=SOFT, edge=DEEP):
    tb = Table([[paras]], colWidths=[16.6 * cm])
    tb.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), bg), ("LINEBEFORE", (0, 0), (0, -1), 3, edge),
                            ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.append(Spacer(1, 2)); story.append(tb); story.append(Spacer(1, 6))

def table(rows):
    n = max(len(r) for r in rows)
    rows = [r + [""] * (n - len(r)) for r in rows]
    lens = [max(len(re.sub(r"[*`]", "", r[i])) for r in rows) for i in range(n)]
    w = [min(max(l, 6), 60) for l in lens]; tot = sum(w)
    widths = [16.6 * cm * x / tot for x in w]
    data = [[Paragraph(inline(c), ss["cellb"] if i == 0 else ss["cell"]) for c in r] for i, r in enumerate(rows)]
    tb = Table(data, colWidths=widths, repeatRows=1)
    st = [("GRID", (0, 0), (-1, -1), 0.4, LINE), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BACKGROUND", (0, 0), (-1, 0), DEEP),
          ("LEFTPADDING", (0, 0), (-1, -1), 3.5), ("RIGHTPADDING", (0, 0), (-1, -1), 3.5), ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
    st += [("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f4f8fb")) for r in range(2, len(rows), 2)]
    tb.setStyle(TableStyle(st)); story.append(tb); story.append(Spacer(1, 7))

def local_images(srcs, cap):
    imgs = []
    for s in srcs:
        p = os.path.join(BASE, s)
        if os.path.exists(p): imgs.append(p)
    if not imgs: return False
    total_w = 16.6 * cm
    if len(imgs) == 1:
        w, h = PILImage.open(imgs[0]).size; W = total_w; H = W * h / w
        if H > 20 * cm: H = 20 * cm; W = H * w / h
        row = [Image(imgs[0], width=W, height=H)]
        flow = row[0]
    else:
        H = 11.5 * cm; ims = []
        for p in imgs:
            w, h = PILImage.open(p).size; ims.append(Image(p, width=H * w / h, height=H))
        sc = min(1, (total_w - 0.4 * cm) / sum(i.drawWidth for i in ims))
        for i in ims: i.drawWidth *= sc; i.drawHeight *= sc
        flow = Table([ims], colWidths=[i.drawWidth + 0.2 * cm for i in ims])
    items = [flow]
    if cap: items.append(Paragraph(inline(cap), ss["cap"]))
    story.append(KeepTogether(items)); return True

def remote_photo_note(alts, cap):
    txt = "<b>Foto en la versión web (GitHub):</b> " + inline(cap if cap else ", ".join(alts))
    box([Paragraph(txt, ss["photo"])], bg=colors.HexColor("#f6f6f2"), edge=colors.HexColor("#b9b2a0"))

class Doc(BaseDocTemplate):
    def afterFlowable(self, f):
        if hasattr(f, "_toc"):
            lvl, txt = f._toc; key = "k%d" % id(f)
            self.canv.bookmarkPage(key); self.canv.addOutlineEntry(re.sub("<[^>]+>", "", txt), key, level=lvl)
            self.notify("TOCEntry", (lvl, txt, self.page, key))

lines = open(SRC, encoding="utf-8").read().split("\n")
title = clean(lines[0].lstrip("# "))
FOOT = title

def deco(canv, doc):
    if doc.page > 1:
        canv.saveState(); canv.setFont("DV", 7.3); canv.setFillColor(colors.HexColor("#6b7c8a"))
        canv.drawString(2.2 * cm, 1.2 * cm, FOOT + " · Óscar Ramírez Martín")
        canv.drawRightString(A4[0] - 2.2 * cm, 1.2 * cm, str(doc.page))
        canv.setStrokeColor(LINE); canv.line(2.2 * cm, 1.5 * cm, A4[0] - 2.2 * cm, 1.5 * cm); canv.restoreState()

doc = Doc(OUT, pagesize=A4, leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
          title=title, author="Óscar Ramírez Martín", subject="Estudio divulgativo")
doc.addPageTemplates([PageTemplate(id="p", frames=[Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height)], onPage=deco)])

# ---- portada ----
i = 1
subtitle = ""
while i < len(lines) and not lines[i].startswith("## "):
    if lines[i].startswith("### ") and not subtitle: subtitle = clean(lines[i][4:])
    i += 1
story.append(Spacer(1, 1.5 * cm))
story.append(Paragraph("<font color='#d64545'>ESTUDIO DIVULGATIVO</font>", ss["h2"]))
story.append(Paragraph(title, ParagraphStyle("t", fontName="DVS-B", fontSize=27, leading=33, textColor=DEEP)))
story.append(Spacer(1, 8))
story.append(Paragraph(subtitle, ParagraphStyle("st", fontName="DV", fontSize=13, leading=18, textColor=INK)))
story.append(Spacer(1, 0.8 * cm))
for fig in ("figs/corte_cueva.png",):
    local_images([fig], "Corte esquemático de la cueva (ilustración propia).")
story.append(Paragraph("<b>Autor:</b> Óscar Ramírez Martín · <b>Fecha:</b> octubre de 2026 · <b>Licencia:</b> CC BY-SA 4.0", ss["body"]))
# notas de cabecera (excepto el enlace al PDF)
for l in lines[1:i]:
    if l.startswith("> ") and ("Nota de respeto" in l):
        box([Paragraph(inline(l[2:]), ss["note"])])
story.append(PageBreak())
story.append(Paragraph("Índice", ss["h1"]))
toc = TableOfContents(); toc.levelStyles = [ss["toc1"], ss["toc2"]]; story.append(toc); story.append(PageBreak())

# ---- cuerpo ----
skip_section = False
para = []
def flush():
    global para
    if para: story.append(Paragraph(inline(" ".join(para)), ss["body"])); para = []

while i < len(lines):
    l = lines[i]; s = l.strip()
    if l.startswith("## "):
        flush(); h = clean(l[3:])
        skip_section = h.lower().startswith("índice")
        if not skip_section:
            story.append(CondPageBreak(5 * cm)); p = Paragraph(inline(h), ss["h1"]); p._toc = (0, inline(h)); story.append(p)
        i += 1; continue
    if skip_section: i += 1; continue
    if l.startswith("### "):
        flush(); h = clean(l[4:]); story.append(CondPageBreak(3.5 * cm)); p = Paragraph(inline(h), ss["h2"]); p._toc = (1, inline(h)); story.append(p); i += 1; continue
    if s.startswith("```"):
        flush(); i += 1
        while i < len(lines) and not lines[i].strip().startswith("```"): i += 1
        i += 1; continue
    if s.startswith("$$"):
        flush(); story.append(Paragraph("<b>P<sub>absoluta</sub> (bar) = 1 + profundidad (m) / 10</b>", ParagraphStyle("f", parent=ss["body"], alignment=TA_CENTER))); i += 1; continue
    if s == "---" or s == "":
        flush(); i += 1; continue
    if s.startswith("|"):
        flush(); rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            r = lines[i].strip().strip("|")
            cells = [c.strip() for c in re.split(r"(?<!\\)\|", r)]
            if not all(re.fullmatch(r":?-{3,}:?", c) for c in cells): rows.append(cells)
            i += 1
        table(rows); continue
    if s.startswith(">"):
        flush(); q = []
        while i < len(lines) and lines[i].strip().startswith(">"):
            q.append(lines[i].strip()[1:].strip()); i += 1
        paras = [Paragraph(inline(x), ss["note"]) for x in " \n".join(q).split("\n \n") if x.strip()]
        paras = [Paragraph(inline(x), ss["note"]) for x in "\n".join(q).split("\n\n") if x.strip()] or paras
        box(paras); continue
    if s.startswith("![") or s.startswith("<p"):
        flush(); srcs = []; alts = []
        if s.startswith("!["):
            m = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", s); alts.append(m.group(1)); srcs.append(m.group(2)); i += 1
        else:
            blk = ""
            while i < len(lines):
                blk += lines[i]; i += 1
                if "</p>" in blk: break
            srcs = re.findall(r'src="([^"]+)"', blk); alts = re.findall(r'alt="([^"]+)"', blk)
        cap = ""
        j = i
        while j < len(lines) and lines[j].strip() == "": j += 1
        if j < len(lines) and lines[j].strip().startswith("*") and not lines[j].strip().startswith("**"):
            cap = lines[j].strip().strip("*"); i = j + 1
        if any(not x.startswith("http") for x in srcs):
            local_images([x for x in srcs if not x.startswith("http")], cap)
        else:
            remote_photo_note(alts, cap)
        continue
    m = re.match(r"^(\s*)(?:[-*]|(\d+)\.)\s+(.*)", l)
    if m:
        flush(); bullet = (m.group(2) + ".") if m.group(2) else "•"
        story.append(Paragraph(inline(m.group(3)), ss["bul"], bulletText=bullet)); i += 1; continue
    para.append(s); i += 1
flush()
doc.multiBuild(story)
print("PDF:", OUT)
