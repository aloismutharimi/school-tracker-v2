"""
PDF generation for reports.
Uses ReportLab to create styled A4 documents.
"""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

from config import DATA_DIR, DEFAULT_TERM
from models import students
from services.tracker import (
    compute_balance, build_finance_data, build_performance_data
)

REPORTS_DIR = DATA_DIR / "reports"

# --- Styles ---
STYLES = getSampleStyleSheet()
TITLE = ParagraphStyle(
    "Title", parent=STYLES["Heading1"],
    fontSize=18, spaceAfter=4, textColor=colors.HexColor("#0b1a2e"),
)
SUBTITLE = ParagraphStyle(
    "Subtitle", parent=STYLES["Normal"],
    fontSize=11, textColor=colors.HexColor("#64748b"), spaceAfter=12,
)
SECTION = ParagraphStyle(
    "Section", parent=STYLES["Heading2"],
    fontSize=13, spaceBefore=14, spaceAfter=8,
    textColor=colors.HexColor("#0b1a2e"),
)
CLASS_HEADER = ParagraphStyle(
    "ClassHeader", parent=STYLES["Heading2"],
    fontSize=14, spaceBefore=16, spaceAfter=8,
    textColor=colors.white, backColor=colors.HexColor("#0b1a2e"),
    borderPadding=6, leftIndent=0,
)
BODY = ParagraphStyle(
    "Body", parent=STYLES["Normal"],
    fontSize=10, spaceAfter=6,
)


def _table(data, col_widths=None, header=True):
    """Build a styled ReportLab table."""
    t = Table(data, colWidths=col_widths, hAlign="LEFT")
    style = [
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#94a3b8")),
        ]
    style += [
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f8fafc")]),
        ("LINEBELOW", (0, 1), (-1, -2), 0.25, colors.HexColor("#e2e8f0")),
    ]
    t.setStyle(TableStyle(style))
    return t


def _finance_table(finance_rows):
    if not finance_rows: return None
    data = [["Student Name", "Class", "Due", "Paid", "Balance", "Status"]]
    for r in finance_rows:
        status = "ARREARS" if r["in_arrears"] else "CLEARED"
        data.append([
            r["name"], r["class"],
            f"{r['due']:,.0f}", f"{r['paid']:,.0f}",
            f"{r['balance']:,.0f}", status,
        ])
    return _table(data, col_widths=[130, 55, 65, 65, 65, 60])


def _perf_table(perf_rows):
    if not perf_rows: return None
    data = [["Rank", "Student Name", "Class", "Average"]]
    for r in perf_rows:
        data.append([f"#{r['rank']}", r["name"], r["class"], f"{r['average']:.1f}%"])
    return _table(data, col_widths=[45, 180, 70, 75])

