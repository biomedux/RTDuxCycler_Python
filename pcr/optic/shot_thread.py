import sys
import time
import threading

import cv2
import numpy as np

from pcr.serial_ctrl import FILTER_POSITIONS, LED_PWMS
from pcr.optic.camera import IMX298BufferCleaner, tubes_intensity, FLUORESCENCES, FOCUS, EXPOSURE

led_time = {
    -1 : 1.25,
    -2 : 0.75,
    -3 : 1,
    -4 : 0.75,
    -5 : 0.75
}
        

class ShotThread(threading.Thread):
    """
        PCR Task와 비동기적으로 Shot을 하기 위한 Thread class
    """
    ## def __init__(self, serial, file_manager, main_ui):
    def __init__(self, serial, file_manager, main_ui, task):
        super().__init__()
        self.daemon = True

        self.task = task
        print(f"task : {task}")

        # Initialize
        self.main_ui = main_ui
        self.serial = serial
        self.file_manager = file_manager
        self.cam_worker = IMX298BufferCleaner()
        self.cam_worker.start()

        # Thread event
        self.shot_event = threading.Event()

        # Shotting flag
        self.shotting = False

        # Shotting params
        self.cur_loop = None
        self.target_flours = None

        self.main_ui.frame_ctrl.init_pwm(LED_PWMS)
        self.pwms = self.main_ui.frame_ctrl.get_pwm()
        print(self.pwms)

    def run(self):
        while True:
            self.shot_event.wait()
            self._shot()
            self.shot_event.clear()

    def _shot(self):
        """
            TODO : shot logic
        """

        st = time.time()
        
        cam_vals = self.cam_worker.get_all_settings()
        led_sleep = led_time[cam_vals["exposure"][0]]
        

        print(cam_vals)

        self.pwms = self.main_ui.frame_ctrl.get_pwm()
        print(self.pwms)

        # set focus
        self.cam_worker.set_focus(FOCUS)
        # self.cam_worker.set_exposure(EXPOSURE)

        if self.cur_loop == None:
            self.serial.lid_forward()
            print("lid servo forwarding")
            # time.sleep(5)

        imgs=[]
        # Shot each filters
        for flour in self.target_flours:
            pos = FILTER_POSITIONS[flour]
            pwm = self.pwms[flour]

            self.serial.flush()

            # TODO : GOTO target position:
            self.serial.go_to(pos)
            
            print(f"LED on time : {led_sleep}")
            
            # TODO : LED On
            self.serial.set_LEDPwm(pwm)
            
            time.sleep(led_sleep)
            


            # Shot
            img = self.cam_worker.shot()
            print("SHOT!!!!!!!!!!!!!!!!!!!")
            imgs.append(img)

            # TODO : LED Off
            self.serial.set_LEDPwm(0)

        # TODO : GO HOME
        # GO HOME 까지 순차적으로
        self.serial.go_home()
            

        print(f"--go home done time : {time.time()-st}")

        if self.cur_loop == None:
            self.serial.lid_backward()
            time.sleep(5)
        

        # Save img & analysing
        for flour, img in zip(self.target_flours, imgs):
            # Save img
            try:
                if self.cur_loop == None:
                    self.file_manager.save_test_img(img, flour)
                else:
                    self.file_manager.save_img(img, flour, self.cur_loop)

                    values = tubes_intensity(flour, img)
                    self.file_manager.xlsx.record_values(flour, values, self.cur_loop)
                    # self.main_ui.frame_graph.update_values(flour, values)
                    # self.main_ui.frame_img.display_values(flour, values)
                    self.task.set_update_vals(flour, values)
                    
            
            except Exception as e:
                print(f"{e}")
        
        self.shotting=False
        print(f"end shot!!! : {time.time()-st}")
        print(self.cam_worker.get_all_settings())

    def shot(self, loop, selected_fluors):
        if not self.shotting:
            self.cur_loop = loop
            self.target_flours = [FLUORESCENCES[ind] for ind, is_sel in enumerate(selected_fluors) if is_sel]
            self.shotting = True
            self.shot_event.set()

    def close(self):
        self.cam_worker.close()
        sys.exit(0)