from flask_restful import Resource, abort, request
from celery_module.tasks import printHello
from opentelemetry import trace, propagate
from loguru import logger
# from decorators import trace_function
import json
import requests

class HelloHandler(Resource):
    # @trace_function("sumHelper")
    def sumHelper(self):
        logger.info("In sumHelper")
        return (4, 2)

    # @trace_function("get_hello")
    def get(self):
        try:
            a = self.sumHelper()
            task_payload = {'x': a[0], 'y': a[1]}

            # trace_context = {}
            # propagate.inject(trace_context)

            full_payload = {
                'task_payload': task_payload,
                # 'trace_context': trace_context,
                'name': "abc"
            }
            logger.info(f"Sending payload to queue -> {full_payload}")
            printHello.delay(full_payload)
            url = "http://127.0.0.1:8081/test"

            payload = json.dumps(full_payload)
            headers = {
            'Content-Type': 'application/json'
            }

            response = requests.request("POST", url, headers=headers, data=payload)

            return response.text
            # return "Hello, World!"
        except Exception as error:
            logger.error(str(error))
            return "Hello, World!"
        
    @staticmethod
    def init(api):
        api.add_resource(HelloHandler, '/hello/name')
