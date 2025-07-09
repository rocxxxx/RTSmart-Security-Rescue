#96 -*- coding: UTF-8 -*-
# 文件名: audio_recorder_mqtt.py
# 描述: 可交互的音频录制模块，支持 exit 返回主界面，
#       并在每段录音结束时通过 MQTT 将二进制数据发到网页端

import os
import time
import _thread
import re # 导入正则表达式模块，用于从文件名中提取数字
from machine import Pin
from media.pyaudio import PyAudio, paInt16
import media.wave as wave
from media.media import MediaManager
import network
from umqtt.simple import MQTTClient
import ujson
import random

# === 音频参数 ===
CHUNK = 1024
FORMAT = paInt16
CHANNELS = 1
RATE = 16000

# === MQTT 配置 ===
MQTT_BROKER_HOST = 'broker.emqx.io'
MQTT_TOPIC = b'k230/ai/status_feed'
CLIENT_ID = 'k230_board_' + str(random.randint(1000, 9999))
mqtt_client = None
is_mqtt_connected = False

# === 录音状态锁 ===
_recording_lock = False
_stop_record_flag = False   # 用于控制录音线程停止

# === 判断触摸是否在区域内的函数 ===
def is_in_area(tx, ty, cx, cy, w=100, h=40):
    """
    判断触摸点是否在指定区域内。
    参数:
        tx (int): 触摸点的X坐标。
        ty (int): 触摸点的Y坐标。
        cx (int): 区域左上角的X坐标。
        cy (int): 区域左上角的Y坐标。
        w (int): 区域的宽度。
        h (int): 区域的高度。
    返回:
        bool: 如果触摸点在区域内则返回True，否则返回False。
    """
    return (cx <= tx <= cx + w) and (cy <= ty <= cy + h)

# === 生成文件名 ===
def generate_filename(base_path="/sdcard/app", prefix="留言"):
    """
    生成一个不重复的文件名。
    参数:
        base_path (str): 文件保存的基础路径。
        prefix (str): 文件名前缀。
    返回:
        str: 生成的完整文件路径。
    """
    try:
        os.stat(base_path)
    except OSError: # 捕获文件或目录不存在的错误
        os.makedirs(base_path)
    index = 1
    while True:
        filename = f"{base_path}/{prefix}{index}.wav"
        try:
            os.stat(filename) # 尝试获取文件信息，如果不存在会抛出异常
        except OSError:
            return filename
        index += 1

# === 网络连接 ===
def connect_using_lan():
    """
    尝试通过有线方式（LAN）连接网络。
    """
    print("--- 尝试有线网络连接 ---")
    lan = network.LAN()
    if not lan.active():
        lan.active(True)
        time.sleep(2) # 等待LAN接口激活
    if not lan.isconnected():
        raise RuntimeError("网线未连接，网络不可用。")
    lan.ifconfig("dhcp") # 通过DHCP获取IP地址
    # 等待IP地址分配成功
    while lan.ifconfig()[0] == '0.0.0.0':
        print("等待 DHCP 分配 IP ...")
        time.sleep(1)
    print(f"网络已连接，IP: {lan.ifconfig()[0]}")

# === 连接MQTT ===
def mqtt_connect():
    """
    尝试连接到MQTT服务器。
    返回:
        bool: 连接成功返回True，否则返回False。
    """
    global mqtt_client, is_mqtt_connected
    print(f"连接MQTT服务器: {MQTT_BROKER_HOST}")
    mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER_HOST, keepalive=60)
    try:
        mqtt_client.connect()
        is_mqtt_connected = True
        print("MQTT连接成功")
        return True
    except Exception as e:
        print(f"MQTT连接失败: {e}")
        is_mqtt_connected = False
        return False

# === 发送MQTT二进制状态消息 ===
def send_mqtt_binary_status(status_byte_code):
    """
    向MQTT主题发布表示录音状态的二进制数据。
    参数:
        status_byte_code (bytes): 要发送的单个字节二进制数据，表示录音状态或索引。
                                  例如: b'\x01' 表示留言1完成, b'\xFF' 表示无法提取索引, b'\x00' 表示录音失败。
    """
    global mqtt_client, is_mqtt_connected
    if not is_mqtt_connected:
        print("MQTT未连接，尝试重连...")
        if not mqtt_connect():
            print("MQTT重连失败，数据未发送。")
            return
    try:
        mqtt_client.publish(MQTT_TOPIC, status_byte_code)
        print(f"MQTT发送二进制状态码: {status_byte_code.hex()}") # 打印十六进制表示方便调试
    except Exception as e:
        print(f"MQTT数据发送失败: {e}")
        is_mqtt_connected = False # 发送失败则认为连接断开

