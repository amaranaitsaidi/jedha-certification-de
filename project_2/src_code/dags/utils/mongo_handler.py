import logging
from pymongo import MongoClient
from datetime import datetime

class MongoHandler(logging.Handler):
    def __init__(self, uri, db_name="airflow_logs", collection="logs"):
        super().__init__()
        self.client = MongoClient(uri)
        self.collection = self.client[db_name][collection]

    def emit(self, record):
        log_entry = self.format(record)
        data = {
            "message": log_entry,
            "level": record.levelname,
            "logger": record.name,
            "timestamp": datetime.utcnow(),
            "dag_id": getattr(record, "dag_id", None),
            "task_id": getattr(record, "task_id", None),
            "run_id": getattr(record, "run_id", None)
        }
        self.collection.insert_one(data)
