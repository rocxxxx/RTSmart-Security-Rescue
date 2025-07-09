
from libs.PipeLine import PipeLine, ScopedTiming
from libs.AIBase import AIBase
from libs.AI2D import Ai2d
import os, ujson, random, gc, sys
import nncase_runtime as nn
import ulab.numpy as np
import time, utime, image
import aidemo
from machine import Pin, FPIOA, UART
from machine import TOUCH

#DeviceKey：K230
#DeviceSecret：neGSvSKgDnrOaHzi

# ==============================================================================
# 新增：网络与MQTT通信模块
# ==============================================================================
import network
from umqtt.simple import MQTTClient

# --- MQTT 配置 ---
MQTT_BROKER_HOST = 'broker.emqx.io'
# 【状态上报】主题：设备 -> 网页
MQTT_TOPIC = b'k230/ai/status_feed' 
# ⭐【指令下发】主题：网页 -> 设备 (新增)
MQTT_CMD_TOPIC = b'k230/ai/command'
CLIENT_ID = 'k230_board_' + str(random.randint(1000, 9999)) 
mqtt_client = None
is_mqtt_connected = False
g_uart_obj = None # ⭐ 新增：全局变量，用于在回调中访问uart对象

# 🆕 新增: 全局变量，用于存储自动出动的默认地点
g_auto_dispatch_location = 0x01 # 默认前往地点一
g_auto_dispatch_location_uart = b'\x01' # 默认前往地点一
# --- 网络连接函数 (保持不变) ---
def connect_using_lan():
    # ... 此函数内容不变 ...
    print("--- 准备通过有线方式（LAN）连接网络 ---")
    lan = network.LAN()
    if not lan.active():
        print("网卡未激活，正在尝试激活...")
        lan.active(True)
        time.sleep(2)
    if not lan.isconnected():
        raise RuntimeError("网络连接失败：请检查网线是否正确插入。")
    print("网线已连接，网卡已激活。")
    print("正在通过 DHCP 获取 IP 地址...")
    lan.ifconfig("dhcp")
    while lan.ifconfig()[0] == '0.0.0.0':
        print("等待获取 IP 地址...")
        time.sleep(1)
    print(f"--- 网络连接成功, IP: {lan.ifconfig()[0]} ---")


def mqtt_command_callback(topic, msg):
    global g_uart_obj, g_auto_dispatch_location, g_auto_dispatch_location_uart
    try:
        if topic.decode() == MQTT_CMD_TOPIC.decode():
            print(f"MQTT Recv CMD < {msg.decode()}")
            data = ujson.loads(msg)
            command = data.get("command")

            if command == "dispatch_vehicle":
                location = data.get("location")
                print(f"收到'出动小车'指令, 目标地点: {location}")

                if g_uart_obj:
                    # 根据地点选择对应的【串口指令码】和【MQTT确认码】
                    uart_command = None
                    mqtt_confirmation = None

                    if location == 1:
                        uart_command = STATUS_DISPATCH_VEHICLE_1
                        mqtt_confirmation = STATUS_DISPATCH_CONFIRMED_1
                    elif location == 2:
                        uart_command = STATUS_DISPATCH_VEHICLE_2
                        mqtt_confirmation = STATUS_DISPATCH_CONFIRMED_2
                    elif location == 3:
                        uart_command = STATUS_DISPATCH_VEHICLE_3
                        mqtt_confirmation = STATUS_DISPATCH_CONFIRMED_3
                    else:
                        print(f"错误：无效的地点'{location}'，不执行任何操作。")
                        return

                    # 1. 向底层硬件(串口)发送【指令码】
                    _send_ai_status_packet(g_uart_obj, uart_command)

                    # 2. 向网页(MQTT)发布【确认码】，以示区分
                    publish_mqtt_status(mqtt_confirmation, STATUS_TEXT_MAP.get(mqtt_confirmation))
                else:
                    print("错误：UART对象未初始化，无法发送指令。")

            # “设置地点”指令的处理 (无改动)
            elif command == "set_location":
                location = data.get("location")
                print(f"收到'切换地点'指令, 自动出动目标已更新为: 地点{location}")
                if location == 1:
                    g_auto_dispatch_location = STATUS_DISPATCH_VEHICLE_1
                    g_auto_dispatch_location_uart = STATUS_DISPATCH_VEHICLE_1_UART
                elif location == 2:
                    g_auto_dispatch_location = STATUS_DISPATCH_VEHICLE_2
                    g_auto_dispatch_location_uart = STATUS_DISPATCH_VEHICLE_2_UART
                elif location == 3:
                    g_auto_dispatch_location = STATUS_DISPATCH_VEHICLE_3
                    g_auto_dispatch_location_uart = STATUS_DISPATCH_VEHICLE_3_UART
                else:
                    print(f"错误：无效的切换地点'{location}'")

    except Exception as e:
        print(f"处理MQTT指令时出错: {e}")
