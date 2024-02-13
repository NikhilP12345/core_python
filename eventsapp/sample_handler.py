import logging

from rabbitmq.event_metadata import EventMetadata
from eventsapp import PublisherEventsEnum, app

logger = logging.getLogger(__name__)


@app.handle("sample-event")
def handle_sample_event(metadata: EventMetadata, payload):
    logger.info("Received event in sample event handler")
    logger.info("Metadata: %s", metadata)
    logger.info("Payload: %s", payload)

    sample_event_2_payload = {"sample_event_id": metadata.event_id}
    logger.info("Pushing a sample-event-2 with payload %s", sample_event_2_payload)

    metadata = app.publish(PublisherEventsEnum.SAMPLE_EVENT_2, sample_event_2_payload)
    logger.info("Published sample-event-2 with metadata %s", metadata)


@app.handle("sample-event-2")
def handle_sample_event_2(metadata, payload):
    logger.info("Received event in sample event 2 handler")
    logger.info("Metadata: %s", metadata)
    logger.info("Payload: %s", payload)
