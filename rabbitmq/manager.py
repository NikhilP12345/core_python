# -*- coding: utf-8 -*-
import enum
import json
import logging
import time
from functools import wraps

from core.rabbitmq.event_metadata import EventMetadata
from core.rabbitmq.queue_helper import QueueHelper

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EventsManager:
    def __init__(
        self,
        name=None,
        amqp_uri=None,
        publisher_events_enum_class=None,
    ):
        if name is None:
            raise Exception("name cannot be None")

        if amqp_uri is None:
            raise Exception("amqp_uri cannot be None")

        if publisher_events_enum_class is None or not issubclass(
            publisher_events_enum_class, enum.Enum
        ):
            raise Exception(
                "publisher_events_enum_class is required and has to be a sub-class of enum.Enum"
            )

        self.__app_name = name
        self.__amqp_uri = amqp_uri

        self.publisher_events = publisher_events_enum_class

        if len(self.publisher_events) == 0:
            logger.warning(
                "No publisher events configured, will not be able to publish AMQP events"
            )

        self.__consumer_event_handlers = {}
        self.__consumer_started = False
        self.__consumer_setup_completed = False
        self.__publisher_setup_completed = False

    def setup_consumer(self):
        """
        Create / assert the service queue and event-specific exchanges, with their bindings
        """

        logger.info("Setting up consumer queue and exchanges...")

        if self.__consumer_setup_completed:
            logger.warning("Consumer has already been setup, will not setup again")
            return

        for consumer_event in self.__consumer_event_handlers:
            try:
                QueueHelper._addQueue(self.__app_name, consumer_event)
            except Exception:
                logger.exception(
                    "Failure in setting up exchange binding for exchange %s",
                    consumer_event,
                )
                raise

        self.__consumer_setup_completed = True

    def setup_publisher(self):
        """
        Create / assert the event-specific exchanges for the events published by this application
        """

        logger.info("Setting up publisher exchanges...")

        if self.__publisher_setup_completed:
            logger.warning("Publisher has already been setup, will not setup again")
            return

        for event_type_enum in self.publisher_events:
            try:
                QueueHelper._addExchange(event_type_enum.value)
            except Exception:
                logger.exception(
                    "Failure in setting up exchange for publisher event %s",
                    event_type_enum.value,
                )
                raise

        self.__publisher_setup_completed = True

    def publish(self, publisher_event_type, payload):
        """
        Method to publish events to RabbitMQ. Before any events are published,
        `self.setup_publisher` needs to be called.
        """

        if not self.__publisher_setup_completed:
            raise Exception("Publisher has not been setup, cannot publish events")

        if publisher_event_type not in self.publisher_events:
            # TODO: Determine whether this should raise an exception
            logger.error(
                "Attempted to publish unrecognized event <%s> with payload <%s>, ignoring",
                publisher_event_type,
                payload,
            )
            return None

        if type(payload) is not dict:
            # TODO: Determine whether this should raise an exception
            logger.error(
                "AMQP events expects a dict payload, %s given instead, ignoring",
                type(payload),
            )

        metadata = EventMetadata.from_event_type_enum(publisher_event_type)
        QueueHelper.publishMessage(
            metadata.event_type,
            json.dumps(payload, default=str),
            headers=metadata.get_amqp_headers(),
        )

        return metadata

    def add_handler(self, consumer_event_type, handler):
        if self.__consumer_started:
            raise Exception("Runtime addition of handler is currently not supported")

        if self.__consumer_setup_completed:
            raise Exception("Cannot add event handler after calling .setup_consumer")

        if consumer_event_type in self.__consumer_event_handlers:
            raise Exception(
                f"Another handler <{self.__consumer_event_handlers[consumer_event_type].__name__}> "
                f"already exists for event <{consumer_event_type}"
            )

        self.__consumer_event_handlers[consumer_event_type] = handler
        logger.info(
            "Added handler <%s> for event type <%s>",
            handler.__name__,
            consumer_event_type,
        )

    def handle(self, consumer_event_type):
        """
        Decorator method to add an event handler
        """

        def decorator(fn):
            @wraps(fn)
            def decorated(metadata, payload):
                return fn(metadata, payload)

            self.add_handler(consumer_event_type, decorated)

            return decorated

        return decorator

    def __process_event(self, channel, method_frame, properties, body):
        """
        Generic event handler to consume events from service queue and invoke the corresponding
        handler for the event.

        Before the consumer can handle any events, `self.setup_consumer` needs to be
        called (only once in the process's lifetime).
        """

        if not self.__consumer_setup_completed:
            raise Exception("Consumer has not been setup, cannot consume events")

        # Ignore unknown messages
        if method_frame.exchange not in self.__consumer_event_handlers:
            logger.warning(
                "Received unknown event from exchange <%s>, ingoring",
                method_frame.exchange,
            )
            channel.basic_reject(delivery_tag=method_frame.delivery_tag, requeue=False)
            return

        # Parse payload
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            logger.exception("Failure in parsing event body")
            channel.basic_reject(delivery_tag=method_frame.delivery_tag, requeue=False)
            return

        # Create metadata
        try:
            metadata = EventMetadata.from_amqp_message(method_frame, properties)
        except Exception:
            logger.exception("Failed to parse metadata")
            channel.basic_reject(delivery_tag=method_frame.delivery_tag, requeue=False)
            return

        handler = self.__consumer_event_handlers[metadata.event_type]

        try:
            event_processing_start_time = time.time()

            # Handle the event using the handler
            return_value = handler(metadata, payload)

            event_processing_total_time = time.time() - event_processing_start_time
            logger.info(
                "Handler <%s> took %.2f seconds to handle event <%s>",
                handler.__name__,
                event_processing_total_time,
                metadata.event_id,
            )

            if return_value is not None:
                logger.warning(
                    "Handler <%s> returned a value <%s>, however return values are "
                    "currently not supported",
                    handler.__name__,
                    return_value,
                )

            # ACK the event to prevent re-delivery
            channel.basic_ack(delivery_tag=method_frame.delivery_tag)

        except Exception:
            logger.exception(
                "Failure in handling event <%s> in handler <%s> for metadata <%s> and payload <%s>",
                metadata.event_type,
                handler.__name__,
                metadata,
                payload,
            )
            # TODO: Figure out the right behaviour for this failure
            channel.basic_reject(delivery_tag=method_frame.delivery_tag, requeue=True)
            return

    def setup_channel(self):
        logger.info("Establishing a channel to the queue...")
        QueueHelper._initChannel(self.__amqp_uri)

    def run_consumer(self):
        logger.info("Preparing to start consumer...")
        self.setup_channel()
        self.setup_consumer()
        self.setup_publisher()

        self.__consumer_started = True
        logger.info("Started consumer!")

        QueueHelper.startConsumer(self.__app_name, self.__process_event)

    def close_connection(self):
        QueueHelper.close_connection()    
