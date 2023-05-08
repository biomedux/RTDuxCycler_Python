from ctypes import create_string_buffer
from pcr.constants.constant import Command

from pcr import logger

# GOTO 
AF_GOTO				= 250
# Tx_buffer size is 65
TX_BUFSIZE          = 65

# Tx_buffer index definitions
TX_CMD              = 1;    TX_ACTNO            = 2
TX_TEMP			    = 3;    TX_TIMEH			= 4
TX_TIMEL			= 5;    TX_LIDTEMP			= 6
TX_REQLINE			= 7;    TX_CURRENT_ACT_NO 	= 8
TX_BOOTLOADER		= 10


def make_nop():
    """All zero"""
    return create_string_buffer(TX_BUFSIZE)

def make_taskWrite(action, preheat, line):
    """Return TASK_WRITE buffer
    
    Args:
        action: One line(action) of PCR Protocol object(actions)
        preheat: Preheat temperature
        line: Line number of PCR protocol

    Note:
        param 'action' name is not clear... It can be confused like rx_action, tx_action
    """
    buffer = create_string_buffer(TX_BUFSIZE)
    # label = AF_GOTO if action['Label'] == 'GOTO' else int(action['Label'])
    # temp = int(action['Temp']); time = int(action['Time'])

    buffer[TX_CMD] = Command.TASK_WRITE
    buffer[TX_ACTNO] = AF_GOTO if action['Label'] == 'GOTO' else action['Label']
    buffer[TX_TEMP] = action['Temp']
    buffer[TX_TIMEH] = action['Time'] >> 8
    buffer[TX_TIMEL] = action['Time'] & 0xFF
    buffer[TX_LIDTEMP] = preheat
    buffer[TX_REQLINE] = line
    buffer[TX_CURRENT_ACT_NO] = line
    
    return buffer

def make_taskEnd():
    """Retrun TASK_END buffer"""
    buffer = create_string_buffer(TX_BUFSIZE)
    buffer[TX_CMD] = Command.TASK_END
    return buffer

def make_go():
    """Return Go buffer"""
    buffer = create_string_buffer(TX_BUFSIZE)
    buffer[TX_CMD] = Command.GO
    return buffer

def make_stop():
    """Return STOP buffer"""
    buffer = create_string_buffer(TX_BUFSIZE)
    buffer[TX_CMD] = Command.STOP
    return buffer

def make_bootLoader():
    """Return BOOTLOADER buffer
    
    Note:
        Boot loader mod is not implemented yet...
    """
    buffer = create_string_buffer(TX_BUFSIZE)
    buffer[TX_CMD] = Command.BOOTLOADER
    return buffer

def make_requestLine(request_line):
    """Return REQUEST_LINE buffer
    
    Args:
        request_line: Line number of already written PCR protocol in Duxcycler. It must be Integer
    """
    buffer = create_string_buffer(TX_BUFSIZE)
    buffer[TX_REQLINE] = request_line
    return buffer