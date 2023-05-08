
from cProfile import label
import enum
import sys
import numpy as np

import PyQt5
from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QIntValidator
from PyQt5.QtWidgets import QAbstractItemView, QApplication, QCheckBox, QDialog, QFileDialog, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QProgressBar, QToolButton, QVBoxLayout, QPushButton, QWidget, QMainWindow, QFrame, QTableWidget, QTableWidgetItem, QTabWidget, QSpinBox, QMessageBox, QLineEdit
from PyQt5.QtCore import QFileDevice, QRect, QSize, Qt
from PyQt5.QtCore import pyqtSlot

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

from pcr.task import PCRTask
from pcr import protocol as Protocol

from pcr import logger




#Test raw data
"""
    TEST_DATA:
        shape : (40, 4, 25) == (cycle, fluor, chamber)
"""
TEST_DATA = [[[chamber*4+fluor for cycle in range(0, 40)] for fluor in range(0, 4)] for chamber in range(0, 25)]
FLUORESCENCES = ['FAM', 'HEX', 'ROX', 'CY5']


class MainUI(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.setWindowTitle("DuxCycler_ProtoTester - camsetting") # set title
        self.setGeometry(100, 100, 900, 750) # (pos_x, pos_y , width, height)
        self.setFixedSize(900, 750) # Disable window resize

        self.frame_graph = GraphFrame()
        self.frame_ctrl = ControlFrame()
        self.frame_img = ImageFrame()
        self.frame_graphSel = GraphSelectionFrame(self.frame_graph)
        self.frame_camctrl = CameraControlFrame()

        

        self.grid_layout = QGridLayout()
        self.grid_layout.setRowMinimumHeight(0, 500)

        self.grid_layout.addWidget(self.frame_graph, 0, 0, 1, 3)
        self.grid_layout.addWidget(self.frame_ctrl, 1, 0)
        self.grid_layout.addWidget(self.frame_img, 1, 1)
        self.grid_layout.addWidget(self.frame_graphSel, 1, 2)
        self.grid_layout.addWidget(self.frame_camctrl, 2, 0, 1, 3)

        self.setLayout(self.grid_layout)

        # Test code : loading bar
        self.loading_dialog = QDialog()
        self.loading_dialog.setWindowTitle('Loading...')
        self.loading_dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.loading_dialog.resize(270, 50)
        
        self.loading_bar = QProgressBar(self.loading_dialog)
        self.loading_bar.setGeometry(10, 10, 250, 30)

        self.loading_dialog.show()

    def set_progress_value(self, value, text=''):
        self.loading_bar.setValue(value)
        self.loading_bar.setFormat("%d%% (%s)" %(value, text))

    def close_loading_bar(self):
        self.loading_dialog.close()

    def running_event(self):
        # Set disable select fluorescences
        for btn in self.frame_ctrl.fluor_btns:
            btn.setEnabled(False)

        # Set disable protocol read button
        self.frame_ctrl.btn_read.setEnabled(False)

        # Set disable take out button
        self.frame_ctrl.btn_take_out.setEnabled(False)

        # Set disable shot button
        self.frame_ctrl.btn_shot.setEnabled(False)

        # Set disable preheat spinbox
        self.frame_ctrl.spin_preheat.setEnabled(False)

        # Set start button disable while sending command(TASKWRITE ~ TASKEND ~ GO)
        self.frame_ctrl.btn_start.setDisabled(True)

        self.frame_camctrl.set_disabled(True)

        # Clear image frmae
        self.frame_img.display_none()

        # Init graph frame's values & reset graph
        self.frame_graph.init_fluor_values()
        self.frame_graph.reset_figure()

    def not_running_event(self):
        # Set disable select fluorescences
        for btn in self.frame_ctrl.fluor_btns:
            btn.setEnabled(True)

        # Set disable protocol read button
        self.frame_ctrl.btn_read.setEnabled(True)

        # Set disable take out button
        self.frame_ctrl.btn_take_out.setEnabled(True)

        # Set disable preheat spinbox
        self.frame_ctrl.spin_preheat.setEnabled(True)

        # Set disable shot button
        self.frame_ctrl.btn_shot.setEnabled(True)

        # Set start button disable while sending command(TASKWRITE ~ TASKEND ~ GO)
        self.frame_ctrl.btn_start.setDisabled(False)

        self.frame_camctrl.set_disabled(False)

    def chamber_take_out_event(self, state):
        self.frame_ctrl.btn_take_out.setDisabled(True)

        print(state)
        self.frame_ctrl.btn_shot.setEnabled(not state)
        self.frame_ctrl.btn_start.setDisabled(state)

    def start_btn_in_shotting(self, flag):
        self.frame_ctrl.btn_start.setDisabled(flag)
        
        


class GraphFrame(QFrame):
    def __init__(self):
        super().__init__()

        self.fluor_values = None
        self.init_fluor_values()

        self.checkbox_inds = []
        self.fluor_state = []

        self.setLineWidth(1)
        self.setFrameStyle(QFrame.Shape.Panel)

        self.fig = plt.Figure()
        self.canvas = FigureCanvas(self.fig)
        self.toolbar = NavigationToolbar(self.canvas, self)

        self.ax = self.fig.add_subplot(111)

        self.reset_figure()

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)
        
        self.setLayout(self.layout)

    def init_fluor_values(self):
        self.fluor_values = {f:[[] for i in range(25)] for f in FLUORESCENCES}

    def reset_figure(self):
        # self.fig.clear()

        self.ax.clear()
        self.ax.set_ylabel("birghtness")
        self.ax.set_xlabel("cycle")

        self.canvas.draw()

        #TODO : Set initial figure shape

    def plot_graph(self, checkbox_inds, fluor_state):
        self.checkbox_inds = checkbox_inds
        self.fluor_state = fluor_state

        self.reset_figure()

        for cb_ind in checkbox_inds:
            chamber_num = (cb_ind[0]-1)*5+(cb_ind[1]-1)
            for fluor, f_state in zip(FLUORESCENCES, fluor_state):
                values = self.fluor_values[fluor][chamber_num]
                if f_state and values != []:
                    self.ax.plot(self.fluor_values[fluor][chamber_num], label=f"{fluor}_tube{chamber_num}")

        self.ax.set_xlabel("birghtness")
        self.ax.set_xlabel("cycle")
        self.ax.set_xlim(0, 40)
        self.ax.set_ylim(0, 255)
        self.ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))

        self.canvas.draw()

    def update_values(self, fluor, values):
        for ind, value in enumerate(values):
            self.fluor_values[fluor][ind].append(value)

        self.plot_graph(self.checkbox_inds, self.fluor_state)


