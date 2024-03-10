from flask_restful import Resource, abort, request
from opentelemetry import trace, propagate
from loguru import logger
from decorators import trace_function
import json

def json_parse(obj_str=None):
	if obj_str is not None and isinstance(obj_str, (str, bytes, bytearray)) and len(obj_str.strip())>0:
		try:
			return json.loads(obj_str)
		except Exception:
			return None
	else:
		return None

class TestHandler(Resource):


    @trace_function("get_test")
    def post(self):
        try:
            a = json_parse(request.data)
            logger.info(f"Getting payload to test  -> {a}")
            return "Test, World!"
        except Exception as error:
            logger.error(str(error))
            return "Test, World!"
        
    @staticmethod
    def init(api):
        api.add_resource(TestHandler, '/test')