# ⭐🆕 END: 核心修改区域

# --- MQTT 连接函数 ---
def mqtt_connect():
    """连接到MQTT服务器，并设置回调、订阅指令主题"""
    global mqtt_client, is_mqtt_connected
    print(f"\n--- 准备连接到 MQTT 服务器: {MQTT_BROKER_HOST} ---")
    mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER_HOST, keepalive=60)
    
    # ⭐ 设置消息回调函数
    mqtt_client.set_callback(mqtt_command_callback)

    try:
        mqtt_client.connect()
        print("MQTT 服务器连接成功！")
        
        # ⭐ 订阅指令主题
        mqtt_client.subscribe(MQTT_CMD_TOPIC)
        print(f"MQTT 已订阅指令主题: {MQTT_CMD_TOPIC.decode()}")
        
        is_mqtt_connected = True
        return True
    except Exception as e:
        print(f"MQTT 服务器连接失败: {e}")
        is_mqtt_connected = False
        return False


# --- MQTT 数据发布函数 (保持不变) ---
def publish_mqtt_status(status_code, status_text):
    # ... 此函数内容不变 ...
    global mqtt_client, is_mqtt_connected
    if not is_mqtt_connected:
        print("MQTT 未连接，尝试重连...")
        if not mqtt_connect():
            print("重连失败，本次数据未发送。")
            return

    try:
        payload = {
            "status_code": hex(status_code),
            "status_text": status_text,
            "device_id": CLIENT_ID,
            "timestamp": time.time()
        }
        payload_json = ujson.dumps(payload)
        mqtt_client.publish(MQTT_TOPIC, payload_json.encode('utf-8'))
        print(f"MQTT 已发送 -> {payload_json}")
    except Exception as e:
        print(f"MQTT 消息发送失败: {e}")
        is_mqtt_connected = False


# ==============================================================================
# 模块专属的串口通信协议与功能
# ==============================================================================
PACKET_HEADER1 = b'\x2C'
PACKET_HEADER2 = b'\x43'
PACKET_FOOTER = b'\x5B'

# PACKET_HEADER1 = 0x2C
# PACKET_HEADER2 = 0x43
# PACKET_FOOTER = 0x5B

# AI检测状态
STATUS_OD_IDLE = 0x10
STATUS_PERSON_DETECTED = 0x11
STATUS_FALL_DETECTED = 0x12
STATUS_SMOKING_DETECTED = 0x13
# ⭐ 远程指令状态 (新增)
STATUS_DISPATCH_VEHICLE = 0xA0 
STATUS_DISPATCH_VEHICLE_1 = 0x01
STATUS_DISPATCH_VEHICLE_2 = 0x02
STATUS_DISPATCH_VEHICLE_3 = 0x03

# ⭐🆕 新增：设备执行指令后，返回给网页的【确认】状态码
STATUS_DISPATCH_CONFIRMED_1 = 0x31
STATUS_DISPATCH_CONFIRMED_2 = 0x32
STATUS_DISPATCH_CONFIRMED_3 = 0x33



STATUS_DISPATCH_VEHICLE_1_UART =b'\x01'
STATUS_DISPATCH_VEHICLE_2_UART = b'\x02'
STATUS_DISPATCH_VEHICLE_3_UART = b'\x03'
font_size = 30
exit_color = (100, 100, 255, 255)

