import json
import logging
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        try:
            data = json.loads(record.getMessage())
        except (json.JSONDecodeError, ValueError):
            data = {
                "message": record.getMessage(),
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
            }
        data.update({
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        })
        return json.dumps(data)