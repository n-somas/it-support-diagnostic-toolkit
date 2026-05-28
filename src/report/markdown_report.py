from datetime import datetime
from pathlib import Path


def format_value_for_markdown(value):
    """
    Bereitet Werte für eine Markdown-Tabelle auf.
    Mehrzeilige Werte werden mit <br> ersetzt, damit die Tabelle nicht kaputtgeht.
    """

    value_as_text = str(value)
    return value_as_text.replace("\n", "<br>")


def create_markdown_section(title, data):
    """
    Erstellt einen Markdown-Abschnitt aus einem Dictionary.
    """

    lines = []
    lines.append(f"## {title}")
    lines.append("")
    lines.append("| Prüfung | Ergebnis |")
    lines.append("|---|---|")

    for key, value in data.items():
        formatted_value = format_value_for_markdown(value)
        lines.append(f"| {key} | {formatted_value} |")

    lines.append("")
    return "\n".join(lines)


def create_markdown_report(sections):
    """
    Erstellt einen vollständigen Markdown-Supportbericht.
    """

    report_lines = []

    report_lines.append("# IT Support Diagnostic Report")
    report_lines.append("")
    report_lines.append(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")

    for title, data in sections:
        section = create_markdown_section(title, data)
        report_lines.append(section)

    return "\n".join(report_lines)


def save_markdown_report(sections, file_path="reports/support_report.md"):
    """
    Speichert den Markdown-Bericht im reports-Ordner.
    Falls der Ordner nicht existiert, wird er automatisch erstellt.
    """

    report_path = Path(file_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    markdown_content = create_markdown_report(sections)

    report_path.write_text(markdown_content, encoding="utf-8")

    return report_path