class ControlFrame(QFrame):
    def __init__(self):
        super().__init__()

        #set selected_fluor (FAM, HEX, ROX, CY5)
        self.selected_fluor = [False, False, False, False]
        

        self.setLineWidth(1)
        self.setFrameStyle(QFrame.Shape.Panel)

        self.vbox_layout = QVBoxLayout()
        self.fluor_layout = QHBoxLayout()
        self.pwm_layout = QHBoxLayout()
        self.protocol_layout = QHBoxLayout()
        self.info_layout = QHBoxLayout()
        self.btn_layout1 = QHBoxLayout()
        self.btn_layout2 = QHBoxLayout()

        #Set fluorescences
        self.fluor_btns=[]
        self.pwm_editors = []
        for ind, fluor in enumerate(FLUORESCENCES):
            _btn = QToolButton()
            _btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            _btn.setIcon(QIcon('./res/'+fluor+'.bmp'))
            _btn.setText(fluor)
            _btn.clicked.connect(self.flourButtonEvent(ind))
            self.fluor_btns.append(_btn)
            self.fluor_layout.addWidget(_btn)

            _editor = QLineEdit()
            _editor.setValidator(QIntValidator())
            _editor.setText(f"-1")
            _editor.setFixedSize(40, 20)
            self.pwm_editors.append(_editor)
            self.pwm_layout.addWidget(_editor)

        self.vbox_layout.addLayout(self.fluor_layout)
        self.vbox_layout.addLayout(self.pwm_layout)
        
        #Set protocol layout
        self.label_protocol = QLabel('')
        self.label_protocol.setFixedSize(100, 30)
        self.label_protocol.setStyleSheet('border: 1px solid black;')

        # Set preheate layout
        self.preheat_layout = QHBoxLayout()
        self.label_preheat = QLabel('lid_heat :')
        self.label_preheat.setStyleSheet('border: 1px solid black;')

        self.spin_preheat = QSpinBox()
        self.spin_preheat.setMinimum(20); self.spin_preheat.setMaximum(120)
        self.spin_preheat.setValue(104)
        self.spin_preheat.setSingleStep(1)
        self.spin_preheat.valueChanged.connect(self.preheatEvent)
        self.label_preheat.setMaximumWidth(50)
        self.spin_preheat.setMaximumWidth(70)

        self.protocol_layout.addWidget(self.label_protocol)
        self.preheat_layout.addWidget(self.label_preheat)
        self.preheat_layout.addWidget(self.spin_preheat)
        self.protocol_layout.addLayout(self.preheat_layout)
        self.vbox_layout.addLayout(self.protocol_layout)

        

        #Set information layout
        self.label_temp = QLabel('')
        self.label_temp.setFixedSize(50, 30)
        self.label_temp.setStyleSheet('border: 1px solid black;')

        self.label_lid_temp = QLabel('')
        self.label_lid_temp.setFixedSize(50, 30)
        self.label_lid_temp.setStyleSheet('border: 1px solid black;')

        self.label_cycle = QLabel('')
        self.label_cycle.setFixedSize(50, 30)
        self.label_cycle.setStyleSheet('border: 1px solid black;')
        

        self.info_layout.addWidget(self.label_temp)
        self.info_layout.addWidget(self.label_lid_temp)
        self.info_layout.addWidget(self.label_cycle)
        self.vbox_layout.addLayout(self.info_layout)

        #Set button layout1
        self.btn_read = QPushButton('READ')
        self.btn_read.clicked.connect(self.read_protocol)

        self.btn_take_out = QPushButton('꺼내기')
        self.btn_take_out.setCheckable(True)
        self.btn_take_out.toggled.connect(self.btn_take_out_toggle)
        
        self.btn_layout1.addWidget(self.btn_read)
        self.btn_layout1.addWidget(self.btn_take_out)
        self.vbox_layout.addLayout(self.btn_layout1)

        #Set button layout2
        self.btn_start = QPushButton('START')
        self.btn_start.setStyleSheet("background-color: green")
        self.btn_start.setCheckable(True)
        self.btn_start.toggled.connect(self.start_btn_toggle)

        self.btn_shot = QPushButton('촬영')
        self.btn_shot.clicked.connect(self.shot)

        
        self.btn_layout2.addWidget(self.btn_start)
        self.btn_layout2.addWidget(self.btn_shot)
        self.vbox_layout.addLayout(self.btn_layout2)


        self.setLayout(self.vbox_layout)

    @logger.log_ui_start
    @pyqtSlot(bool)
    def start_btn_toggle(self, state):
        pcr_task = PCRTask.instance()
        # self.btn_start.setDisabled(True)
        
        # # If no any fluorescence is selected in the UI
        # sel_fluor = pcr_task.mainUI.frame_ctrl.selected_fluor
        # if not any(sel_fluor):
        #     QMessageBox.about(pcr_task.mainUI, "Info", "Choose one or more fluorescence")
        #     self.btn_start.setDefault()
        #     return
        
        self.btn_start.setStyleSheet("background-color: %s" % ({True: "red", False: "green"}[state]))
        self.btn_start.setText({True: "STOP", False: "START"}[state])
        
        if state:
            PCRTask.instance().pcr_start()
        elif pcr_task.running:
            PCRTask.instance().pcr_stop()

        # self.btn_start.setDisabled(False)

    @pyqtSlot(bool)
    def btn_take_out_toggle(self, state):
        self.btn_take_out.setText({True: "넣기", False: "꺼내기"}[state])

        PCRTask.instance().chamber_take_out(state)


    def temp(self, chamber_temp, lid_temp):
        self.label_lid_temp.setText(str(lid_temp))
        self.label_temp.setText(str(chamber_temp))

    def loop(self, current_loop):
        self.label_cycle.setText(str(current_loop))

    @logger.log_ui_message('INFO', 'Read button이 눌렸습니다.')
    def read_protocol(self):
        file_path = QFileDialog.getOpenFileName(self, 'Select Protocol', 'C:\\mPCR\\protocols', filter='*.txt')[0]
        
        if file_path:
            file_name = file_path.split('/')[-1][:-4]
            PCRTask.instance().load_protocol(file_name)
            self.label_protocol.setText(file_name)

    def preheatEvent(self):
        preheat = self.spin_preheat.value()
        PCRTask.instance().set_preheat(preheat)

    def get_pwm(self):
        res = {}
        for fluor, editor in zip(FLUORESCENCES, self.pwm_editors):
            res[fluor] = int(editor.text())
        
        return res

    def init_pwm(self, pwm_dict):
        for pwm, editor in zip(pwm_dict.values(), self.pwm_editors):
            editor.setText(f"{pwm}")
            

    def flourButtonEvent(self, ind):
        @logger.log_ui_camsel(self)
        def clickedEvent():
            self.selected_fluor[ind] = not self.selected_fluor[ind]

            if self.selected_fluor[ind]:
                self.fluor_btns[ind].setStyleSheet("background-color: green")
            else:
                self.fluor_btns[ind].setStyleSheet("background-color: none")

        return clickedEvent

    @logger.log_ui_message("INFO", f"Shot button이 눌렸습니다.")
    def shot(self):
        PCRTask.instance().optic.shot(None, self.selected_fluor)


