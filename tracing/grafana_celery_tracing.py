from flask import Flask
from loguru import logger
from common.exception import CoreApi

from common.logger import *
from common.tracing import *
from views.hello import HelloHandler


# Initialize your Flask app
app = Flask(__name__)
# Setup tracing and logging
setup_tracing(service_name="example_service")
add_trace_context_to_loguru()

api = CoreApi(app, catch_all_404s=True)


HelloHandler.init(api)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
