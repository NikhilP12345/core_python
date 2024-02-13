import logging

import pika
from pika.exceptions import AMQPConnectionError
from pika.exchange_type import ExchangeType
from retry import retry

LOG_FORMAT = "%(levelname)s %(asctime)s %(name)s %(funcName)s %(lineno)d: %(message)s"
LOGGER = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)


class QueueHelper:

    _channel = None
    _connection = None
    _amqpURI = None
    _offlinePubMessages = []
    _prefetchCount = 10
    _messageExpiry = 36000

    @staticmethod
    @retry(
        exceptions=AMQPConnectionError,
        delay=5,
        max_delay=120,
        backoff=1.2,
        logger=LOGGER,
    )
    def _initChannel(_amqp_uri=None):
        if QueueHelper._amqpURI is None:
            QueueHelper._amqpURI = _amqp_uri
        if QueueHelper._amqpURI is None:
            raise Exception(
                "AMQP URI is required for QueueHelper to connect to RabbitMQ"
            )
        LOGGER.info(f"_amqp_uri : {QueueHelper._amqpURI}")
        parameters = pika.URLParameters(QueueHelper._amqpURI)

        LOGGER.info(f"parameters :{parameters} ")

        # TODO: Need to handle RabbitMQ connection blocks, maybe by adding `blocked_connection_timeout``
        QueueHelper._connection = pika.BlockingConnection(parameters)
        QueueHelper._channel = QueueHelper._connection.channel()

        # Adding prefetch count to channel
        QueueHelper._channel.basic_qos(
            prefetch_count=QueueHelper._prefetchCount,
        )

        # Clear offline messages
        QueueHelper._clearOfflineMessages()

    @staticmethod
    def _addExchange(exchangeName, exchangeType=ExchangeType.fanout):
        if QueueHelper._channel is None:
            raise Exception("Need to _initChannel before adding exchange")

        # Declare exchange as durable to survive restart
        QueueHelper._channel.exchange_declare(
            exchange=exchangeName,
            exchange_type=exchangeType,
            durable=True,
        )

    @staticmethod
    def _addQueue(
        queueName,
        exchangeName,
        deadLetterExchange=False,
        messageTtl=_messageExpiry,
        routing_key="",
    ):
        if QueueHelper._channel is None:
            raise Exception("Need to _initChannel before adding queue")

        if exchangeName is not None:
            QueueHelper._addExchange(exchangeName)

        QueueHelper._channel.queue_declare(queue=queueName, durable=True)
        QueueHelper._channel.queue_bind(queueName, exchangeName, routing_key)

    @staticmethod
    def _clearOfflineMessages():
        LOGGER.info("Clearing queued messages")

        while len(QueueHelper._offlinePubMessages) > 0:
            msg_kwargs = QueueHelper._offlinePubMessages.pop(0)
            QueueHelper.publishMessage(msg_kwargs.get("exchange"), msg_kwargs.get("body"), msg_kwargs.get("headers"), msg_kwargs.get("routing_key"))

    @staticmethod
    def publishMessage(exchangeName, message, headers=None, routing_key=""):
        msg_kwargs = dict(
            exchange=exchangeName,
            routing_key=routing_key,
            body=message,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
                headers=headers or {},
            ),
        )

        try:
            # deliver_mode = 2 for persistent message
            QueueHelper._channel.basic_publish(**msg_kwargs)
        except AMQPConnectionError as e:
            LOGGER.exception(f"Message publish failed : {e}")
            msg_kwargs['headers'] = headers
            QueueHelper._offlinePubMessages.append(msg_kwargs)
            QueueHelper._initChannel()
        except Exception as e:
            LOGGER.exception(f"Reconnection Failed : {e}")
            msg_kwargs['headers'] = headers
            QueueHelper._offlinePubMessages.append(msg_kwargs)
            QueueHelper._initChannel()
            LOGGER.exception("Message publish failed")

    @staticmethod
    def startConsumer(queueName, processingFunction):
        # This function needs raise an Exception if it cannot connect, as it
        # serves as an entrypoint

        if QueueHelper._channel is None:
            raise Exception("Consumer channel has not been initialized")

        QueueHelper._channel.basic_consume(
            queue=queueName,
            on_message_callback=processingFunction,
        )

        while True:
            try:
                QueueHelper._channel.start_consuming()
            except AMQPConnectionError:
                LOGGER.exception("AMQPConnectionError, reconnecting...")
                QueueHelper._initChannel()
            except Exception:
                LOGGER.exception(f"Error in consuming message from queue {queueName}")

    @staticmethod
    def close_connection():
        LOGGER.info("Closing Rabbit Mq Connection")
        QueueHelper._channel.close()
        LOGGER.info("Rabbit Mq Connection Closed")