class ImageFrame(QFrame):
    def __init__(self):
        super().__init__()

        # Set Frame props
        self.setLineWidth(1)
        self.setFrameStyle(QFrame.Shape.Panel)
        self.layout = QVBoxLayout()
        self.setMaximumWidth(300)

        # Get Tab Widget
        self.tabs = QTabWidget()

        # Set images
        self.images = {fluor:ImageTab(fluor, color) for fluor, color in zip(FLUORESCENCES, ["#038569", "#FDCA01", "#E30C1B", "#E31718", "#C8061E"])}

        # Add images to tab
        for flour in self.images:
            self.tabs.addTab(self.images[flour], flour)

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)

    def display_values(self, fluor, values):
        self.images[fluor].display_values(values)

    def display_none(self):
        for fluor in FLUORESCENCES:
            self.images[fluor].display_none()
        


class ImageTab(QWidget):
    def __init__(self, fluor, color_code="#54ab48"):
        super().__init__()
        self.flour = fluor

        # Set layout
        self.layout = QGridLayout()
        self.setMaximumWidth(280)
        self.setMaximumHeight(280)

        # Set labels
        self.labels = [QLabel('-') for i in range(25)]
        for row in range(0, 5):
            for col in range(0, 5):
                chamber_num = (row)*5+(col)
                label = self.labels[chamber_num]
                
                label.setFixedSize(50, 50)
                label.setAlignment(Qt.AlignCenter)
                label.setStyleSheet(f"border: 3px solid {color_code}; border-radius:25px; background-color: {color_code}; color: white;")
                
                self.layout.addWidget(label, row, col, Qt.AlignmentFlag.AlignCenter)

        # Display
        self.setLayout(self.layout)
    
    def display_values(self, values):
        for value, label in zip(values, self.labels):
            label.setText(value if type(value) == str else f"{value:.2f}")

    def display_none(self):
        self.display_values(['-']*25)
            

