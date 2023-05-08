from pcr import logger


# 
AF_GOTO			=	250
# rx_buffer size is 64
RX_BUFSIZE		=	64

# Rx_buffer index definitions
RX_STATE 		= 	0;     RX_RES			=	1
RX_CURRENTACTNO	=	2;     RX_CURRENTLOOP	=	3
RX_TOTALACTNO	=	4;     RX_KP			=	5
RX_KI			=	6;     RX_KD			=	7
RX_LEFTTIMEH	=	8;     RX_LEFTTIMEL	    =	9
RX_LEFTSECTIMEH	=	10;    RX_LEFTSECTIMEL	=	11
RX_LIDTEMPL		=	13;    RX_LIDTEMPH		=	12
RX_CHMTEMPH		=	14;    RX_CHMTEMPL		=	15
RX_PWMH			=	16;    RX_PWMDIR		=	18
RX_PWML			=	17;    RX_LABEL		    =	19
RX_TEMP			=	20;    RX_TIMEH		    =	21
RX_TIMEL		=	22;    RX_LIDTEMP		=	23
RX_REQLINE		=	24;    RX_ERROR		    =	25
RX_CUR_OPR		=	26;    RX_SINKTEMPH	    =	27
RX_SINKTEMPL	=	28;    RX_KP_1			=	39
RX_KI_1			=	33;    RX_KD_1			=	37
RX_SERIALH		=	41 #not use this version.
RX_SERIALL		=	42 #only bluetooth version.
RX_SERIALRESERV	=	43;    RX_VERSION		=	44

# Rx_buffer dictionary
rx_buffer = {'State' : 0, 'Res' : 0,
            'Cover_TempH' : 0, 'Cover_TempL' : 0,
            'Chamber_TempH' : 2, 'Chamber_TempL' : 2,
            'Heatsink_TempH' : 0, 'Heatsink_TempL' : 0,
            'Current_Operation' : 0, 'Current_Action' : 0,
            'Current_Loop' : 0, 'Total_Action' : 0,
            'Error' : 0, 'Serial_H' : 0, 'Serial_L' : 0,
            'Total_TimeLeft' : 0, 'Sec_TimeLeft' : 0,
            'Firmware_Version' : 0,
            'Label' : 0, 'Temp' : 0, 'Time_H' : 0, 'Time_L' : 0,
            'ReqLine' : 0}

@logger.log_hid_read
def set_buffer(raw_data):
    """Convert rx_buffer(raw_data) to dict(rx_buffer)"""
    rx_buffer['State']              = raw_data[RX_STATE]
    rx_buffer['Res']                = raw_data[RX_RES]
    rx_buffer['Current_Action']     = raw_data[RX_CURRENTACTNO]
    rx_buffer['Current_Loop']       = raw_data[RX_CURRENTLOOP]
    rx_buffer['Total_Action']       = raw_data[RX_TOTALACTNO]
    rx_buffer['Total_TimeLeft']     = (raw_data[RX_LEFTTIMEH] << 8) + raw_data[RX_LEFTTIMEL]
    rx_buffer['Sec_TimeLeft']       = float((raw_data[RX_LEFTSECTIMEH] << 8) + raw_data[RX_LEFTSECTIMEL])
    rx_buffer['Cover_TempH']        = raw_data[RX_LIDTEMPH]
    rx_buffer['Cover_TempL']        = raw_data[RX_LIDTEMPL]
    rx_buffer['Chamber_TempH']      = raw_data[RX_CHMTEMPH]
    rx_buffer['Chamber_TempL']      = raw_data[RX_CHMTEMPL]
    rx_buffer['Heatsink_TempH']     = raw_data[RX_SINKTEMPH]
    rx_buffer['Heatsink_TempL']     = raw_data[RX_SINKTEMPL]
    rx_buffer['Current_Operation']  = raw_data[RX_CUR_OPR]
    rx_buffer['Error']              = raw_data[RX_ERROR]
    rx_buffer['Serial_H']           = raw_data[RX_SERIALH]
    rx_buffer['Serial_L']           = raw_data[RX_SERIALL]
    rx_buffer['Firmware_Version']   = raw_data[RX_VERSION]
    rx_buffer['Label']              = raw_data[RX_LABEL]
    rx_buffer['Temp']               = raw_data[RX_TEMP]
    rx_buffer['Time_H']             = raw_data[RX_TIMEH]
    rx_buffer['Time_L']             = raw_data[RX_TIMEL]
    rx_buffer['ReqLine']            = raw_data[RX_REQLINE]
    rx_buffer["Time"]               = (rx_buffer['Time_H'] << 8) + rx_buffer['Time_L']