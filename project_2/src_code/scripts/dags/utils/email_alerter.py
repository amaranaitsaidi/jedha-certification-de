"""Email Alerter for ETL Pipeline"""

import logging
import os
from typing import Dict, Optional
from airflow.utils.email import send_email
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailAlerter:

    def __init__(self, to_emails: list, from_email: str = None):
        self.to_emails = to_emails if isinstance(to_emails, list) else [to_emails]
        self.from_email = from_email or os.getenv("AIRFLOW__SMTP__SMTP_MAIL_FROM", "airflow@example.com")

    def send_alert(self, subject: str, html_content: str, **context):
        try:
            logger.info(f"Sending email alert to {self.to_emails}")

            send_email(
                to=self.to_emails,
                subject=subject,
                html_content=html_content
            )

            logger.info("[OK] Email alert sent successfully")
            return True

        except Exception as e:
            logger.error(f"[FAIL] Failed to send email alert: {e}")
            return False

    def alert_no_data_from_s3(self, dag_id: str, task_id: str, execution_date: str,
                               tables: Dict[str, Optional[str]], **context):

        failed_tables = [name for name, uri in tables.items() if uri is None]
        total_tables = len(tables)
        failed_count = len(failed_tables)

        subject = f"[ALERT] ETL Pipeline - No Data Extracted to S3 ({failed_count}/{total_tables} tables failed)"

        html_content = f"""
        <html>
        <body>
            <h2 style="color: #d32f2f;">ALERT: S3 Extraction Failure</h2>

            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>DAG:</strong> {dag_id}</p>
            <p><strong>Task:</strong> {task_id}</p>
            <p><strong>Execution Date:</strong> {execution_date}</p>

            <h3>Summary</h3>
            <p style="color: #d32f2f; font-weight: bold;">
                {failed_count} out of {total_tables} tables failed to extract to S3
            </p>

            <h3>Failed Tables:</h3>
            <ul>
                {''.join(f'<li style="color: #d32f2f;">{table}</li>' for table in failed_tables)}
            </ul>

            <h3>Action Required:</h3>
            <ul>
                <li>Check PostgreSQL source database connectivity</li>
                <li>Verify AWS S3 credentials and permissions</li>
                <li>Review Airflow logs for detailed error messages</li>
            </ul>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Automated alert from ETL Pipeline monitoring system.
            </p>
        </body>
        </html>
        """

        return self.send_alert(subject, html_content, **context)

    def alert_no_data_to_snowflake(self, dag_id: str, task_id: str, execution_date: str,
                                     rows_inserted: int = 0, **context):

        subject = f"[ALERT] ETL Pipeline - No Data Loaded to Snowflake"

        html_content = f"""
        <html>
        <body>
            <h2 style="color: #d32f2f;">ALERT: Snowflake Load Failure</h2>

            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>DAG:</strong> {dag_id}</p>
            <p><strong>Task:</strong> {task_id}</p>
            <p><strong>Execution Date:</strong> {execution_date}</p>

            <h3>Summary</h3>
            <p style="color: #d32f2f; font-weight: bold;">
                Zero rows were inserted into Snowflake
            </p>

            <h3>Possible Causes:</h3>
            <ul>
                <li>No data available in S3 source files</li>
                <li>Data validation rejected all records</li>
                <li>Snowflake connection failure</li>
            </ul>

            <h3>Action Required:</h3>
            <ul>
                <li>Check S3 source files for data</li>
                <li>Review data validation rules</li>
                <li>Verify Snowflake credentials</li>
                <li>Check Airflow logs for errors</li>
            </ul>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Automated alert from ETL Pipeline monitoring system.
            </p>
        </body>
        </html>
        """

        return self.send_alert(subject, html_content, **context)

    def alert_missing_s3_files(self, dag_id: str, task_id: str, execution_date: str,
                                 tables: Dict[str, Optional[str]], **context):

        failed_tables = [name for name, df in tables.items() if df is None]
        total_tables = len(tables)
        failed_count = len(failed_tables)

        subject = f"[ALERT] ETL Pipeline - Missing S3 Files ({failed_count}/{total_tables} tables failed)"

        html_content = f"""
        <html>
        <body>
            <h2 style="color: #d32f2f;">ALERT: S3 Files Missing or Unreadable</h2>

            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>DAG:</strong> {dag_id}</p>
            <p><strong>Task:</strong> {task_id}</p>
            <p><strong>Execution Date:</strong> {execution_date}</p>

            <h3>Summary</h3>
            <p style="color: #d32f2f; font-weight: bold;">
                {failed_count} out of {total_tables} tables could not be loaded from S3
            </p>

            <h3>Failed Tables:</h3>
            <ul>
                {''.join(f'<li style="color: #d32f2f;">{table}</li>' for table in failed_tables)}
            </ul>

            <h3>Possible Causes:</h3>
            <ul>
                <li>Files not present in S3 bucket (extraction failed)</li>
                <li>Incorrect S3 path or bucket name</li>
                <li>AWS credentials issue</li>
                <li>Files corrupted or invalid format</li>
            </ul>

            <h3>Action Required:</h3>
            <ul>
                <li>Check if extraction DAG completed successfully</li>
                <li>Verify files exist in S3 bucket: a-ns-bucket/raw/</li>
                <li>Review Airflow logs for detailed error messages</li>
                <li>Verify AWS S3 credentials and permissions</li>
            </ul>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Automated alert from ETL Pipeline monitoring system.
            </p>
        </body>
        </html>
        """

        return self.send_alert(subject, html_content, **context)

    def alert_pipeline_success(self, dag_id: str, execution_date: str,
                                stats: Dict, **context):

        subject = f"[SUCCESS] ETL Pipeline Completed - {dag_id}"

        html_content = f"""
        <html>
        <body>
            <h2 style="color: #388e3c;">ETL Pipeline Completed Successfully</h2>

            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>DAG:</strong> {dag_id}</p>
            <p><strong>Execution Date:</strong> {execution_date}</p>

            <h3>Statistics</h3>
            <ul>
                <li><strong>Rows Loaded to Snowflake:</strong> {stats.get('snowflake_inserts', 'N/A'):,}</li>
                <li><strong>Rejected Records (MongoDB):</strong> {stats.get('mongodb_inserts', 'N/A'):,}</li>
            </ul>

            <p style="color: #666; font-size: 12px; margin-top: 30px;">
                Automated notification from ETL Pipeline monitoring system.
            </p>
        </body>
        </html>
        """

        return self.send_alert(subject, html_content, **context)