class GraphSelectionFrame(QFrame):
    button_size = 25

    def __init__(self, graph_frame):
        super().__init__()

        self.graph_frame = graph_frame
        #set selected_fluor (FAM, HEX, ROX, CY5)
        self.selected_fluor = [False, False, False, False]

        self.setLineWidth(1)
        self.setFrameStyle(QFrame.Shape.Panel)


        self.hbox_layout = QVBoxLayout()
        self.btn_layout = QHBoxLayout()
        self.cb_layout = QGridLayout()
        self.cb_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.cb_frame = QFrame()
        self.btn_frame = QFrame()
        

        #Set cb layout
        rng = range(1, 6)
        self.check_boxs = []
        for row in rng:
            _ls = []
            for col in rng:
                _cb = QCheckBox()
                _cb.setChecked
                _cb.setGeometry(0, 0, 100, 100)
                _cb.clicked.connect(self.checkboxEvent)
                _ls.append(_cb)
                self.cb_layout.addWidget(_cb, row, col, Qt.AlignmentFlag.AlignCenter)
            self.check_boxs.append(_ls)

        #Add 'ALL' button
        btn_all = QPushButton('ALL')
        btn_all.setFixedSize(25, 25)
        btn_all.clicked.connect(self.selectAll)
        self.cb_layout.addWidget(btn_all, 0, 0, Qt.AlignmentFlag.AlignCenter)

        #Set selection button
        for val in rng:
            #set row button
            _btn = QPushButton(str(val))
            _btn.setFixedSize(25, 25)
            _btn.clicked.connect(self.selectLine(True, val))
            self.cb_layout.addWidget(_btn, val, 0, Qt.AlignmentFlag.AlignCenter)

            #set column button
            _btn = QPushButton(str(val))
            _btn.setFixedSize(25, 25)
            _btn.clicked.connect(self.selectLine(False, val))
            self.cb_layout.addWidget(_btn, 0, val, Qt.AlignmentFlag.AlignCenter)
            

        #Set btn layout
        self.fluor_btns = []
        for ind, fluor in enumerate(FLUORESCENCES):
            _btn = QToolButton()
            _btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            _btn.setIcon(QIcon('./res/'+fluor+'.bmp'))
            _btn.setText(fluor)
            _btn.clicked.connect(self.flourButtonEvent(ind))
            self.fluor_btns.append(_btn)
            self.btn_layout.addWidget(_btn)

        self.cb_frame.setLayout(self.cb_layout)
        self.btn_frame.setLayout(self.btn_layout)

        self.hbox_layout.addWidget(self.btn_frame)
        self.hbox_layout.addWidget(self.cb_frame)

        self.setLayout(self.hbox_layout)


    def selectLine(self, isRow: bool, line: int):
        selected_fluor = self.selected_fluor
        check_boxs=self.check_boxs
        graph_frame = self.graph_frame
        getSelectedCheckboxInd = self.getSelectedCheckboxInd

        def clickedEvent(self):
            target = check_boxs[line-1][:] if isRow else [check_boxs[i][line-1] for i in range(0, 5)]

            isAllChecked = True
            for cb in target:
                if not cb.isChecked():
                    isAllChecked = False
                    break
            
            for cb in target:
                cb.setChecked(not isAllChecked)

            graph_frame.plot_graph(getSelectedCheckboxInd(), selected_fluor)

        return clickedEvent

    def flourButtonEvent(self, ind):
        selected_fluor = self.selected_fluor
        fluor_btns = self.fluor_btns
        graph_frame = self.graph_frame
        getSelectedCheckboxInd = self.getSelectedCheckboxInd
        
        def clickedEvent(self):
            selected_fluor[ind] = not selected_fluor[ind]

            if selected_fluor[ind]:
                fluor_btns[ind].setStyleSheet("background-color: green")
            else:
                fluor_btns[ind].setStyleSheet("background-color: none")

            graph_frame.plot_graph(getSelectedCheckboxInd(), selected_fluor)

        return clickedEvent

    def selectAll(self):
        isAllChecked=True
        for row_cb in self.check_boxs:
            for cb in row_cb:
                if not cb.isChecked():
                    isAllChecked = False
                    break

        for row_cb in self.check_boxs:
            for cb in row_cb:
                cb.setChecked(not isAllChecked)

        self.graph_frame.plot_graph(self.getSelectedCheckboxInd(), self.selected_fluor)

    def getSelectedCheckboxInd(self):
        selected_cb = [] # 따로 저장해 놓는게 나을듯 하다.

        for row in range(0, 5):
            for col in range(0, 5):
                if self.check_boxs[row][col].isChecked():
                    selected_cb.append((row+1, col+1))

        return selected_cb

    def checkboxEvent(self):
        self.graph_frame.plot_graph(self.getSelectedCheckboxInd(), self.selected_fluor)


