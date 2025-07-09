from machine import Pin, FPIOA, UART, TOUCH ,PWM
import time
import os
import sys
import gc
from libs.PipeLine import PipeLine, ScopedTiming
import socket

# ===================== 4G模块激活函数 (即发即走版) =====================
def activate_4g_module(at_port_path="/dev/ttyUSB1"):
    """
    通过打开端口，发送AT指令来激活4G蜂窝模块，然后立即关闭端口，
    不等待模块返回 "OK"。
    """
    print(f"--- 正在通过发送AT指令激活 4G 模块 ({at_port_path}) ---")
    port = None
    try:
        # 步骤1：打开端口
        # 使用 'r+b' 模式，表示二进制读写, buffering=0 表示无缓冲
        port = open(at_port_path, "r+b", buffering=0)
        print("AT 命令端口打开成功。")

        # 步骤2：发送激活指令
        at_command = b"AT+QNETDEVCTL=1,1,1\r\n"
        print(f"发送激活指令: {at_command.decode().strip()}")
        port.write(at_command)

        # 发送后给予短暂延时，确保指令发出
        time.sleep(0.5)
        print("激活指令已发送。")
        return True

    except Exception as e:
        print(f"错误: 操作 AT 命令端口 '{at_port_path}' 失败: {e}")
        return False
    finally:
        # 步骤3：无论成功与否，都确保关闭端口
        if port:
            port.close()
            print("AT 命令端口已关闭。")



# ===================== 状态定义 =====================
STATUS_IDLE = 0
STATUS_FACE_RUNNING = 1
STATUS_OBJ_RUNNING = 2
STATUS_AUDIO_RUNNING = 3
STATUS_PLAY_RUNNING = 4

current_app_status = STATUS_IDLE

PACKET_HEADER = b'\xAA'
PACKET_FOOTER = b'\x55'

def send_main_status_packet(uart_obj, status_code):
    if uart_obj:
        payload_byte = status_code.to_bytes(1, 'big')
        packet = PACKET_HEADER + payload_byte + PACKET_FOOTER
        uart_obj.write(packet)
        print(f"主程序发送顶层状态: {packet.hex()} (状态码: {status_code})")

# ===================== 显示配置 =====================
all_letter_positions = {
    'face':   (30, 40),
    'yolo':   (30, 140),
    'temp':   (30, 240),  # 新增温湿度按钮
    'record': (30, 340),
    'play':   (30, 440)
}
font_size = 30

def is_in_area(tx, ty, cx, cy, w=100, h=40):
    return (cx <= tx <= cx + w) and (cy <= ty <= cy + h)

def show_letters_by_status(pl, status):
    pl.osd_img.clear()
    if status == STATUS_IDLE:
        keys = ['face', 'yolo', 'temp', 'record', 'play']
    else:
        keys = []

    for key in keys:
        x, y = all_letter_positions[key]
        pl.osd_img.draw_string_advanced(x, y, font_size, key, color=(100, 100, 255, 255))
    pl.show_image()





# ===================== 主程序入口 =====================
print("--- 主程序启动 ---")
pl = None
uart = None

