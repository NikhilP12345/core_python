
import time
import requests
import json
from loguru import logger


def loki_sink(message):
    print(message)
    timestamp_ns = str(int(time.time() * 1e9))  # Current timestamp in nanoseconds
    log_level = message.record["level"].name
    log_message = message.record["message"]
    log_time = message.record["time"].isoformat() 
    data = {
        "streams": [
            {
                "stream": {
                    "service": "example_service",
                    "job": "bot_python",
                    "task_id": "2022-03-01",
                    "type": "execution",
                    "log_level": log_level,
                    "otel_trace_id": message.record["extra"].get("otel_trace_id", "0"*32)
                },
                "values": [
                    [timestamp_ns, f"message: {log_message}"]
                ]
            }
        ]
    }
    print(data)
    headers = {
        "Content-type": "application/json"
    }
    url = "http://localhost:3101/loki/api/v1/push"
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code != 204:
            print(f"Failed to send log to Loki: {response.text}")
        print(response.__dict__)
        pass
    except Exception as e:
        print(f"Error sending log to Loki: {e}")

logger.add(loki_sink, format="{time} {level} {message}", level="INFO")
