# -*- coding: utf-8 -*-
"""RabbitMQ helper for publishing"""
from time import sleep

from pika.exchange_type import ExchangeType
from queue_helper import QueueHelper


class SamplePublisher(object):
    def init(self):
        # Create Connection (need to be done only once)
        QueueHelper._initPublisherChannel("amqp://guest:guest@127.0.0.1:5672/%2F")

        # Start Publisher
        QueueHelper.startPublisher(self.startPublisher)

    def startPublisher(self):
        # Add exchange
        QueueHelper._addExchange(
            exchangeName="Test_Exchange_1",
            exchangeType=ExchangeType.fanout,
            connectionMode="publisher",
        )

    def publishMessage(self, publishMessage):
        if publishMessage is not None:
            print("Published message")
            QueueHelper.publishMessage(
                exchangeName="Test_Exchange_1", message=publishMessage
            )


def main():

    # Connect to localhost:5672 as guest with the password guest and virtual host "/" (%2F)
    samplePublisher = SamplePublisher()
    samplePublisher.init()

    message = "Message Number"
    for i in range(1, 100):
        sleep(2)
        publishMessage = message + " : " + str(i)
        print(f"Sent message: {publishMessage}")
        try:
            samplePublisher.publishMessage(publishMessage)
        except Exception as ex:
            print(f"Error in publishing : {ex}")


main()
