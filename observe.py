import logging

from opentelemetry._logs import set_logger_provider
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs.export import ConsoleLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

import os


logger_provider = LoggerProvider(
    resource=Resource.create(
        {
            "service.name": "artekmed",
            "service.instance.id": os.environ.get("OPENOBSERVE_NODE_NAME", "narvis"),
        }
    ),
)
set_logger_provider(logger_provider)

otlp_exporter = OTLPLogExporter(endpoint="http://collector:4317", insecure=True)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(otlp_exporter))

# console_exporter = ConsoleLogExporter()
# logger_provider.add_log_record_processor(BatchLogRecordProcessor(console_exporter))

handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)