def _send_ai_status_packet(uart_obj, status_code):
    if uart_obj:
        payload_byte = status_code.to_bytes(1, 'big')
        packet = PACKET_HEADER1 + PACKET_HEADER2 + payload_byte + PACKET_FOOTER
        uart_obj.write(payload_byte)
        # 统一打印，无论是AI状态还是指令状态
        print(f"UART Sent Status: {hex(status_code)}")

# 状态码到文本的映射，方便MQTT发送
STATUS_TEXT_MAP = {
    STATUS_OD_IDLE: "一切正常",
    STATUS_PERSON_DETECTED: "检测到有人",
    STATUS_FALL_DETECTED: "检测到跌倒",
    STATUS_SMOKING_DETECTED: "检测到吸烟",
    STATUS_DISPATCH_VEHICLE_1: "指令：出动小车(地点一)",
    STATUS_DISPATCH_VEHICLE_2: "指令：出动小车(地点二)",
    STATUS_DISPATCH_VEHICLE_3: "指令：出动小车(地点三)",
    STATUS_DISPATCH_CONFIRMED_1: "确认：小车已出动前往地点一",
    STATUS_DISPATCH_CONFIRMED_2: "确认：小车已出动前往地点二",
    STATUS_DISPATCH_CONFIRMED_3: "确认：小车已出动前往地点三"
}

def show_touch_buttons(pl):
    # 定义按钮位置
    buttons = {
        'exit': (860, 10),  # 示例按钮位置，可按需调整
    }
    for name, (x, y) in buttons.items():
        pl.osd_img.draw_string_advanced(x, y, font_size, name, color=(255, 0, 0, 0))


# ==============================================================================
# 键盘扫描 (保持不变)
# ==============================================================================
fpioa = FPIOA()
row_pins_num = [28, 29, 30, 31]
col_pins_num = [18, 19, 33, 35]
for pin_num in row_pins_num + col_pins_num:
    fpioa.set_function(pin_num, getattr(FPIOA, f'GPIO{pin_num}'))

rows = [Pin(p, Pin.IN, Pin.PULL_DOWN) for p in row_pins_num]
cols = [Pin(p, Pin.OUT) for p in col_pins_num]
key_names = [["1", "2", "3", "4"], ["5", "6", "7", "8"], ["9", "10", "11", "12"],["13", "14", "15", "16"]]

def scan_key():
    for i, col in enumerate(cols):
        for c in cols: c.value(0)
        col.value(1)
        time.sleep_ms(10)
        for j, row in enumerate(rows):
            if row.value():
                time.sleep_ms(20)
                if row.value(): return key_names[j][i]
    return None

def ALIGN_UP(x, align):
    return (x + (align - 1)) // align * align

