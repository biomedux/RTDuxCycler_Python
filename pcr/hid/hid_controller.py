import hid, sys
from ctypes import windll


# Duxcycler's vid & pid
VENDOR_ID      = 0x04D8
PRODUCT_ID     = 0xFB76
PRODUCT_ID_BMX = 0xEF7F

# For multi
# MAX_DEVICE	   = 20

# Max size of rx_buffer
BUFSIZE        = 65
# Time out is 3 seconds. It will be change
TIMEOUT        = 3

# Filter to get devices list of Duxcycler
device_filter = lambda x : x['vendor_id'] == VENDOR_ID and (x['product_id'] == PRODUCT_ID or x['product_id'] == PRODUCT_ID_BMX)


try:
    hid_devices = hid.enumerate()
    hid_devices = list(filter(device_filter, hid_devices))

    if len(hid_devices) <= 0:
        raise hid.HIDException
    
    # Only use first one in the devices list.
    __hid_device =  hid.Device(hid_devices[0]['vendor_id'], hid_devices[0]['product_id'])
    # __hid_device = hid.Device(VENDOR_ID)
    
except hid.HIDException:
    windll.user32.MessageBoxW(0, u"USB 커넥터를 확인한 뒤 재실행 부탁드립니다", u"USB Connection Error", 0)
    sys.exit()

# manufacturer and serial
manufacturer, serial = __hid_device.manufacturer, __hid_device.serial


# Import logger when after connected hid
from pcr import logger

@logger.log_hid_error
def hid_error_box():
    """Error Message box"""
    windll.user32.MessageBoxW(0, u"USB 커넥터를 확인한 뒤 재실행 부탁드립니다", u"USB Connection Error", 0)
    sys.exit()

@logger.log_hid_read
def read():
    """Read rx_buffer from PIC18 and return"""
    #Rx_buffer_size : 65, Timeout : 3s
    try:
        return __hid_device.read(BUFSIZE, TIMEOUT)
    except hid.HIDException:
        hid_error_box()

@logger.log_hid_write
def write(buffer):
    """Write tx_buffer"""
    try:
        __hid_device.write(buffer)
    except hid.HIDException:
        hid_error_box()