###################################################
# Automated Testing Framework for Network Analytics
#
# class for Kafka consumption
#
###################################################

from confluent_kafka.avro import AvroConsumer
from confluent_kafka import Consumer
import time, logging, json
from typing import List
logger = logging.getLogger(__name__)

class KMessageReader:

    def __init__(self, topic: str, dump_to_file: str=None, plainJson: bool=False):
        consumer_type = 'plain Json' if plainJson else 'avro'
        logger.info('Creating message reader (kafka ' + consumer_type + ' consumer) for topic ' + topic)
        self.topic = topic
        self.dumpfile = dump_to_file
        self.consumer = None
        self.plainJson = plainJson

    def connect(self):
        prop_dict = {
                'bootstrap.servers': 'localhost:9092',
                'security.protocol': 'PLAINTEXT',
                'group.id': 'smoke_test',
                'auto.offset.reset': 'earliest'
            }
        if self.plainJson:
            self.consumer = Consumer(prop_dict)
        else:
            prop_dict['schema.registry.url'] = 'http://localhost:8081'
            self.consumer = AvroConsumer(prop_dict)
        self.consumer.subscribe([self.topic])

    def disconnect(self):
        logger.debug('Message reader disconnect called')
        if self.consumer:
            logger.debug('Consumer exists')
            self.consumer.close()
            logger.debug('Consumer closed')
            self.consumer = None
        else:
            logger.debug('Consumer is already down')

    def __del__(self):
        logger.debug('Message reader destructor called')
        self.disconnect()


    def dump_if_needed(self, msgval: str):
        if not self.dumpfile:
            return
        with open(self.dumpfile, 'a') as f:
            f.write(msgval + '\n')


    # Receives as input the maximum time to wait and the number of expected messages
    # Returns a list of dictionaries representing the messages received, or None if fewer than expected messages
    # (or no messages at all) were received
    def get_messages(self, max_time_seconds: int, messages_expected: int) -> List[dict]:
        messages = []
        message_count = messages_expected
        time_start = round(time.time())
        time_now = round(time.time())
        while messages_expected>0 and time_now-time_start<max_time_seconds:
            msg = self.consumer.poll(5)
            if not msg or msg.error():
                logger.debug('No message from Kafka (or msg error), waiting (' + str(max_time_seconds-time_now+time_start) + ' seconds left)')
            else:
                # If avro, message value arrives as json and needs dumping; if not (plain json), then
                # it's in byte format and needs decoding
                msgval = msg.value().decode('utf-8') if self.plainJson else json.dumps(msg.value())
                self.dump_if_needed(msgval)
                logger.debug('Received message: ' + msgval)
                # If plain json, then dictionary is created simply by loading the decoded value of the message
                # If avro, then msg.value() is a dictionary already
                messages.append(json.loads(msgval) if self.plainJson else msg.value())
                messages_expected -= 1
                if messages_expected>0:
                    logger.debug('Waiting for ' + str(messages_expected) + ' more messages')
            time_now = round(time.time())
        if messages_expected<1:
            logger.info('Received the expected number of messages (' + str(message_count) + ')')
        if len(messages)<1:
            logger.warning('No messages read by kafka consumer in ' + str(max_time_seconds) + ' second(s)')
            return None
        if len(messages)<message_count:
            logger.warning('Received ' + str(len(messages)) + ' messages instead of ' + str(message_count))
            return None
        return messages


class KMessageReaderList(list):

    def getReaderOfTopicStartingWith(self, txt: str) -> KMessageReader:
        for consumer in self:
            if consumer.topic.startswith(txt):
                return consumer
        return None
