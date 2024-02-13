import enum
import logging

import config
from config.configutils import build_ampq_uri
from rabbitmq.manager import EventsManager

logger = logging.getLogger(__name__)

events_amqp_uri = build_ampq_uri(
    config.EVENTS_AMQP_HOST,
    config.EVENTS_AMQP_PORT,
    config.EVENTS_AMQP_VHOST,
    config.EVENTS_AMQP_USER,
    config.EVENTS_AMQP_PASSWORD,
)

class PublisherEventsEnum(enum.Enum):
    SAMPLE_EVENT = "sample-event"
    SAMPLE_EVENT_2 = "sample-event-2"

    # DriverInvoice
    DRIVER_INVOICE_STATUS_UPDATE_EVENT = "driver-invoice-status-update-event"


def get_new_event_manager_instance():
    logger.info("Starting Events Frame Work")
    
    events_app = EventsManager(
      config.EVENTS_APPNAME,
      events_amqp_uri,
      publisher_events_enum_class=PublisherEventsEnum,
    )

    events_app.setup_channel()
    events_app.setup_publisher()

    return events_app