try:
    pipeline_rgb_size = [1920, 1080]
    display_size = [960, 540]

    print("初始化 PipeLine...")
    pl = PipeLine(rgb888p_size=pipeline_rgb_size, display_size=display_size, display_mode="lcd")
    pl.create(hmirror=True)

    print("初始化 UART2...")
    fpioa = FPIOA()
    fpioa.set_function(11, FPIOA.UART2_TXD)
    fpioa.set_function(12, FPIOA.UART2_RXD)
    uart = UART(UART.UART2, 115200)

    # ===================== 在这里调用4G模块激活功能 =====================
    activate_4g_module()
    # =======================================================================
    tp = TOUCH(0)
    #send_main_status_packet(uart, STATUS_IDLE)
    show_letters_by_status(pl, STATUS_IDLE)

    last_touch = None



    while True:
        if uart.any():
            data = uart.read()
            if data:
                print(f"UART 接收到: {data}")
                uart.write(b'ACK:' + data)

        points = tp.read()
        if points and len(points) > 0:
            p = points[0]
            tx, ty = 960 - p.x, 536 - p.y

            if (not last_touch) or abs(tx - last_touch[0]) > 10 or abs(ty - last_touch[1]) > 10:
                last_touch = (tx, ty)
                print(f"有效触摸: ({tx}, {ty})")

                if current_app_status == STATUS_IDLE:
                    if is_in_area(tx, ty, *all_letter_positions['face']):
                        print("触发 face 人脸识别")
                        #send_main_status_packet(uart, STATUS_FACE_RUNNING)
                        current_app_status = STATUS_FACE_RUNNING
                        show_letters_by_status(pl, current_app_status)
                        try:
                            if '人脸识别' in sys.modules: del sys.modules['人脸识别']
                            if "/sdcard/project" not in sys.path: sys.path.append("/sdcard/project")
                            import 人脸识别 as face_app
                            gc.collect()
                            face_app.run_face_recognition(pl, pipeline_rgb_size, uart)
                        except Exception as e:
                            print("人脸识别错误:")
                            sys.print_exception(e)
                        finally:
                            current_app_status = STATUS_IDLE
                           # send_main_status_packet(uart, STATUS_IDLE)
                            show_letters_by_status(pl, current_app_status)

                    elif is_in_area(tx, ty, *all_letter_positions['yolo']):
                        print("触发 yolo 目标检测")
                        #send_main_status_packet(uart, STATUS_OBJ_RUNNING)
                        current_app_status = STATUS_OBJ_RUNNING
                        show_letters_by_status(pl, current_app_status)
                        try:
                            if 'object_detect_yolov8n_net' in sys.modules: del sys.modules['object_detect_yolov8n_net']
                            if "/sdcard/project" not in sys.path: sys.path.append("/sdcard/project")
                            import object_detect_yolov8n_net as obj_app
                            gc.collect()
                            obj_app.run_object_detection(pl, pipeline_rgb_size, uart)
                        except Exception as e:
                            print("目标检测错误:")
                            sys.print_exception(e)
                        finally:
                            current_app_status = STATUS_IDLE
                           # send_main_status_packet(uart, STATUS_IDLE)
                            show_letters_by_status(pl, current_app_status)

                    elif is_in_area(tx, ty, *all_letter_positions['temp']):
                        print("触发 temp 温湿度显示")
                        show_letters_by_status(pl, STATUS_IDLE)
                        try:
                            if 'wenshidu' in sys.modules: del sys.modules['wenshidu']
                            if "/sdcard/project" not in sys.path: sys.path.append("/sdcard/project")
                            import wenshidu
                            wenshidu.run_temp_display(pl,tp)
                        except Exception as e:
                            print("温湿度模块错误:")
                            sys.print_exception(e)
                        finally:
                            show_letters_by_status(pl, STATUS_IDLE)

                    elif is_in_area(tx, ty, *all_letter_positions['record']):
                        print("触发 record 语音录音")
                       # send_main_status_packet(uart, STATUS_AUDIO_RUNNING)
                        current_app_status = STATUS_AUDIO_RUNNING
                        show_letters_by_status(pl, current_app_status)
                        try:
                            if 'maikefeng' in sys.modules: del sys.modules['maikefeng']
                            if "/sdcard/project" not in sys.path: sys.path.append("/sdcard/project")
                            import maikefeng as audio_app
                            audio_app.run_audio_recording(pl, tp)
                        except Exception as e:
                            print("语音录音错误:")
                            sys.print_exception(e)
                        finally:
                            current_app_status = STATUS_IDLE
                           # send_main_status_packet(uart, STATUS_IDLE)
                            show_letters_by_status(pl, current_app_status)

                    elif is_in_area(tx, ty, *all_letter_positions['play']):
                        print("触发 play 音频播放")
                       # send_main_status_packet(uart, STATUS_PLAY_RUNNING)
                        current_app_status = STATUS_PLAY_RUNNING
                        show_letters_by_status(pl, current_app_status)
                        try:
                            if 'bofang' in sys.modules: del sys.modules['bofang']
                            if "/sdcard/project" not in sys.path: sys.path.append("/sdcard/project")
                            import bofang as play_app
                            play_app.run_audio_play(pl, tp)
                        except Exception as e:
                            print("音频播放错误:")
                            sys.print_exception(e)
                        finally:
                            current_app_status = STATUS_IDLE
                          #  send_main_status_packet(uart, STATUS_IDLE)
                            show_letters_by_status(pl, current_app_status)
        else:
            last_touch = None

        time.sleep(0.1)

except Exception as e:
    sys.print_exception(e)
finally:
    print("主程序退出，清理资源...")
    if pl:
        pl.destroy()
