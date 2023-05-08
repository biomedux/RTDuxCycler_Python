import time
import datetime
import logging
import sys

import cv2

from pcr.constants.constant import Command, State
from pcr.hid.hid_controller import serial


LOG_PATH = f"C:/mPCR/log"
LOG_FNAME = serial + '_' + datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '.log'


# Logging formatter & file handler definitions
formatter = logging.Formatter(f"%(asctime)s\t%(name)s\t\t%(levelname)s\t%(message)s")
file_handler = logging.FileHandler(f"{LOG_PATH}/{LOG_FNAME}", mode='w')
file_handler.setFormatter(formatter)

# Logger definitions
root_logger = logging.getLogger("PCR")
root_logger.addHandler(file_handler)
root_logger.setLevel(logging.DEBUG)

ui_logger = logging.getLogger("PCR.UI")
ui_logger.setLevel(logging.DEBUG)

hid_logger = logging.getLogger("PCR.hid")
hid_logger.setLevel(logging.DEBUG)

serial_logger = logging.getLogger("PCR.serial")
serial_logger.setLevel(logging.DEBUG)

camera_logger = logging.getLogger("PCR.cam")
camera_logger.setLevel(logging.DEBUG)

file_logger = logging.getLogger("PCR.cam")
file_logger.setLevel(logging.DEBUG)


# PCR Logging decorator definitions
def log_pcr_message(level, message):
    lev = getattr(logging, level)
    def decorator(func):
        def wrapper(*args, **kwargs):
            root_logger.log(lev, message)
            res = func(*args, **kwargs)
            return res
        return wrapper
    return decorator

def log_pcr_command(func):
    def wrapper(*args, **kwargs):
        task = args[0]
        pre_command = task.command
        func(*args, **kwargs)
        command = task.command

        if task.running:
            if pre_command != Command.NOP and command != Command.NOP:
                root_logger.debug(f"Command가 바뀌었습니다. {pre_command.name} --> {command.name}")
    return wrapper


# UI Logging decorator definitions
def log_ui_message(level, message):
    lev = getattr(logging, level)
    def decorator(func):
        def wrapper(*args, **kwargs):
            ui_logger.log(lev, message)
            res = func(args[0])
            return res
        return wrapper
    return decorator

def log_ui_start(func):
    def wrapper(*args, **kwargs):
        state = args[1]
        func(*args, **kwargs)

        if state:   ui_logger.debug("Start button 이 toggle 되었습니다. Start --> Stop")
        else:       ui_logger.debug("Start button 이 toggle 되었습니다. Stop --> Start")
    return wrapper

def log_ui_camsel(instance):
    def decorator(func):
        def wrapper(*args, **kwargs):
            func()
            ui_logger.debug(f"선택된 Shot 형광 {instance.selected_fluor}")
        return wrapper
    return decorator


# Camera Logging decorator definitions
def log_cam_message(level, message):
    lev = getattr(logging, level)
    def decorator(func):
        def wrapper(*args, **kwargs):
            camera_logger.log(lev, message)
            res = func(*args, **kwargs)
            return res
        return wrapper
    return decorator

def log_cam_init(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        # cap = args[0].cap
        
        # settings = {}
        # settings['width'] = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
        # settings['height'] = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
        # settings['autofocus'] = cap.get(cv2.CAP_PROP_AUTOFOCUS)
        # settings['focus'] = cap.get(cv2.CAP_PROP_FOCUS)
        # settings['autoexposure'] = cap.get(cv2.CAP_PROP_AUTO_EXPOSURE)
        # settings['exposure'] = cap.get(cv2.CAP_PROP_EXPOSURE)
        # settings['gain'] = cap.get(cv2.CAP_PROP_GAIN)
        # settings['gamma'] = cap.get(cv2.CAP_PROP_GAMMA)

        # camera_logger.info(f"Setting result {settings}")
    return wrapper

def log_cam_brightness(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)
        camera_logger.debug(f"values : {res}")
        return res
    return wrapper

# Hid Logging decorator definitions
def log_hid_write(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        tx_buf = list(args[0].raw)

        if tx_buf[1] != Command.NOP:
            hid_logger.info(f"Tx_buffer : {list(tx_buf)}")
    return wrapper

def log_hid_read(func):
    def wrapper(*args, **kwargs):
        res = func(*args, **kwargs)

        if res == None or len(res) == 0:
            pass
        else:
            rx_buf = list(res)
            # if rx_buf[0] != State.READY:
            if True:
                hid_logger.info(f"rx_buffer : {rx_buf}")
        return res
    return wrapper

def log_hid_error(func):
    def wrapper(*args, **kwargs):
        hid_logger.exception(f"hid 연결이 끊겼습니다.")
        func(*args, **kwargs)
    return wrapper

def log_start_expt(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        file_logger.info(f"실험 '{args[1]}'이 시작되었습니다.")
    return wrapper

def log_save_img(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        instance = args[0]
        file_logger.info(f"이미지 {instance.expt_img_path}/{instance.current_expt}_{args[2]}_{args[3]}.png 저장")
    return wrapper

def log_save_test_img(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        instance = args[0]
        file_logger.info(f"이미지 {instance.DATA_PATH}/img/{args[2]}_test.png 저장")
    return wrapper