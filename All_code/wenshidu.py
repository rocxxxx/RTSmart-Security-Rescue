# -*- coding: UTF-8 -*-
# 文件名: wenshidu.py
# 描述: 可交互的温湿度模块，支持 exit 返回主界面，失败时保留上次数据，
#       并通过 MQTT 将数据发到网页端 (修改版：每10秒发送一次温湿度)

import utime
from machine import Pin, FPIOA
import network
import random
import ujson
from umqtt.simple import MQTTClient

# MQTT 配置
MQTT_BROKER_HOST = 'broker.emqx.io'
MQTT_TOPIC = b'k230/ai/status_feed'
CLIENT_ID = 'k230_board_' + str(random.randint(1000, 9999))
mqtt_client = None
is_mqtt_connected = False

# ====== DHT11 类 ======
class DHT11:
    def __init__(self, pin):
        self.pin = pin
        self.temperature = -1
        self.humidity = -1

    def read(self):
        try:
            # ——— 发送启动脉冲 ———
            self.pin.init(Pin.OUT, Pin.PULL_NONE)
            self.pin.value(0)
            utime.sleep_ms(20)
            self.pin.value(1)
            self.pin.init(Pin.IN, Pin.PULL_UP)

            # 等待 DHT11 拉低总线（应答信号）
            t_start = utime.ticks_us()
            while self.pin.value() == 1:
                if utime.ticks_diff(utime.ticks_us(), t_start) > 100:
                    return False

            # 等待拉高
            while self.pin.value() == 0:
                if utime.ticks_diff(utime.ticks_us(), t_start) > 200:
                    return False

            # 等待再次拉低
            while self.pin.value() == 1:
                if utime.ticks_diff(utime.ticks_us(), t_start) > 300:
                    return False

            # ——— 读取 40 个位 ———
            bits = []
            for _ in range(40):
                # 等待低电平结束
                t0 = utime.ticks_us()
                while self.pin.value() == 0:
                    if utime.ticks_diff(utime.ticks_us(), t0) > 100:
                        return False
                # 测高电平时长
                t1 = utime.ticks_us()
                while self.pin.value() == 1:
                    if utime.ticks_diff(utime.ticks_us(), t1) > 150:
                        return False
                # 根据高电平时长判 0/1（>45µs 则为 1）
                bits.append(1 if utime.ticks_diff(utime.ticks_us(), t1) > 45 else 0)

        finally:
            pass  # 可选：如果需要复位引脚状态可在此处做

        # 校验数据长度
        if len(bits) != 40:
            return False

        # 每 8 位组成一个字节
        data_bytes = [int("".join(str(b) for b in bits[i:i+8]), 2)
                      for i in range(0, 40, 8)]
        checksum = sum(data_bytes[0:4]) & 0xFF
        if checksum != data_bytes[4]:
            return False

        # 赋值温度和湿度
        self.humidity    = data_bytes[0]
        self.temperature = data_bytes[2]
        return True

# ====== 工具函数 ======
def is_in_area(tx, ty, cx, cy, w=100, h=40):
    return (cx <= tx <= cx + w) and (cy <= ty <= cy + h)

def draw_exit_button(pl):
    x, y = 870, 446
    font_size = 30
    pl.osd_img.draw_string_advanced(x, y, font_size, "exit", color=(255, 0, 0, 255))

# ====== 网络与 MQTT ======
def connect_using_lan():
    print("--- 准备通过有线方式（LAN）连接网络 ---")
    lan = network.LAN()
    if not lan.active():
        lan.active(True)
        utime.sleep(2)
    if not lan.isconnected():
        raise RuntimeError("网络连接失败：请检查网线是否正确插入。")
    print("LAN 网络配置:", lan.ifconfig())

def mqtt_connect():
    global mqtt_client, is_mqtt_connected
    print(f"--- 准备连接到 MQTT 服务器: {MQTT_BROKER_HOST} ---")
    mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER_HOST, keepalive=60)
    try:
        mqtt_client.connect()
        print("MQTT 服务器连接成功！")
        is_mqtt_connected = True
    except Exception as e:
        print("MQTT 连接失败:", e)
        is_mqtt_connected = False

# ====== 主函数 ======
def run_temp_display(pl, tp):
    print("[温湿度] 开始显示")

    # 尝试网络与 MQTT 连接
    try:
        connect_using_lan()
        mqtt_connect()
    except Exception as e:
        print("网络或 MQTT 异常:", e)

    # 初始化 DHT11
    DHT11_PIN_NUM = 27
    fpioa = FPIOA()
    fpioa.set_function(DHT11_PIN_NUM, getattr(FPIOA, f'GPIO{DHT11_PIN_NUM}'))
    dht_pin = Pin(DHT11_PIN_NUM, Pin.IN, Pin.PULL_UP)
    sensor = DHT11(dht_pin)

    last_temp = "--"
    last_humi = "--"

    # 新增：用于计时，控制10秒发送间隔
    last_mqtt_send_time = utime.time()

    while True:
        if sensor.read():
            last_temp = sensor.temperature
            last_humi = sensor.humidity

        # 清屏并显示（保持每2秒刷新一次，确保本地显示流畅）
        pl.osd_img.clear()
        color = (255, 100, 100, 255)
        pl.osd_img.draw_string_advanced(340, 140, 55, f"温度: {last_temp}°C", color=color)
        pl.osd_img.draw_string_advanced(340, 340, 55, f"湿度: {last_humi}%", color=color)
        draw_exit_button(pl)
        pl.show_image()

        # ====== MQTT 发送逻辑 (每10秒执行一次) ======
        current_time = utime.time()
        if is_mqtt_connected and mqtt_client and (current_time - last_mqtt_send_time >= 10):
            # 构建一个不含 "status_code" 的 payload
            # 这样网页端就不会在“历史事件日志”中记录它
            payload = {
                "device_id": CLIENT_ID,
                "temperature": last_temp,
                "humidity": last_humi,
                "time": current_time
            }
            try:
                mqtt_client.publish(MQTT_TOPIC, ujson.dumps(payload).encode('utf-8'))
                print(f"MQTT 已发送温湿度 -> {payload}")
                last_mqtt_send_time = current_time # 更新发送时间
            except Exception as e:
                print("MQTT 消息发送失败:", e)

        # 检测触摸退出
        points = tp.read()
        if points and len(points) > 0:
            p0 = points[0]
            tx, ty = 960 - p0.x, 536 - p0.y
            if is_in_area(tx, ty, 870, 446):
                print("[温湿度] 触发 exit，退出显示")
                break

        utime.sleep(1) # 循环延时保持不变，用于控制屏幕刷新率