# -*- coding: utf-8 -*-
"""RabbitMQ helper for publishing"""
from queue_helper import QueueHelper


class SampleConsumer(object):
    def init(self):
        # Create Connection (need to be done only once)
        QueueHelper._initConsumerChannel("amqp://guest:guest@127.0.0.1:5672/%2F")

        # Start Consumer
        QueueHelper.startConsumer(self.startConsumer)

        # Attach Consuming Function
        QueueHelper.startConsumer(self.startConsuming)

    def startConsumer(self):
        # Add exchange
        QueueHelper._addQueue(
            queueName="Test_Queue_1",
            exchangeName="Test_Exchange_1",
            connectionMode="consumer",
        )

    def startConsuming(self):
        # Add Consuming Function
        QueueHelper.consumeMessage(
            queueName="Test_Queue_1", processingFunction=self.consumerFunc
        )

    def consumerFunc(self, ch, method, properties, body):
        # Consume message here
        print(f"In consumerFunc with message : {body}")
        ch.basic_ack(delivery_tag=method.delivery_tag)
