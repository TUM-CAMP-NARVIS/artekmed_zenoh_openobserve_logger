import time
import sys
import os
import zenoh
import logging
import argparse

from observe import handler, logger_provider

import schema


# Main function
def main():
    parser = argparse.ArgumentParser(description='Zenoh log-subscriber forwarding to openobserve.')
    parser.add_argument('--query', metavar='query', type=str, default='tcn/loc/*/*/str/logs',
                        help='query for retrieving the logs')
    parser.add_argument('--zenoh-config', metavar='zenoh_config', type=str, default='/config/zenoh_config.json5',
                        help='Zenoh Configuration File')

    args = parser.parse_args()

    log_query = args.query

    node_name = os.environ.get("OPENOBSERVE_NODE_NAME", "narvis")
    # Attach OTLP handler to root logger
    logging.getLogger().addHandler(handler)
    logger = logging.getLogger(node_name)
    logger.setLevel(logging.DEBUG)

    zenoh_config_filepath = pathlib.Path(args.zenoh_config)
    if not zenoh_config_filepath.is_file():
        logger.error(f"Invalid Zenoh Configuration File: {zenoh_config_filepath}")
        exit(1)

    # @todo: maybe define max-log-level as cmdline arg and use LogLevelType to decide (debug vs. trace)

    # setup callbacks
    LVL_MAP = {}
    LVL_MAP[schema.LogLevelType.HL2_LOG_ERROR] = logger.error
    LVL_MAP[schema.LogLevelType.HL2_LOG_WARNING] = logger.warning
    LVL_MAP[schema.LogLevelType.HL2_LOG_INFO] = logger.info
    LVL_MAP[schema.LogLevelType.HL2_LOG_DEBUG] = logger.debug
    LVL_MAP[schema.LogLevelType.HL2_LOG_TRACE] = logger.debug

    LVL = {}
    LVL[schema.LogLevelType.HL2_LOG_ERROR] = logging.ERROR
    LVL[schema.LogLevelType.HL2_LOG_WARNING] = logging.WARNING
    LVL[schema.LogLevelType.HL2_LOG_INFO] = logging.INFO
    LVL[schema.LogLevelType.HL2_LOG_DEBUG] = logging.DEBUG
    LVL[schema.LogLevelType.HL2_LOG_TRACE] = logging.DEBUG

    # Log handler
    def log_handler(sample):
        try:
            message = schema.LogMessage.deserialize(sample.payload)
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
    zenoh.init_logger()
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