def _class_summary_block(finance_rows, perf_rows):
    """Return a list of flowables for a per-class summary."""
    flow = [Paragraph("Class Summary", SECTION)]
    
    if not finance_rows:
        return flow
        
    total_due = sum(r["due"] for r in finance_rows)
    total_paid = sum(r["paid"] for r in finance_rows)
    total_bal = sum(r["balance"] for r in finance_rows)
    arrears = sum(1 for r in finance_rows if r["in_arrears"])
    
    rows = [
        ["Total billed:", f"{total_due:,.0f}"],
        ["Total collected:", f"{total_paid:,.0f}"],
        ["Outstanding:", f"{total_bal:,.0f}"],
        ["In arrears:", f"{arrears}/{len(finance_rows)} students"],
    ]
    
    if perf_rows:
        avg = sum(r["average"] for r in perf_rows) / len(perf_rows)
        top = perf_rows[0] # We know it's sorted by rank
        rows.append(["Class average:", f"{avg:.1f}%"])
        rows.append(["Top performer:", f"{top['name']} ({top['average']:.1f}%)"])

    t = Table(rows, colWidths=[130, 200], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(t)
    return flow


def _school_summary_block(finance_rows):
    """Return a list of flowables for the school-wide summary."""
    flow = [Paragraph("SCHOOL SUMMARY", CLASS_HEADER), Spacer(1, 6)]
    
    if not finance_rows:
        return flow
        
    total_due = sum(r["due"] for r in finance_rows)
    total_paid = sum(r["paid"] for r in finance_rows)
    total_bal = sum(r["balance"] for r in finance_rows)
    arrears = sum(1 for r in finance_rows if r["in_arrears"])
    
    rows = [
        ["Total billed:", f"{total_due:,.0f}"],
        ["Total collected:", f"{total_paid:,.0f}"],
        ["Outstanding:", f"{total_bal:,.0f}"],
        ["In arrears:", f"{arrears}/{len(finance_rows)} students"],
    ]
    
    t = Table(rows, colWidths=[130, 200], hAlign="LEFT")
    t.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    flow.append(t)
    return flow

def export_full_pdf(term=None):
    """Generate a full school report broken down by class."""
    term = term or DEFAULT_TERM
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{term}-full.pdf"

    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title=f"Term Report — {term}",
    )

    story = [
        Paragraph(f"Term Report · {term}", TITLE),
        Paragraph("School Fees &amp; Results Tracker", SUBTITLE),
    ]

    finance_data = build_finance_data(term)
    perf_data = build_performance_data(term)

    # Group by class
    all_classes = sorted({s["class"] for s in students.list_all()})

    for c in all_classes:
        story.append(Paragraph(f"{c.upper()}", CLASS_HEADER))
        story.append(Spacer(1, 6))

        c_fin = [r for r in finance_data if r["class"] == c]
        c_perf = [r for r in perf_data if r["class"] == c]

        story.append(Paragraph("Fees &amp; Balances", SECTION))
        t_fin = _finance_table(c_fin)
        if t_fin: story.append(t_fin)
        else: story.append(Paragraph("No fee data.", BODY))

        story.append(Paragraph("Performance Ranking", SECTION))
        t_perf = _perf_table(c_perf)
        if t_perf: story.append(t_perf)
        else: story.append(Paragraph("No scores recorded.", BODY))

        # ADD THIS LINE:
        story.extend(_class_summary_block(c_fin, c_perf))

        story.append(PageBreak())

    # ADD THESE LINES AT THE END, BEFORE doc.build(story):
    story.extend(_school_summary_block(finance_data))

    doc.build(story)
    return path


def export_student_pdf(student_id, term=None):
    """Generate a single-page PDF for one student."""
    term = term or DEFAULT_TERM
    student = students.get(student_id)
    if not student:
        raise ValueError(f"Unknown student {student_id}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{term}-{student_id}.pdf"

    doc = SimpleDocTemplate(
        str(path), pagesize=A4,
        leftMargin=18*mm, rightMargin=18*mm,
        topMargin=18*mm, bottomMargin=18*mm,
        title=f"Student Report — {student['name']}",
    )

    story = [
        Paragraph(f"Student Report · {student['name']} · {term}", TITLE),
        Paragraph("School Fees &amp; Results Tracker", SUBTITLE),
        Paragraph(f"{student['name']} · {student['class']}", BODY),
    ]

    # Fees
    story.append(Paragraph("Fees &amp; Balances", SECTION))
    fin_row = compute_balance(student_id, term)
    t_fin = _finance_table([fin_row])
    if t_fin: story.append(t_fin)

    # Performance
    story.append(Paragraph("Performance", SECTION))
    perf_data = build_performance_data(term, target_class=student["class"])
    student_perf = next((r for r in perf_data if r["student_id"] == student_id), None)

    if student_perf:
        story.append(Paragraph(f"Rank in class: <b>#{student_perf['rank']}</b> of {len(perf_data)}", BODY))
        story.append(Paragraph(f"Average: <b>{student_perf['average']:.1f}%</b>", BODY))
    else:
        story.append(Paragraph("No scores recorded this term.", BODY))

    # Subject Breakdown
    story.append(Paragraph("Subject Breakdown", SECTION))
    # Note: we need a model function to list scores by student
    from models import scores as scores_model
    student_scores = scores_model.list_by_student(student_id, term)

    if not student_scores:
        story.append(Paragraph("No scores recorded.", BODY))
    else:
        data = [["Subject", "Score", "Percentage"]]
        for s in student_scores:
            pct = (s["score"] / s["out_of"]) * 100
            data.append([
                s["subject"],
                f"{s['score']:.0f}/{s['out_of']:.0f}",
                f"{pct:.1f}%",
            ])
        story.append(_table(data, col_widths=[180, 90, 100]))

    doc.build(story)
    return path