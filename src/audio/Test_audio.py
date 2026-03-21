# import time
#
# from listener import Listener
# import threading
#
# def function_start():
#     print("function_start")
# def function_end():
#     print("function_end")
# def function_next():
#     print("function_next")
# def function_previous():
#     print("function_previous")
# def function_reset():
#     print("function_reset")
# def function_plank():
#     print("function_plank")
# def function_sit_ups():
#     print("function_sit_ups")
# def function_bicep_curl():
#     print("function_bicep_curl")
# def function_lateral_raise():
#     print("function_lateral_raise")
# def function_press():
#     print("function_press")
#
# commands = [
# "start","end", "next", "previous", "reset","plank", "sit ups", "bicep curl", "lateral raise", "press"
# ]
# functions = [
#     function_start, function_end, function_next,function_previous, function_reset,function_plank, function_sit_ups, function_bicep_curl,function_lateral_raise, function_press
# ]
#
# listener = Listener(commands, functions)
# listener.start()
#
# while(1):
#     print("work")
#     time.sleep(1)
#
