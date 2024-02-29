from celery_module.celery import app
from loguru import logger




@app.task(bind=True)
def printSum(self, full_payload):
    task_payload = full_payload['task_payload']
    x, y = task_payload['x'], task_payload['y']
    z = x + y
    logger.info({"sum": f"sum is : {z}"})
