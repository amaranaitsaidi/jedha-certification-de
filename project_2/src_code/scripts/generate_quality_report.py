"""
Generate Data Quality Report
============================
Génère un rapport HTML de qualité des données à partir des tests.
"""

import json
import os
from datetime import datetime
from pathlib import Path


def generate_html_report(json_report_path: str, output_path: str = None):
    """
    Générer un rapport HTML à partir des résultats JSON.

    Args:
        json_report_path: Chemin vers le rapport JSON
        output_path: Chemin de sortie pour le HTML (optionnel)
    """
    with open(json_report_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    if output_path is None:
        output_path = json_report_path.replace('.json', '.html')

    summary = results['summary']
    tests = results['tests']

    # Calculate success rate
    success_rate = (summary['passed'] / summary['total'] * 100) if summary['total'] > 0 else 0

    # Determine overall status
    if success_rate == 100:
        status_color = '#28a745'
        status_text = 'EXCELLENT'
    elif success_rate >= 80:
        status_color = '#ffc107'
        status_text = 'GOOD'
    else:
        status_color = '#dc3545'
        status_text = 'NEEDS ATTENTION'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Data Quality Report - Amazon Reviews ETL</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}

        .stat-card .number {{
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}

        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .stat-card.total .number {{ color: #667eea; }}
        .stat-card.passed .number {{ color: #28a745; }}
        .stat-card.failed .number {{ color: #dc3545; }}
        .stat-card.rate .number {{ color: {status_color}; }}

        .status-badge {{
            display: inline-block;
            background: {status_color};
            color: white;
            padding: 10px 30px;
            border-radius: 50px;
            font-weight: bold;
            margin: 20px 0;
        }}

        .tests {{
            padding: 40px;
        }}

        .test-item {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 25px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }}

        .test-item:hover {{
            border-color: #667eea;
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.1);
        }}

        .test-item.passed {{
            border-left: 5px solid #28a745;
        }}

        .test-item.failed {{
            border-left: 5px solid #dc3545;
        }}

        .test-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .test-name {{
            font-size: 1.3em;
            font-weight: bold;
            color: #333;
        }}

        .test-badge {{
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
        }}

        .test-badge.passed {{
            background: #d4edda;
            color: #155724;
        }}

        .test-badge.failed {{
            background: #f8d7da;
            color: #721c24;
        }}

        .test-details {{
            color: #666;
            line-height: 1.8;
        }}

        .test-details strong {{
            color: #333;
        }}

        .footer {{
            background: #f8f9fa;
            padding: 20px 40px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e9ecef;
        }}

        .progress-bar {{
            height: 30px;
            background: #e9ecef;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, {status_color} 0%, {status_color} 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 1s ease;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Data Quality Report</h1>
            <p>Amazon Reviews ETL Pipeline</p>
            <p style="opacity: 0.7; margin-top: 10px;">{results['timestamp']}</p>
        </div>

        <div class="summary">
            <div class="stat-card total">
                <div class="number">{summary['total']}</div>
                <div class="label">Total Tests</div>
            </div>
            <div class="stat-card passed">
                <div class="number">{summary['passed']}</div>
                <div class="label">Passed</div>
            </div>
            <div class="stat-card failed">
                <div class="number">{summary['failed']}</div>
                <div class="label">Failed</div>
            </div>
            <div class="stat-card rate">
                <div class="number">{success_rate:.1f}%</div>
                <div class="label">Success Rate</div>
            </div>
        </div>

        <div style="text-align: center; padding: 20px; background: #f8f9fa;">
            <span class="status-badge">STATUS: {status_text}</span>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {success_rate}%;">
                    {success_rate:.1f}%
                </div>
            </div>
        </div>

        <div class="tests">
            <h2 style="margin-bottom: 30px; color: #333;">Detailed Test Results</h2>
"""

    # Add test details
    for test_name, test_data in tests.items():
        status = 'passed' if test_data['success'] else 'failed'
        badge_text = 'OK PASSED' if test_data['success'] else 'X FAILED'

        html += f"""
            <div class="test-item {status}">
                <div class="test-header">
                    <div class="test-name">{test_name.replace('_', ' ').title()}</div>
                    <div class="test-badge {status}">{badge_text}</div>
                </div>
                <div class="test-details">
"""

        # Add details
        details = test_data['details']
        if 'error' in details:
            html += f"<p><strong>Error:</strong> {details['error']}</p>"
        elif 'message' in details:
            html += f"<p>{details['message']}</p>"
        else:
            for key, value in details.items():
                if key not in ['expectation_result']:
                    html += f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value:,}" if isinstance(value, (int, float)) else f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>"

        html += """
                </div>
            </div>
"""

    html += f"""
        </div>

        <div class="footer">
            <p>Generated by Amazon Reviews ETL Pipeline</p>
            <p style="margin-top: 5px; font-size: 0.9em;">Powered by Great Expectations</p>
        </div>
    </div>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"\nOK HTML report generated: {output_path}")
    return output_path


def main():
    """Main function."""
    # Find the latest report
    reports_dir = Path(__file__).parent.parent / 'reports'
    json_files = list(reports_dir.glob('data_quality_report*.json'))

    if not json_files:
        print("No JSON report found. Run tests first: python tests/test_data_quality.py")
        return

    latest_report = max(json_files, key=lambda p: p.stat().st_mtime)
    print(f"Generating HTML report from: {latest_report}")

    generate_html_report(str(latest_report))


if __name__ == "__main__":
    main()