class CameraControlFrame(QFrame):
    def __init__(self):
        super().__init__()

        self.setLineWidth(1)
        self.setFrameStyle(QFrame.Shape.Panel)

        self.frames = {
            "focus"         : CamSettingFrame("focus"),
            "exposure"      : CamSettingFrame("exposure"),
            "gain"          : CamSettingFrame("gain"),
            "gamma"         : CamSettingFrame("gamma"),
            "whilebalance"  : CamSettingFrame("whilebalance"),
            "low_light_com" : CamSettingFrame("low_light_com"),
        }

        self.btn_setting = QPushButton(f"Cam_setting")
        self.btn_setting.clicked.connect(self.set_cam)
        
        # set layout
        self.layout = QHBoxLayout()

        for frame in self.frames.values():
            self.layout.addWidget(frame)
        self.layout.addWidget(self.btn_setting)

        self.setLayout(self.layout)

    def set_disabled(self, flag):
        self.btn_setting.setDisabled(flag)
        # for frame in self.frames.values():
        #     frame.set_disabled(flag)

    def set_cam(self):
        cam = PCRTask.instance().optic.shot_thread.cam_worker

        setting_dict = self.get_set_vals()

        cam.setup_cam_all(focus = setting_dict["focus"],
                          exposure=setting_dict["exposure"],
                          gain = setting_dict["gain"],
                          gamma = setting_dict["gamma"],
                          low_light_com= setting_dict["low_light_com"],
                          white_balance = setting_dict["whilebalance"])

        vals_dict = cam.get_all_settings()
        for name, val in vals_dict.items():
            self.frames[name].set_getval(*val)

    def init_display(self):
        cam = PCRTask.instance().optic.shot_thread.cam_worker

        vals_dict = cam.get_all_settings()
        for name, val in vals_dict.items():
            self.frames[name].set_getval(*val)
            self.frames[name].set_setval(val[0])

    def get_set_vals(self):
        return {name:frame.get_setval() for name, frame in self.frames.items()}

