import csv
import os
from collections import Counter, defaultdict
from html import escape

from speed_validator import get_threshold

RESULTS_DIR = "results"
INPUT_FILE = os.path.join(RESULTS_DIR, "can_validation_results.csv")
ENRICHED_CSV = os.path.join(RESULTS_DIR, "can_validation_results_with_thresholds.csv")
HTML_REPORT = os.path.join(RESULTS_DIR, "can_validation_report.html")
PDF_REPORT = os.path.join(RESULTS_DIR, "can_validation_report.pdf")


def read_rows(path):
    with open(path, newline="") as file:
        return list(csv.DictReader(file))


def int_can_id(value):
    return int(value, 16)


def enrich_rows(rows):
    enriched = []
    for row in rows:
        can_id = int_can_id(row["can_id"])
        threshold = get_threshold(can_id)
        new_row = dict(row)
        new_row.update(threshold)
        enriched.append(new_row)
    return enriched


def write_enriched_csv(rows):
    if not rows:
        return

    fieldnames = list(rows[0].keys())
    with open(ENRICHED_CSV, "w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def pass_fail_counts(rows):
    counts = defaultdict(Counter)
    for row in rows:
        counts[row["signal"]][row["receiver_result"]] += 1
    return counts


def suite_counts(rows):
    return Counter(row["suite_result"] for row in rows)


def threshold_rows(rows):
    seen = {}
    for row in rows:
        seen[row["can_id"]] = {
            "can_id": row["can_id"],
            "signal": row["signal"],
            "pass_rule": row["pass_rule"],
            "warning_rule": row["warning_rule"],
            "fail_rule": row["fail_rule"],
            "example_pass": row["example_pass"],
            "example_fail": row["example_fail"],
        }
    return [seen[key] for key in sorted(seen.keys())]


def make_bar_svg(counts):
    signals = list(counts.keys())
    width = 920
    height = 340
    margin_left = 160
    margin_bottom = 50
    chart_width = width - margin_left - 40
    chart_height = height - 60 - margin_bottom
    max_count = max(
        [counts[signal]["PASS"] + counts[signal]["FAIL"] for signal in signals] + [1]
    )
    group_height = chart_height / max(len(signals), 1)

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Pass and fail counts by signal">'
    ]
    parts.append(
        f'<line x1="{margin_left}" y1="20" x2="{margin_left}" '
        f'y2="{height - margin_bottom}" stroke="#334155" />'
    )

    for index, signal in enumerate(signals):
        y = 35 + index * group_height
        pass_count = counts[signal]["PASS"]
        fail_count = counts[signal]["FAIL"]
        pass_width = chart_width * pass_count / max_count
        fail_width = chart_width * fail_count / max_count

        parts.append(
            f'<text x="10" y="{y + 16:.1f}" font-size="13" '
            f'fill="#0f172a">{escape(signal)}</text>'
        )
        parts.append(
            f'<rect x="{margin_left}" y="{y:.1f}" width="{pass_width:.1f}" '
            'height="18" fill="#16a34a" />'
        )
        parts.append(
            f'<rect x="{margin_left}" y="{y + 22:.1f}" width="{fail_width:.1f}" '
            'height="18" fill="#dc2626" />'
        )
        parts.append(
            f'<text x="{margin_left + pass_width + 8:.1f}" y="{y + 14:.1f}" '
            f'font-size="12" fill="#0f172a">PASS {pass_count}</text>'
        )
        parts.append(
            f'<text x="{margin_left + fail_width + 8:.1f}" y="{y + 36:.1f}" '
            f'font-size="12" fill="#0f172a">FAIL {fail_count}</text>'
        )

    parts.append("</svg>")
    return "\n".join(parts)


