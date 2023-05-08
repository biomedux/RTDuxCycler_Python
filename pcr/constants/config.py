import sys
import json


try:
    with open(r'.\conf.json', 'r') as config_file:
        config_json = json.load(config_file)

except FileNotFoundError as e:
    print("conf.json file does not exist :\n", e)
    raise e("conf.json file does not exist.")

CAM_NAME = config_json["cam_name"]
CAM_SETTINGS = config_json["cam_settings"][CAM_NAME]


FILTER_WHEEL = config_json["optic"]["filter_wheel"]
SERVO_MOTOR = config_json["optic"]["servo_motor"]
LED = config_json["optic"]["led"]


FLUORESCENCES = config_json["optic"]["fluoresences"]
CHANNELS = config_json["optic"]["channel"]