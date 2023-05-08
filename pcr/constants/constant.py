from enum import IntEnum

class Command(IntEnum):
    NOP         = 0x00,
    TASK_WRITE  = 0x01,
    TASK_END    = 0x02,
    GO          = 0x03,
    STOP        = 0x04,
    PARAM_WRITE = 0x05,
    PARAM_END   = 0x06,
    PAUSE       = 0x07,
    CONTINUE    = 0x08,
    BOOTLOADER  = 0x55

class State(IntEnum):
    READY           = 0x01,
    RUN             = 0x02,
    PCREND          = 0x03,
    STOP            = 0x04,
    TASK_WRITE      = 0x05,
    TASK_READ       = 0x06,
    ERROR           = 0x07,
    REFRIGERATION   = 0x08,
    PAUSE           = 0x09,
    INCREASE        = 0x10

class StateOper(IntEnum):
    INIT             = 0x00,
    COMPLETE         = 0x01,
    INCOMPLETE       = 0x02,
    RUN_REFRIGERATOR = 0x03