def make_value_svg(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["signal"]].append(row)

    width = 920
    height = 420
    margin_left = 160
    chart_width = width - margin_left - 40
    row_height = 68
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        'aria-label="Observed values by signal">'
    ]

    max_value = max([int(row["value"]) for row in rows] + [1])

    for index, (signal, values) in enumerate(grouped.items()):
        y = 35 + index * row_height
        parts.append(
            f'<text x="10" y="{y + 5}" font-size="13" '
            f'fill="#0f172a">{escape(signal)}</text>'
        )
        parts.append(
            f'<line x1="{margin_left}" y1="{y}" x2="{width - 30}" y2="{y}" '
            'stroke="#cbd5e1" />'
        )
        for value_index, row in enumerate(values[:12]):
            value = int(row["value"])
            x = margin_left + chart_width * value / max_value
            jitter = (value_index % 3) * 13 - 13
            color = "#16a34a" if row["receiver_result"] == "PASS" else "#dc2626"
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y + jitter:.1f}" r="5" '
                f'fill="{color}" opacity="0.8" />'
            )
            parts.append(
                f'<text x="{x + 7:.1f}" y="{y + jitter + 4:.1f}" '
                f'font-size="10" fill="#475569">{value}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts)


def make_html_report(rows):
    counts = pass_fail_counts(rows)
    suite = suite_counts(rows)
    threshold_table_rows = threshold_rows(rows)

    threshold_html = "\n".join(
        "<tr>"
        f"<td>{escape(row['can_id'])}</td>"
        f"<td>{escape(row['signal'])}</td>"
        f"<td>{escape(row['pass_rule'])}</td>"
        f"<td>{escape(row['warning_rule'])}</td>"
        f"<td>{escape(row['fail_rule'])}</td>"
        f"<td>{escape(row['example_pass'])}</td>"
        f"<td>{escape(row['example_fail'])}</td>"
        "</tr>"
        for row in threshold_table_rows
    )

    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>CAN Validation Report</title>
  <style>
    body {{ font-family: Arial, sans-serif; color: #0f172a; margin: 32px; }}
    h1, h2 {{ margin: 0 0 14px; }}
    .page {{ min-height: 950px; page-break-after: always; }}
    .summary {{ display: flex; gap: 16px; margin: 18px 0; }}
    .metric {{ border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px 16px; }}
    .metric strong {{ display: block; font-size: 26px; }}
    .chart {{ border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; margin: 16px 0; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
    th, td {{ border: 1px solid #cbd5e1; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #e2e8f0; }}
    .note {{ color: #475569; font-size: 13px; }}
    @media print {{ body {{ margin: 18mm; }} .page {{ page-break-after: always; }} }}
  </style>
</head>
<body>
  <section class="page">
    <h1>CAN Validation Report</h1>
    <p class="note">Source CSV: {escape(INPUT_FILE)}</p>
    <div class="summary">
      <div class="metric"><span>Total frames</span><strong>{len(rows)}</strong></div>
      <div class="metric"><span>Suite PASS</span><strong>{suite['PASS']}</strong></div>
      <div class="metric"><span>Suite FAIL</span><strong>{suite['FAIL']}</strong></div>
    </div>
    <h2>Graph 1: Receiver PASS/FAIL Counts</h2>
    <div class="chart">{make_bar_svg(counts)}</div>
    <h2>Graph 2: Observed Signal Values</h2>
    <div class="chart">{make_value_svg(rows)}</div>
  </section>

  <section class="page">
    <h1>Page 2: Threshold Table</h1>
    <p class="note">This table is also written into {escape(ENRICHED_CSV)}.</p>
    <table>
      <thead>
        <tr>
          <th>CAN ID</th>
          <th>Signal</th>
          <th>PASS threshold</th>
          <th>Warning threshold</th>
          <th>FAIL threshold</th>
          <th>Example PASS</th>
          <th>Example FAIL</th>
        </tr>
      </thead>
      <tbody>
        {threshold_html}
      </tbody>
    </table>
  </section>
</body>
</html>
"""
    with open(HTML_REPORT, "w") as file:
        file.write(html)


def try_make_matplotlib_pdf(rows):
    try:
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages
    except Exception:
        return False

    counts = pass_fail_counts(rows)
    threshold_table_rows = threshold_rows(rows)

    with PdfPages(PDF_REPORT) as pdf:
        fig, axes = plt.subplots(2, 1, figsize=(11, 8.5))
        signals = list(counts.keys())
        pass_counts = [counts[signal]["PASS"] for signal in signals]
        fail_counts = [counts[signal]["FAIL"] for signal in signals]
        x_values = range(len(signals))

        axes[0].bar(x_values, pass_counts, label="PASS", color="#16a34a")
        axes[0].bar(x_values, fail_counts, bottom=pass_counts, label="FAIL", color="#dc2626")
        axes[0].set_title("Receiver PASS/FAIL Counts")
        axes[0].set_xticks(list(x_values), signals, rotation=20, ha="right")
        axes[0].legend()

        for signal in signals:
            values = [int(row["value"]) for row in rows if row["signal"] == signal]
            axes[1].plot(values, marker="o", label=signal)
        axes[1].set_title("Observed Signal Values")
        axes[1].set_xlabel("Frame index per signal")
        axes[1].set_ylabel("Value")
        axes[1].legend(fontsize=8)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis("off")
        table_data = [
            [
                row["can_id"],
                row["signal"],
                row["pass_rule"],
                row["warning_rule"],
                row["fail_rule"],
                row["example_pass"],
                row["example_fail"],
            ]
            for row in threshold_table_rows
        ]
        table = ax.table(
            cellText=table_data,
            colLabels=[
                "CAN ID",
                "Signal",
                "PASS threshold",
                "Warning threshold",
                "FAIL threshold",
                "Example PASS",
                "Example FAIL",
            ],
            loc="center",
            cellLoc="left",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(8)
        table.scale(1, 1.6)
        ax.set_title("Page 2: Threshold Table", pad=20)
        pdf.savefig(fig)
        plt.close(fig)

    return True


def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    rows = read_rows(INPUT_FILE)
    if not rows:
        print("No rows found in", INPUT_FILE)
        return

    enriched = enrich_rows(rows)
    write_enriched_csv(enriched)
    make_html_report(enriched)
    made_pdf = try_make_matplotlib_pdf(enriched)

    print("Wrote", ENRICHED_CSV)
    print("Wrote", HTML_REPORT)
    if made_pdf:
        print("Wrote", PDF_REPORT)
    else:
        print("matplotlib is not installed, so PDF was skipped.")
        print("Open the HTML report in a browser and print/save as PDF if needed.")


if __name__ == "__main__":
    main()