# ==============================================================================
# AI 应用核心类
# ==============================================================================
class ObjectDetectionApp(AIBase):
    def __init__(self,kmodel_path,labels,model_input_size,max_boxes_num,confidence_threshold=0.5,nms_threshold=0.2,rgb888p_size=[224,224],display_size=[1920,1080],debug_mode=0):
        super().__init__(kmodel_path,model_input_size,rgb888p_size,debug_mode)
        self.labels=labels
        self.model_input_size=model_input_size
        self.confidence_threshold=confidence_threshold
        self.nms_threshold=nms_threshold
        self.max_boxes_num=max_boxes_num
        self.rgb888p_size=[ALIGN_UP(rgb888p_size[0],16),rgb888p_size[1]]
        self.display_size=[ALIGN_UP(display_size[0],16),display_size[1]]
        self.debug_mode=debug_mode
        self.color_four=[(255, 220, 20, 60), (255, 119, 11, 32), (255, 0, 0, 142), (255, 0, 0, 230),(255, 106, 0, 228), (255, 0, 60, 100), (255, 0, 80, 100), (255, 0, 0, 70),(255, 0, 0, 192), (255, 250, 170, 30), (255, 100, 170, 30), (255, 220, 220, 0),(255, 175, 116, 175), (255, 250, 0, 30), (255, 165, 42, 42), (255, 255, 77, 255),(255, 0, 226, 252), (255, 182, 182, 255), (255, 0, 82, 0), (255, 120, 166, 157)]
        self.x_factor = float(self.rgb888p_size[0])/self.model_input_size[0]
        self.y_factor = float(self.rgb888p_size[1])/self.model_input_size[1]
        self.ai2d=Ai2d(debug_mode)
        self.ai2d.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT,nn.ai2d_format.NCHW_FMT,np.uint8, np.uint8)

    def config_preprocess(self,input_image_size=None):
        with ScopedTiming("set preprocess config",self.debug_mode > 0):
            ai2d_input_size=input_image_size if input_image_size else self.rgb888p_size
            self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
            self.ai2d.build([1,3,ai2d_input_size[1],ai2d_input_size[0]],[1,3,self.model_input_size[1],self.model_input_size[0]])

    # 自定义当前任务的后处理
    def postprocess(self,results):
        with ScopedTiming("postprocess",self.debug_mode > 0):
            result=results[0]
            result = result.reshape((result.shape[0] * result.shape[1], result.shape[2]))
            output_data = result.transpose()
            boxes_ori = output_data[:,0:4]
            scores_ori = output_data[:,4:]
            confs_ori = np.max(scores_ori,axis=-1)
            inds_ori = np.argmax(scores_ori,axis=-1)
            boxes,scores,inds = [],[],[]
            for i in range(len(boxes_ori)):
                if confs_ori[i] > self.confidence_threshold:
                    scores.append(confs_ori[i])
                    inds.append(inds_ori[i])
                    x = boxes_ori[i,0]
                    y = boxes_ori[i,1]
                    w = boxes_ori[i,2]
                    h = boxes_ori[i,3]
                    left = int((x - 0.5 * w) * self.x_factor)
                    top = int((y - 0.5 * h) * self.y_factor)
                    right = int((x + 0.5 * w) * self.x_factor)
                    bottom = int((y + 0.5 * h) * self.y_factor)
                    boxes.append([left,top,right,bottom])
            if len(boxes)==0:
                return []
            boxes = np.array(boxes)
            scores = np.array(scores)
            inds = np.array(inds)
            # NMS过程
            keep = self.nms(boxes,scores,self.nms_threshold)
            dets = np.concatenate((boxes, scores.reshape((len(boxes),1)), inds.reshape((len(boxes),1))), axis=1)
            dets_out = []
            for keep_i in keep:
                dets_out.append(dets[keep_i])
            dets_out = np.array(dets_out)
            dets_out = dets_out[:self.max_boxes_num, :]
            return dets_out

    # 多目标检测 非最大值抑制方法实现
    def nms(self,boxes,scores,thresh):
        """Pure Python NMS baseline."""
        x1,y1,x2,y2 = boxes[:, 0],boxes[:, 1],boxes[:, 2],boxes[:, 3]
        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
        order = np.argsort(scores,axis = 0)[::-1]
        keep = []
        while order.size > 0:
            i = order[0]
            keep.append(i)
            new_x1,new_y1,new_x2,new_y2,new_areas = [],[],[],[],[]
            for order_i in order:
                new_x1.append(x1[order_i])
                new_x2.append(x2[order_i])
                new_y1.append(y1[order_i])
                new_y2.append(y2[order_i])
                new_areas.append(areas[order_i])
            new_x1 = np.array(new_x1)
            new_x2 = np.array(new_x2)
            new_y1 = np.array(new_y1)
            new_y2 = np.array(new_y2)
            xx1 = np.maximum(x1[i], new_x1)
            yy1 = np.maximum(y1[i], new_y1)
            xx2 = np.minimum(x2[i], new_x2)
            yy2 = np.minimum(y2[i], new_y2)
            w = np.maximum(0.0, xx2 - xx1 + 1)
            h = np.maximum(0.0, yy2 - yy1 + 1)
            inter = w * h
            new_areas = np.array(new_areas)
            ovr = inter / (areas[i] + new_areas - inter)
            new_order = []
            for ovr_i,ind in enumerate(ovr):
                if ind < thresh:
                    new_order.append(order[ovr_i])
            order = np.array(new_order,dtype=np.uint8)
        return keep


    def draw_result(self,pl,dets):
        with ScopedTiming("display_draw",self.debug_mode >0):
            pl.osd_img.clear()
            #show_touch_buttons(pl)
            pl.osd_img.draw_string_advanced(10, 10, 24, "目标检测中...(点击exit退出)", color=(255, 255, 0, 0))
            if dets is not None and len(dets) > 0:
                for det in dets:
                    x1, y1, x2, y2 = map(int, det[:4])
                    score, class_id = det[4], int(det[5])
                    x = int(x1*self.display_size[0] / self.rgb888p_size[0])
                    y = int(y1*self.display_size[1] / self.rgb888p_size[1])
                    w = int((x2-x1)*self.display_size[0] / self.rgb888p_size[0])
                    h = int((y2-y1)*self.display_size[1] / self.rgb888p_size[1])
                    pl.osd_img.draw_rectangle(x,y, w, h, color=self.get_color(class_id),thickness=4)
                    pl.osd_img.draw_string_advanced(x, y-50, 32," " + self.labels[class_id] + " " + str(round(score,2)) , color=self.get_color(class_id))

    def get_color(self, x):
        return self.color_four[x % len(self.color_four)]