# === 显示 exit 按钮 ===
def draw_exit_button(pl):
    """
    在屏幕上绘制“exit”按钮。
    参数:
        pl: 屏幕绘图对象 (osd_img)。
    """
    x, y = 870, 446
    font_size = 30
    pl.osd_img.clear() # 清屏
    pl.osd_img.draw_string_advanced(x, y, font_size, "exit", color=(255, 0, 0, 255))
    pl.show_image() # 显示绘制的图像

# === 录音任务主体 ===
def _record_audio_task(pl, tp):
    """
    录音任务的主体函数，负责音频录制、文件保存和MQTT二进制消息发送。
    参数:
        pl: 屏幕绘图对象。
        tp: 触摸屏对象。
    """
    global _recording_lock, _stop_record_flag
    if _recording_lock:
        print("录音已进行，忽略重复请求")
        return
    _recording_lock = True

    p = None
    stream = None
    filename = None # 初始化文件名变量

    try:
        filename = generate_filename()
        print(f"开始录音，文件: {filename}")

        p = PyAudio()
        p.initialize(CHUNK)

        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE,
                        input=True, frames_per_buffer=CHUNK)

        frames = []
        draw_exit_button(pl) # 绘制退出按钮

        while True:
            if _stop_record_flag:
                print("收到停止录音指令，结束录音")
                break
            try:
                data = stream.read()
                frames.append(data)
            except Exception as e:
                print(f"读取音频失败: {e}")
                break # 读取失败则退出循环

            # 检测触摸退出
            points = tp.read()
            if points and len(points) > 0:
                p0 = points[0]
                tx, ty = 960 - p0.x, 536 - p0.y # 坐标转换
                if is_in_area(tx, ty, 870, 446): # 检查是否点击了退出按钮区域
                    print("触摸退出区域，停止录音")
                    break
            time.sleep(0.01) # 短暂延时，避免CPU占用过高

        # 停止流，保存文件
        stream.stop_stream()
        stream.close()
        wf = wave.open(filename, 'wb')
        wf.set_channels(CHANNELS)
        wf.set_sampwidth(p.get_sample_size(FORMAT))
        wf.set_framerate(RATE)
        wf.write_frames(b''.join(frames))
        wf.close()
        print(f"录音保存成功: {filename}")

        # === 录音完成时发送 MQTT 二进制消息 ===
        # 从文件名中提取录音索引，例如 "留言1.wav" -> 1
        match = re.search(r'留言(\d+)\.wav$', filename)
        if match:
            recording_index = int(match.group(1))
            # 将索引转换为单个字节的二进制数据
            # 假设索引不会超过255 (0-255)。如果可能更大，需要更多字节或不同的编码方式。
            try:
                binary_data_to_send = recording_index.to_bytes(1, 'big')
                send_mqtt_binary_status(binary_data_to_send)
            except OverflowError:
                print(f"录音索引 {recording_index} 过大，无法转换为单个字节。发送默认完成字节。")
                send_mqtt_binary_status(b'\xFE') # 发送一个默认的完成字节 (例如 0xFE)，表示索引过大
        else:
            print("无法从文件名中提取录音索引，发送默认完成字节。")
            send_mqtt_binary_status(b'\xFF') # 发送一个默认的完成字节 (例如 0xFF)，表示无法提取索引

    except Exception as e:
        print(f"录音异常: {e}")
        # 如果发生异常，发送一个表示错误的二进制数据
        send_mqtt_binary_status(b'\x00') # 例如，0x00 表示录音失败
    finally:
        # 确保PyAudio资源被释放
        try:
            if stream:
                stream.stop_stream()
                stream.close()
        except Exception as e:
            print(f"关闭音频流异常: {e}")
        try:
            if p:
                p.terminate()
        except Exception as e:
            print(f"终止PyAudio异常: {e}")
        _recording_lock = False
        _stop_record_flag = False
        print("录音任务退出")

# === 主入口 ===
def run_audio_recording(pl, tp):
    """
    音频录制模块的主入口函数。
    参数:
        pl: 屏幕绘图对象。
        tp: 触摸屏对象。
    """
    global mqtt_client, is_mqtt_connected
    try:
        # 尝试连接网络和MQTT，确保在录音前准备就绪
        connect_using_lan()
        mqtt_connect()
    except Exception as e:
        print(f"网络或MQTT初始化失败: {e}")
        # 如果网络或MQTT初始化失败，仍然可以尝试录音，但不会发送MQTT消息
        is_mqtt_connected = False # 确保标志位正确设置

    print("[录音] 开始录音任务")
    # 启动录音任务
    _record_audio_task(pl, tp)

