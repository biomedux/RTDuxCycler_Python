from email.policy import default
import os
import pcr.constants.constant as constant
from ctypes import windll

# Path definitions
PCR_PATH = "C:/mPCR"
PROTOCOL_PATH = PCR_PATH + "/protocols"
RECENT_PROTOCOL_FILENAME = "recent_protocol_python.txt"


class Protocol():
    """사용중인 PCR Protocol 관리를 위한 클래스

    Params:
        name: `str`
            Protocol name
        actions: `list`
            A list of actions(lines) in the PCR Protocol

    Note:
        The parameter 'actions' must be shaped with multiple `dict` like this.
        [
            {'Label' : 1, 'Temp' : 60, 'Time' : 5},
            {'Label' :'GOTO','Temp' : 2,'Time' : 1},
            ...
        ]
    """
    def __init__(self, name, actions):
        self.name = name
        self.actions = actions

    def __getitem__(self, idx):
        return self.actions[idx]
    
    def __str__(self):
        _str = 'name : ' + self.name + '\n'
        for action in self.actions:
            _str += f'Label : {action["Label"]:>4}, Temp : {action["Temp"]:>3}, Time : {action["Time"]:>3}\n'
        return _str

    def __len__(self):
        return len(self.actions)

# Default pcr protocol actions
default_protocol = Protocol('Default', [
    {'Label' : 1, 'Temp' : 60, 'Time' : 5}, 
    {'Label' : 2, 'Temp' : 90, 'Time' : 5}, 
    {'Label' : 3, 'Temp' : 65, 'Time' : 5},
    {'Label' :'GOTO','Temp' : 2,'Time' : 2},
    {'Label' : 4, 'Temp' : 40, 'Time' : 5}
])

# PCR Protocol Error definitions
class PCRProtocolError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg

def list_protocols():
    """Return list of *.txt file(protocol file) names
    """
    # filtering extension
    files = list(filter(lambda x : x[-4:] == '.txt', os.listdir(PROTOCOL_PATH)))
    protocols = [file[:-4] for file in files]   # slicing extension
    return protocols

def save_protocol(protocol):
    path = os.path.join(PROTOCOL_PATH, protocol.name) # protocol path
    try:
        actions = check_protocol(protocol)    # check protocol
    except PCRProtocolError as err:
        windll.user32.MessageBoxW(0, f"{err}", u"PCR Protocol error", 0)

    with open(path, 'w') as file:   # open protocol file
        # actions to text list ('label'\t'temp'\t'time')
        lines = ['{}\t{}\t{}'.format(*action.values()).strip() for action in actions]
        # write text list
        file.write('\n'.join(lines))

def load_protocol(protocol_name):
    path = os.path.join(PROTOCOL_PATH, protocol_name) # protocol path

    with open(path + ".txt", 'r') as file:   # open protocol file
        protocol_keys = ['Label', 'Temp', 'Time'] # protocol keys 
        lines = file.read().strip().split('\n')   # read text lines
        # list to dict (text to actions)  
        actions = [dict(zip(protocol_keys, line.split('\t'))) for line in lines] 
        # check protocol and return protocol
        try:
            actions = check_protocol(actions)
        except PCRProtocolError as err:
            windll.user32.MessageBoxW(0, f"{err}", u"PCR Protocol error", 0)
            # If rasied error while loading Protocol..
            # Set default protocol...
            return default_protocol

        return actions


def check_protocol(protocol):
    line_number = 0
    current_label = 1
    actions = []

    # Check Protocol (save & load)
    for line in protocol:
        line_number += 1

        # unpacking action to (label, temp, time)
        # Check the line
        label, temp, time = list(map(lambda x : int(x) if type(x) is str and x.isdigit() else x, list(line.values())))
        
        # check the label
        if label == 'SHOT':
            pass     # TODO : SHOT line check
    
        if label == 'GOTO':     # GOTO action check
            if current_label != 0 and current_label >= temp: 
                if not 1 <= time <= 100: 
                    raise PCRProtocolError(f"Invalid GOTO count(1~100), line {line_number}")
            else:
                raise PCRProtocolError(f"Invalid GOTO target label, line {line_number}")

        else: # If its not 'GOTO' label 
            # Protocol 읽는 도중 time <= 15 일시 Protocol 읽지 않고 Error 처리
            if time < 15:
                raise PCRProtocolError('Invalid protocol time : protocol time must be at least 15 seconds. line {line_number}')
            

        # Normal action check 
        if type(label) is int:
            # protocol data can not be splited into label, temp, time.
            if len(line) != 3:
                print('Invalid protocol data, line %d' %line_number)
                break
            # label value is incorrect.
            if label != current_label:
                print('Invalid label value, line %d' %line_number)
                break
            current_label += 1

        # do not enter into this block
        else:
            pass
        
        actions.append({'Label' : label, 'Temp' : temp, 'Time' : time})
    return actions

def loadRecentProtocolName():
    try:
        with open(PCR_PATH + '\\' + RECENT_PROTOCOL_FILENAME, 'r') as file:
            protocol_name = file.readline()
            file.close()
        
        return protocol_name
    except FileNotFoundError as err:
        return

def saveRecentProtocolName(protocol_name=''):
    try:
        with open(PCR_PATH + '\\' + RECENT_PROTOCOL_FILENAME, 'w') as file:
            file.write(protocol_name)
            file.close()
        
        return protocol_name
    except FileNotFoundError as err:
        return