# ==============================================================================
# 模块入口函数 (⭐ 重要修改)
# ==============================================================================
def is_in_area(tx, ty, cx, cy, w=100, h=40):
    return (cx <= tx <= cx + w) and (cy <= ty <= cy + h)

def run_object_detection(pl, pipeline_input_size, uart_obj=None):
    # ⭐ 将uart_obj赋值给全局变量，以便回调函数使用
    global g_uart_obj, g_pipeline, is_mqtt_connected
    g_uart_obj = uart_obj
    g_pipeline = pl

    # 在AI初始化之前，先完成网络和MQTT的连接
    try:
        connect_using_lan()
        mqtt_connect()
    except Exception as e:
        print(f"网络或MQTT初始化失败: {e}。程序将继续运行，但网络功能可能受限。")
    
        # 在AI初始化之前，先清空并显示状态
    pl.osd_img.clear()
    pl.osd_img.draw_string_advanced(10, 10, 24, "Initializing...", color=(255, 255, 255, 0))
    pl.show_image()

    try:
        pl.osd_img.draw_string_advanced(10, 40, 24, "Connecting to LAN...", color=(255, 255, 255, 0))
        pl.show_image()
        connect_using_lan()
        
        pl.osd_img.draw_string_advanced(10, 70, 24, "Connecting to MQTT...", color=(255, 255, 255, 0))
        pl.show_image()
        mqtt_connect()

    except Exception as e:
        pl.osd_img.draw_string_advanced(10, 100, 24, f"Network Error: {e}", color=(255, 255, 0, 0))
        pl.show_image()
        time.sleep(3) # 显示错误信息几秒钟



    # ... 模型路径、标签等配置保持不变 ...
    kmodel_path = "/sdcard/examples/my_kmodel/object_detect_yolov8n/yolo11n_640_best.kmodel"
    labels = ["person", "fall", "hand", "cigarette", "lighter"]
    confidence_threshold, nms_threshold = 0.5, 0.35
    max_boxes_num, model_input_size = 10, [640, 640]
    display_size = [960, 540]

    ob_det = None
    last_sent_status = -1
    last_sent_time = 0
    IDLE_REPORT_INTERVAL = 60  # “一切正常”状态上报间隔，单位：秒

    # ⭐ 新增：用于状态稳定/防抖的变量
    STATE_CONFIRM_SECONDS = 3.0      # 状态需要稳定持续2秒才被确认 (您可以按需调整这个值)
    potential_status = STATUS_OD_IDLE
    confirmed_status = STATUS_OD_IDLE  # 系统最终确认的、用于上报的状态
    status_change_time = time.time()   # “潜在状态”开始出现的时间点

    last_reconnect_attempt = 0
    tp = TOUCH(0)
    exit_btn_x, exit_btn_y = 870, 446  # 右下角exit位置

    #  新增：跌倒自动出动相关变量
    AUTO_DISPATCH_FALL_DURATION = 10  # (秒) 跌倒持续超过这个时间，将自动出动小车，您可以按需修改
    fall_start_time = 0               # 记录跌倒状态开始的时间点，0表示未在计时
    is_vehicle_dispatched_for_fall = False # 标记是否已为本次长时间跌倒出动过小车，防止重复发送指令

    # 🆕 新增：跌倒状态消失后的“宽限期”变量
    FALL_RESET_GRACE_PERIOD = 3.0     # (秒) 跌倒状态消失超过这个时间，才真正重置计时器
    fall_disappeared_time = 0         # 记录跌倒状态消失的时间点


    try:
        ob_det = ObjectDetectionApp(kmodel_path,labels=labels,model_input_size=model_input_size,
                                     max_boxes_num=max_boxes_num,confidence_threshold=confidence_threshold,
                                     nms_threshold=nms_threshold,rgb888p_size=pipeline_input_size,
                                     display_size=display_size,debug_mode=0)
        ob_det.config_preprocess(input_image_size=pipeline_input_size)

        last_touch = None



        while True:
            # ⭐ 主循环中增加对MQTT消息的检查
            if is_mqtt_connected:
                try:
                    # 非阻塞检查，如果收到消息，会自动调用上面设置的回调函数
                    mqtt_client.check_msg()
                except Exception as e:
                    print(f"检查MQTT消息时出错: {e}")
                    # 可以考虑在这里做重连逻辑
                    is_mqtt_connected = False
                    last_reconnect_attempt = time.time() # 立即准备重连

            # 新增：MQTT自动重连逻辑
            if not is_mqtt_connected and (time.time() - last_reconnect_attempt > 5):
                print("MQTT 连接已断开，正在尝试后台重连...")
                mqtt_connect() # 调用现有的连接函数
                last_reconnect_attempt = time.time()     

            points = tp.read()
            if points and len(points) > 0:
                p = points[0]
                tx, ty = 960 - p.x, 536 - p.y  # 坐标翻转

                if (not last_touch) or abs(tx - last_touch[0]) > 10 or abs(ty - last_touch[1]) > 10:
                    last_touch = (tx, ty)
                    print(f"[Touch] ({tx}, {ty})")

                    if is_in_area(tx, ty, exit_btn_x, exit_btn_y):
                        print("【触摸exit】退出目标检测程序...")
                        break
            else:
                last_touch = None
                
            img = pl.get_frame()
            res = ob_det.run(img)
            ob_det.draw_result(pl, res)
            pl.osd_img.draw_string_advanced(exit_btn_x, exit_btn_y, font_size, "exit", color=exit_color)
            pl.show_image()
            # ==================================================================
            # 🔧 修改：全新的状态判断与发送逻辑 (集成防抖和心跳)
            # ==================================================================
            # _send_ai_status_packet(uart_obj, STATUS_DISPATCH_VEHICLE_1)

            # 1. 从当前帧获取“原始”检测状态
            raw_status = STATUS_OD_IDLE
            if res is not None and len(res) > 0:
                has_fall, has_person, has_hand, has_smoke_item = False, False, False, False
                for det in res:
                    class_name = labels[int(det[5])]
                    if class_name == 'fall': has_fall = True
                    elif class_name == 'person': has_person = True
                    elif class_name == 'hand': has_hand = True
                    elif class_name in ['cigarette', 'lighter']: has_smoke_item = True

                if has_fall: raw_status = STATUS_FALL_DETECTED
                elif has_hand and has_smoke_item: raw_status = STATUS_SMOKING_DETECTED
                elif has_person: raw_status = STATUS_PERSON_DETECTED

            # 2. 状态防抖/稳定化处理
            now = time.time()
            
            # 如果当前帧的“原始状态”与“潜在状态”不一致，说明发生了变化
            # 更新“潜在状态”，并重置计时器
            if raw_status != potential_status:
                potential_status = raw_status
                status_change_time = now

            # 只有当一个“潜在状态”持续了足够长的时间，它才会被“确认”
            # 并且，只在“确认状态”需要更新时才进行赋值操作
            if confirmed_status != potential_status and (now - status_change_time) >= STATE_CONFIRM_SECONDS:
                print(f"状态 '{STATUS_TEXT_MAP.get(potential_status)}' 已持续 {STATE_CONFIRM_SECONDS} 秒, 现已确认为稳定状态。")
                confirmed_status = potential_status

            # ==================================================================
            # 🆕 新增：跌倒超时自动出动逻辑 (带防误识别中断的宽限期)
            # ==================================================================
            # A. 检查并启动或在宽限期后重置计时器
            if confirmed_status == STATUS_FALL_DETECTED:
                # 如果是跌倒状态，且主计时器未启动，则启动它
                if fall_start_time == 0:
                    fall_start_time = time.time()
                    print(f"-> 跌倒状态已确认，开始计时 (超时 {AUTO_DISPATCH_FALL_DURATION} 秒后将自动出动)...")
                # 如果跌倒状态恢复，则重置“消失”计时器
                if fall_disappeared_time != 0:
                    fall_disappeared_time = 0
            else:
                # 如果当前不是跌倒状态，但之前是（主计时器已启动）
                if fall_start_time > 0:
                    # 启动“消失”计时器（如果它还没启动）
                    if fall_disappeared_time == 0:
                        print(f"-> 跌倒状态暂时消失，进入 {FALL_RESET_GRACE_PERIOD} 秒宽限期...")
                        fall_disappeared_time = time.time()

                    # 只有当“消失”时间超过了宽限期，才真正重置一切
                    if (time.time() - fall_disappeared_time) > FALL_RESET_GRACE_PERIOD:
                        print(f"-> 跌倒状态消失超过 {FALL_RESET_GRACE_PERIOD} 秒，正式重置计时器。")
                        fall_start_time = 0
                        is_vehicle_dispatched_for_fall = False
                        fall_disappeared_time = 0 # 也要重置自己

            # 🆕 START: 改动区域 (修改自动出动逻辑以使用全局变量)
            # B. 判断是否达到自动出动条件
            if (fall_start_time > 0 and
                (time.time() - fall_start_time) > AUTO_DISPATCH_FALL_DURATION and
                not is_vehicle_dispatched_for_fall):

                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                print(f"!! 紧急：跌倒已持续超过 {AUTO_DISPATCH_FALL_DURATION} 秒，自动出动小车！")

                # 使用全局变量中存储的地点
                auto_dispatch_status = g_auto_dispatch_location
                auto_dispatch_status_uart = g_auto_dispatch_location_uart
                _send_ai_status_packet(uart_obj, auto_dispatch_status)           
                publish_mqtt_status(auto_dispatch_status, STATUS_TEXT_MAP.get(auto_dispatch_status, "自动指令：出动小车"))

                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

                is_vehicle_dispatched_for_fall = True


            # 3. 基于“确认后”的状态，结合心跳逻辑，判断是否需要发送
            should_send = False

            # 条件1: “确认状态”是新的，且与上次发送的状态不同
            if confirmed_status != last_sent_status:
                should_send = True
            # 条件2: “确认状态”是“一切正常”，并且距离上次发送超过了心跳间隔
            elif confirmed_status == STATUS_OD_IDLE and (now - last_sent_time) > IDLE_REPORT_INTERVAL:
                # print(f"状态正常，距离上次通信已超过 {IDLE_REPORT_INTERVAL} 秒，发送一次心跳包。") # 此日志可按需开启
                should_send = True

            # 4. 如果需要，执行发送操作
            if should_send:
                print("----------------------------------------")
                print(f"发送状态: {STATUS_TEXT_MAP.get(confirmed_status, '未知')}")
                #_send_ai_status_packet(uart_obj, confirmed_status)
                publish_mqtt_status(confirmed_status, STATUS_TEXT_MAP.get(confirmed_status, "未知状态"))
                print("----------------------------------------")
                
                # 更新最后发送的状态和时间
                last_sent_status = confirmed_status
                last_sent_time = now
            
            gc.collect()


    except Exception as e:
        sys.print_exception(e)

    finally:
        # ... 清理程序 (保持不变) ...
        print("--- 开始执行清理程序 ---")
        #_send_ai_status_packet(uart_obj, STATUS_OD_IDLE)
        if mqtt_client and is_mqtt_connected:
            publish_mqtt_status(STATUS_OD_IDLE, STATUS_TEXT_MAP[STATUS_OD_IDLE])
            mqtt_client.disconnect()
            print("MQTT 连接已断开。")
        if ob_det is not None:
            ob_det.deinit()
            del ob_det
        print("--- 目标检测模块清理完成 ---")
