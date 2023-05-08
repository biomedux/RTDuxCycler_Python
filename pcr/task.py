import os
import time
import datetime
import threading
import logging

import asyncio


import cv2

import PyQt5
from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox


from pcr.constants.constant import Command, State, StateOper
from pcr import protocol as Protocol

import pcr.hid.tx_action as TxAction
import pcr.hid.rx_action as RxAction

from pcr.optic.optic import PCROptic
from pcr.file_manager import PCRFileManager
from pcr.optic.camera import FLUORESCENCES

from pcr import logger


class PCRTask:
    """PCR task class"""
    
    __instance = None

    @classmethod
    def _getInstance(cls):
        return cls.__instance

    @classmethod
    def instance(cls, *args, **kargs):
        cls.__instance = cls(*args, **kargs)
        cls.instance = cls._getInstance
        return cls.__instance

    @logger.log_pcr_message("INFO", f"PCR Task Initialized")
    def __init__(self, mainIU):
        super().__init__()

        # mainUI instance
        self.mainUI = mainIU

        self.mainUI.set_progress_value(10, "Setting flags...")
        # State & command paramters
        self.state = State.READY
        self.command = Command.NOP

        # PCR flags
        self.running = False
        self.finishPCR = False

        # PCR parameters 
        self.preheat = 104
        self.action_num = 0
        self.taskEnded = False

        # Temporary variable
        self.expt_name = None
        self.update_vals = []

        self.mainUI.set_progress_value(10, "Load Protocols...")
        # Load default protocol
        self.protocol = Protocol.default_protocol
        self.get_device_protocol()

        self.mainUI.set_progress_value(80, "Setting FileManager...")
        # FileManager
        self.file_manager = PCRFileManager()


        # PCR Optic(arduino_serial, camera)
        self.optic = PCROptic(self.file_manager, self.mainUI, self)
        # self.optic.arduino_serial.set_LEDPwm(200)


        self.optic.lid_backward()
        self.optic.chamber_backward()

        self.mainUI.set_progress_value(100, "Setting FileManager...")
        self.mainUI.close_loading_bar()
        self.mainUI.show()
        
    
    '''
        PCR START & STOP event functions
    '''
    @logger.log_pcr_message("INFO", f"PCR Start")
    def pcr_start(self):
        """MainUI 에서 Start 버튼 동작시 실행되는 함수"""

        # Set Flags
        self.running = True
        self.finishPCR = False
        self.command = Command.TASK_WRITE
        
        # Get expt name
        self.expt_name = PCRFileManager.gen_expt_name()

        # Get selected fluor & create path and *.xlsx
        sel_fluors = [FLUORESCENCES[ind] for ind, is_sel in enumerate(self.mainUI.frame_ctrl.selected_fluor) if is_sel]
        self.file_manager.start_task(self.expt_name, sel_fluors)

        self.optic.lid_forward()

        # mainUI's mainUI
        self.mainUI.running_event()

    @logger.log_pcr_message("INFO", f"PCR Stop")
    def pcr_stop(self):
        """MainUI 에서 Stop 버튼 동작시 실행되는 함수
            
            비동기 처리
        """
        if self.state == State.RUN:
            self.command = Command.STOP

    '''
        UI 이벤트들
    '''
    def set_preheat(self, preheat):
        self.preheat = preheat


    '''
        Protocol 관련 함수들
    '''
    def load_protocol(self, protocol_name):
        try:
            self.protocol = Protocol.load_protocol(protocol_name)
            Protocol.saveRecentProtocolName(protocol_name)
            self.cycle_num =  next((item for item in self.protocol if item['Label'] == 'GOTO'))['Time']

            self.mainUI.frame_ctrl.label_protocol.setText(protocol_name)
        except ValueError as err:
            QMessageBox.about(self.mainUI, "Invalid_protocol", "올바르지 않은 프로토콜 입니다.")
    
    def get_device_protocol(self):
        '''
        TODO : initialize 로직으로 이동
            220322 : self.deviceCheck flag 제거하고,
                        get_device_protocol call을 timer -> PCR_Task.__init__() 으로 옮김
        '''
        protocol_name = Protocol.loadRecentProtocolName()
        if protocol_name:
            try:
                self.load_protocol(protocol_name)
            except FileNotFoundError as err:
                QMessageBox.about(self.mainUI, "protocol_not_found", "최근 프로토콜 파일 존재하지 않음!")
        else:
            pass
    
    '''
        PCR Task 관련 함수들
    '''
    def check_action(self):
        """
            self.check_status() 에서
            TASK_WRITE 로 프로토콜 라인을 보낸 후
            rx_buffer 를 check 하는 함수
        """
        action = self.protocol[self.action_num].copy()
        action['Label'] = 250 if action['Label'] == "GOTO" else action['Label']
        
        # python dictionary subset compare
        return action.items() <= RxAction.rx_buffer.items()

    @logger.log_pcr_command
    def check_status(self):
        """읽어온 rx_buffer의 Status를 기반으로 flag들을 변경해 주는 함수

            State(Constant.State) 기반으로 작성되었으나,
            logic error 와 code 가독성을 위해 "이전 커맨드" 기반으로 변경하였음.
        """
        self.rx_action = RxAction.rx_buffer

        if self.command == Command.NOP:
            # TODO : UI Update
            state_oper = RxAction.rx_buffer["Current_Operation"]
            
            if state_oper != StateOper.INIT:
                if self.running and not self.finishPCR:
                    # TODO : reset parameters 
                    if state_oper == StateOper.COMPLETE:
                        # TODO : PCR Complate logic
                        self.optic.lid_backward()
                        QMessageBox.about(self.mainUI, "PCR END", "PCR COMPLITE!")

                        self.mainUI.frame_ctrl.btn_start.toggle()

                    elif state_oper == StateOper.INCOMPLETE:
                        # TODO : PCR Incomplate logic
                        self.optic.lid_backward()
                        QMessageBox.about(self.mainUI, "PCR END", "PCR INCOMPLATE")

                    self.mainUI.not_running_event()

                    self.running = False
                    self.finishPCR = True
                    self.action_num = 0

                    # self.expt_name = None
                    # self.file_manager.end_task()

            else:
                pass

        elif self.command == Command.TASK_WRITE:
            '''
                읽어온 rx_buffer 가 정상일 때,  
                남아 있는 action 이 있다면 action_num 를 1증가시키고, 
                남아 있는 action 이 없다면 command를 TASK_END 로 변경한다. 
            '''
            if self.check_action() :
                if  self.action_num != (len(self.protocol) - 1):
                    self.action_num += 1
                else:
                    self.command = Command.TASK_END

        elif self.command == Command.TASK_END:
            self.command = Command.GO
            
        elif self.command == Command.GO:
            if self.state == State.RUN:
                """
                Running button 누를시 start button 은 disable 상태로 변하며,
                TASKWRITE -> TASKEND -> GO 커맨드를 보낸 후 State가 Run 상태일때 활성화 된다.
                """
                self.mainUI.frame_ctrl.btn_start.setDisabled(False)
                self.command = Command.NOP
        
        elif self.command == Command.STOP:
            if self.state == State.READY or self.state == State.STOP:
                self.command = Command.NOP
    
    def calc_temp(self):
        """
            Chamber와 LID heater 온도 계산 후 MainUI에 Display 해주는 함수
        """
        chamber_temp = RxAction.rx_buffer['Chamber_TempH'] + RxAction.rx_buffer['Chamber_TempL'] * 0.1
        heater_temp = RxAction.rx_buffer['Cover_TempH'] + RxAction.rx_buffer['Cover_TempL'] * 0.1

        self.mainUI.frame_ctrl.temp(chamber_temp, heater_temp)

    def line_task(self):
        if self.state == State.RUN:
            loop, _, left_time = RxAction.rx_buffer["Current_Loop"], RxAction.rx_buffer["Current_Action"], RxAction.rx_buffer["Sec_TimeLeft"]
            self.mainUI.frame_ctrl.loop((0 if loop == 255 else self.cycle_num-loop))

            if len(self.update_vals) > 0:
                update_val = self.update_vals.pop(0)
                self.mainUI.frame_graph.update_values(update_val[0], update_val[1])
                self.mainUI.frame_img.display_values(update_val[0], update_val[1])

    def calc_time(self):
        pass

    def check_shot(self):
        """
            Shot이 가능한지 판단 후,
            PCR protocol에서 다음 label이 'GOTO' 이고, 남은시간이 10sec 일때 shot
        """
        if self.state == State.RUN and not self.optic.shot_thread.shotting:
            loop, action = RxAction.rx_buffer["Current_Loop"], RxAction.rx_buffer["Current_Action"]
            target_temp = self.protocol[action-1]["Temp"]
            next_label = self.protocol[action]["Label"]

            if action != 0 and next_label == "GOTO":
                left_time = RxAction.rx_buffer["Sec_TimeLeft"]

                if left_time == 10:
                    print(f"start shot!!!, {(0 if loop == 255 else self.cycle_num-loop)}")
                    loop = 0 if loop == 255 else self.cycle_num-loop
                    fluor = self.mainUI.frame_ctrl.selected_fluor
                    self.optic.shot(loop, fluor)

        self.mainUI.start_btn_in_shotting(self.optic.shot_thread.shotting)

    def set_update_vals(self, fluor, values):
        self.update_vals.append((fluor, values))

    '''
        Arduino & Camera 관련 함수들
    '''

    def chamber_take_out(self, state):
        self.mainUI.chamber_take_out_event(state)

        if state:
            print("꺼내기")
            self.optic.arduino_serial.chamber_forward()
        else:
            self.optic.arduino_serial.chamber_backward()

        self.mainUI.frame_ctrl.btn_take_out.setDisabled(False)