class CamSettingFrame(QFrame):
    def __init__(self, name):
        super().__init__()

        self.setStyleSheet('border: 1px solid black;')

        self.set_editor = QLineEdit()
        self.set_editor.setValidator(QIntValidator())
        self.set_editor.setText(f"-1")

        self.get_editor = QLineEdit()
        self.get_editor.setText(f"NaN")
        self.get_editor.setDisabled(True)

        self.layout = QGridLayout()
        self.layout.addWidget(QLabel(f"{name}"), 0, 0, 1, 2)
        self.layout.addWidget(QLabel(f"set : "), 1, 0)
        self.layout.addWidget(self.set_editor, 1, 1)
        self.layout.addWidget(QLabel(f"get : "), 2, 0)
        self.layout.addWidget(self.get_editor, 2, 1)

        self.setLayout(self.layout)

    def set_getval(self, val, flag):
        self.get_editor.setText(f"{val}, {flag}")

    def set_setval(self, val):
        self.set_editor.setText(f"{val}")

    def get_setval(self):
        return int(self.set_editor.text())

    def set_disabled(self, flag):
        self.set_editor.setDisabled(flag)

    


app = QApplication(sys.argv)
app.setStyle('Fusion') #windowsvista Windows Fusion
# app.aboutToQuit.connect(closeEvent)
window = MainUI()
# window.show()

