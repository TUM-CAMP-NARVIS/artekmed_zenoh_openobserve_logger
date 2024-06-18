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
