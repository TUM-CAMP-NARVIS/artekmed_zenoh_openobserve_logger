import time
import sys
import os
import zenoh
import logging
import argparse
import pathlib

#from observe import handler, logger_provider

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs.export import ConsoleLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from enum import Enum, auto
from dataclasses import dataclass, field
from pycdr2 import IdlStruct, IdlEnum
from pycdr2.types import int32, uint8, uint16, uint32, uint64, float32, float64, sequence, array

class LogLevelType(IdlEnum, typename="LogLevelType"):
    HL2_LOG_ERROR = auto()
    HL2_LOG_WARNING = auto()
    HL2_LOG_INFO = auto()
    HL2_LOG_DEBUG = auto()
    HL2_LOG_TRACE = auto()


@dataclass
class Time(IdlStruct, typename="Time"):
    sec: int32
    nanosec: uint32


@dataclass
class Duration(IdlStruct, typename="Duration"):
    sec: int32
    nanosec: uint32


@dataclass
class Header(IdlStruct, typename="Header"):
    stamp: Time
    frame_id: str


@dataclass
class LogItem(IdlStruct, typename="LogItem"):
    timestamp: Time
    severity: LogLevelType
    message: str


@dataclass
class LogMessage(IdlStruct, typename="LogMessage"):
    header: Header
    items: sequence[LogItem]


# Main function
def main():
    parser = argparse.ArgumentParser(description='Zenoh log-subscriber forwarding to openobserve.')
    parser.add_argument('--query', metavar='query', type=str, default='tcn/loc/*/*/str/logs',
                        help='query for retrieving the logs')
    parser.add_argument('--zenoh-config', metavar='zenoh_config', type=str, default='/config/zenoh_config.json5',
                        help='Zenoh Configuration File')
    parser.add_argument('--collector-url', metavar='collector_url', type=str, default='http://collector:4137',
                        help='Telemetry Collector URL')

    args = parser.parse_args()

    log_query = args.query
    collector_url = args.collector_url

    node_name = os.environ.get("OPENOBSERVE_NODE_NAME", "narvis")

    logging.basicConfig(level=logging.DEBUG)

    # create OTLP Logger
    logger_provider = LoggerProvider(
        resource=Resource.create(
            {
                "service.name": "artekmed",
                "service.instance.id": os.environ.get("OPENOBSERVE_NODE_NAME", "narvis"),
            }
        ),
    )
    set_logger_provider(logger_provider)

    otlp_exporter = OTLPLogExporter(endpoint=collector_url, insecure=True)
    logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))

    #console_exporter = ConsoleLogExporter()
    #logger_provider.add_log_record_processor(BatchLogRecordProcessor(console_exporter))

    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)


    # Attach OTLP handler to root logger
    logging.getLogger().addHandler(handler)
    logger = logging.getLogger(node_name)
    logger.setLevel(logging.DEBUG)

    zenoh_config_filepath = pathlib.Path(args.zenoh_config)
    if not zenoh_config_filepath.is_file():
        logger.error(f"Invalid Zenoh Configuration File: {zenoh_config_filepath}")
        exit(1)

    logger.info(f"Loading zenoh config from: {zenoh_config_filepath}")

    # @todo: maybe define max-log-level as cmdline arg and use LogLevelType to decide (debug vs. trace)

    # setup callbacks
    LVL_MAP = {}
    LVL_MAP[LogLevelType.HL2_LOG_ERROR] = logger.error
    LVL_MAP[LogLevelType.HL2_LOG_WARNING] = logger.warning
    LVL_MAP[LogLevelType.HL2_LOG_INFO] = logger.info
    LVL_MAP[LogLevelType.HL2_LOG_DEBUG] = logger.debug
    LVL_MAP[LogLevelType.HL2_LOG_TRACE] = logger.debug

    LVL = {}
    LVL[LogLevelType.HL2_LOG_ERROR] = logging.ERROR
    LVL[LogLevelType.HL2_LOG_WARNING] = logging.WARNING
    LVL[LogLevelType.HL2_LOG_INFO] = logging.INFO
    LVL[LogLevelType.HL2_LOG_DEBUG] = logging.DEBUG
    LVL[LogLevelType.HL2_LOG_TRACE] = logging.DEBUG

    # Log handler
    def log_handler(sample):
        try:
            message = LogMessage.deserialize(sample.payload.to_bytes())
            sender = message.header.frame_id
            for item in message.items:
                # print("{} >> {}".format(sender, item.message[:-1]))
                record = logger.makeRecord(node_name, LVL[item.severity], sender, 0, item.message[:-1],
                                           (), None, "log", None)
                logger.handle(record)
                # LVL_MAP[item.severity]("{} >> {}".format(sender, item.message[:-1]))
        except Exception as e:
            logger.error("Error while decoding the LogMessage.")


    # start Zenoh services
    zenoh.try_init_log_from_env()
    zenoh_connected = False
    while not zenoh_connected:
        try:
            session = zenoh.open(zenoh.Config.from_json5(open(zenoh_config_filepath, "r").read()))
            zenoh_connected = True
        except zenoh.ZError as e:
            logger.warn(f"Error connecting to zenoh router: {e}")
            logger.info("Waiting 2 seconds before retrying")
            time.sleep(2)
        except KeyboardInterrupt:
            exit(0)

    logger.info(f"Listening for logs on '{log_query}'")
    subscriber = session.declare_subscriber(log_query, log_handler)

    print("Enter 'q' or ctrl-c to quit...")
    try:
        c = '\0'
        while c != 'q':
            c = sys.stdin.read(1)
            if c == '':
                time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        subscriber.undeclare()
        logger.info("stop listening to logs")
        logger_provider.shutdown()


if __name__ == "__main__":
    main()
