# ==============================================================================
# 导入所有必需的库
# ==============================================================================
from libs.PipeLine import PipeLine, ScopedTiming
from libs.AIBase import AIBase
from libs.AI2D import Ai2d
import os, ujson, random, gc, sys, math
import nncase_runtime as nn
import ulab.numpy as np
import time, utime, image
import aidemo
from machine import Pin, FPIOA, UART, TOUCH, PWM
import network
from umqtt.simple import MQTTClient

# ==============================================================================
# 全局变量与MQTT通信模块 (采用您指定的框架)
# ==============================================================================
# --- MQTT 配置 ---
MQTT_BROKER_HOST = 'broker.emqx.io'
MQTT_TOPIC = b'k230/ai/status_feed'       # 【状态上报】主题
MQTT_CMD_TOPIC = b'k230/ai/command'      # 【指令下发】主题
CLIENT_ID = 'k230_board_' + str(random.randint(1000, 9999))

# --- 全局变量 ---
mqtt_client = None
is_mqtt_connected = False
g_uart_obj = None # 用于在回调中访问uart对象


# ⭐ 新增：模式定义
MODE_VISITOR = 0
MODE_REGISTRATION = 1

# ⭐ 新增：全局当前模式变量，默认为访客模式
g_current_mode = MODE_VISITOR

# --- 网络连接函数 ---
def connect_using_lan():
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

# --- 状态码定义 ---
STATUS_OD_IDLE = 0x10
STATUS_PERSON_DETECTED = 0x11
STATUS_FALL_DETECTED = 0x12
STATUS_SMOKING_DETECTED = 0x13
STATUS_FACE_RECOGNIZED = 0x21
STATUS_UNAUTHORIZED_PERSON = 0x22  # ⭐ 新增：未授权人员状态码
STATUS_DISPATCH_VEHICLE = 0xa0

STATUS_TEXT_MAP = {
    STATUS_OD_IDLE: "一切正常",
    STATUS_PERSON_DETECTED: "检测到有人",
    STATUS_FALL_DETECTED: "检测到跌倒",
    STATUS_SMOKING_DETECTED: "检测到吸烟",
    STATUS_FACE_RECOGNIZED: "识别到授权人员",
    STATUS_UNAUTHORIZED_PERSON: "检测到未授权人员", # ⭐ 新增
    STATUS_DISPATCH_VEHICLE: "远程指令：出动小车"
}

def _send_ai_status_packet(uart_obj, status_code):
    if uart_obj:
        payload_byte = status_code.to_bytes(1, 'big')
        packet = b'\xAA' + payload_byte + b'\x55'
        uart_obj.write(packet)
        print(f"UART Sent Status: {hex(status_code)}")

# ==============================================================================       
# 请用这段代码替换您 K230 Python 脚本中现有的 mqtt_command_callback 函数
# ==============================================================================
def mqtt_command_callback(topic, msg):
    global g_uart_obj, g_current_mode
    try:
        # 确保主题是我们期望的指令主题
        if topic.decode() == MQTT_CMD_TOPIC.decode():
            print(f"MQTT Recv CMD < {msg.decode()}")
            data = ujson.loads(msg)
            command = data.get("command")

            # --- 处理小车调度指令 ---
            if command == "dispatch_vehicle":
                print("收到'出动小车'指令，准备通过串口发送...")
                if g_uart_obj:
                    _send_ai_status_packet(g_uart_obj, STATUS_DISPATCH_VEHICLE)
                else:
                    print("错误：UART对象未初始化，无法发送指令。")

            # --- 处理进入注册模式指令 ---
            elif command == "enter_registration_mode":
                print("[MODE] 收到指令: 切换到注册模式")
                g_current_mode = MODE_REGISTRATION
                # 关键：向服务器回传确认消息，通知网页更新UI
                payload = {"event_type": "mode_change", "mode": "registration"}
                publish_mqtt_event(payload)
                print("[MODE] 已发送'注册模式'确认回执")

            # --- 处理退出注册模式（返回访客模式）指令 ---
            elif command == "exit_registration_mode":
                print("[MODE] 收到指令: 切换到访客模式")
                g_current_mode = MODE_VISITOR
                # 关键：向服务器回传确认消息，通知网页更新UI
                payload = {"event_type": "mode_change", "mode": "visitor"}
                publish_mqtt_event(payload)
                print("[MODE] 已发送'访客模式'确认回执")

            # --- 可以添加对其他指令的处理 ---
            # elif command == "set_location":
            #     print(f"收到设置地点指令，新地点: {data.get('location')}")
            #     # 在这里添加处理地点切换的逻辑...

    except Exception as e:
        print(f"处理MQTT指令时出错: {e}")


# --- MQTT 数据发布函数 (参考您提供的版本) ---
# --- MQTT 数据发布函数 ---
# ⭐ 修改：现在接收一个完整的 payload 字典作为参数
def publish_mqtt_event(payload):
    global mqtt_client, is_mqtt_connected
    if not is_mqtt_connected:
        print("MQTT 未连接，尝试重连...")
        if not mqtt_connect():
            print("重连失败，本次数据未发送。")
            return
    try:
        # 补充设备ID和时间戳
        payload["device_id"] = CLIENT_ID
        payload["timestamp"] = time.time()
        payload_json = ujson.dumps(payload)
        mqtt_client.publish(MQTT_TOPIC, payload_json.encode('utf-8'))
        print(f"MQTT 已发送 -> {payload_json}")
    except Exception as e:
        print(f"MQTT 消息发送失败: {e}")
        is_mqtt_connected = False

# --- MQTT 连接函数 ---
def mqtt_connect():
    global mqtt_client, is_mqtt_connected
    print(f"\n--- 准备连接到 MQTT 服务器: {MQTT_BROKER_HOST} ---")
    mqtt_client = MQTTClient(CLIENT_ID, MQTT_BROKER_HOST, keepalive=60)
    mqtt_client.set_callback(mqtt_command_callback)
    try:
        mqtt_client.connect()
        print("MQTT 服务器连接成功！")
        mqtt_client.subscribe(MQTT_CMD_TOPIC)
        print(f"MQTT 已订阅指令主题: {MQTT_CMD_TOPIC.decode()}")
        is_mqtt_connected = True
        return True
    except Exception as e:
        print(f"MQTT 服务器连接失败: {e}")
        is_mqtt_connected = False
        return False
    
def next_db_filename(db_dir, prefix="user", ext=".bin"):
    """
    在数据库目录下生成形如 user_0001.bin 的下一个可用文件名。
    """
    existing = [f for f in os.listdir(db_dir) if f.startswith(prefix) and f.endswith(ext)]
    nums = []
    for f in existing:
        try:
            nums.append(int(f[len(prefix)+1:-len(ext)]))
        except:
            pass
    n = max(nums, default=0) + 1
    return f"{db_dir}{prefix}_{n:04d}{ext}"

# 实例化FPIOA
fpioa = FPIOA()

# 触摸按钮区域定义
letter_positions = {
    'register': (820, 89),
    'clear': (855, 267),
    'exit': (870, 446)
}

font_size = 30

# 显示触摸按钮
def show_touch_buttons(pl, mode):
    pl.osd_img.clear()
    if mode == MODE_REGISTRATION:
        pl.osd_img.draw_string_advanced(10, 10 + 30, 24, "注册模式 (exit返回访客模式)", color=(255, 255, 0, 0)) # 向下移动30像素
        for word, (x, y) in letter_positions.items():
            pl.osd_img.draw_string_advanced(x, y, font_size, word, color=(100, 100, 255, 255))
    else: # MODE_VISITOR
        pl.osd_img.draw_string_advanced(10, 10 + 30, 24, "访客模式", color=(255, 0, 255, 0)) # 向下移动30像素
         # 在访客模式下也显示 exit 按钮，但颜色可以不那么醒目
        pl.osd_img.draw_string_advanced(letter_positions['exit'][0], letter_positions['exit'][1], font_size, 'exit', color=(150, 150, 150, 255)) # 使用灰色显示 exit
    pl.show_image() # 立即刷新屏幕以显示/隐藏按钮

# 判断触摸点是否在按钮区域
def is_in_area(tx, ty, cx, cy, w=100, h=40):
    return (cx <= tx <= cx + w) and (cy <= ty <= cy + h)

def ALIGN_UP(x, align):
    return (x + (align - 1)) // align * align

# 自定义人脸检测任务类
class FaceDetApp(AIBase):
    def __init__(self,kmodel_path,model_input_size,anchors,confidence_threshold=0.25,nms_threshold=0.3,rgb888p_size=[1920,1080],display_size=[1920,1080],debug_mode=0):
        super().__init__(kmodel_path,model_input_size,rgb888p_size,debug_mode)
        # kmodel路径
        self.kmodel_path=kmodel_path
        # 检测模型输入分辨率
        self.model_input_size=model_input_size
        # 置信度阈值
        self.confidence_threshold=confidence_threshold
        # nms阈值
        self.nms_threshold=nms_threshold
        self.anchors=anchors
        # sensor给到AI的图像分辨率，宽16字节对齐
        self.rgb888p_size=[ALIGN_UP(rgb888p_size[0],16),rgb888p_size[1]]
        # 视频输出VO分辨率，宽16字节对齐
        self.display_size=[ALIGN_UP(display_size[0],16),display_size[1]]
        # debug模式
        self.debug_mode=debug_mode
        # 实例化Ai2d，用于实现模型预处理
        self.ai2d=Ai2d(debug_mode)
        # 设置Ai2d的输入输出格式和类型
        self.ai2d.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT,nn.ai2d_format.NCHW_FMT,np.uint8, np.uint8)

    # 配置预处理操作，这里使用了pad和resize，Ai2d支持crop/shift/pad/resize/affine，具体代码请打开/sdcard/app/libs/AI2D.py查看
    def config_preprocess(self,input_image_size=None):
        with ScopedTiming("set preprocess config",self.debug_mode > 0):
            # 初始化ai2d预处理配置，默认为sensor给到AI的尺寸，可以通过设置input_image_size自行修改输入尺寸
            ai2d_input_size=input_image_size if input_image_size else self.rgb888p_size
            # 计算padding参数，并设置padding预处理
            self.ai2d.pad(self.get_pad_param(), 0, [104,117,123])
            # 设置resize预处理
            self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
            # 构建预处理流程,参数为预处理输入tensor的shape和预处理输出的tensor的shape
            self.ai2d.build([1,3,ai2d_input_size[1],ai2d_input_size[0]],[1,3,self.model_input_size[1],self.model_input_size[0]])

    # 自定义后处理，results是模型输出的array列表，这里使用了aidemo库的face_det_post_process接口
    def postprocess(self,results):
        with ScopedTiming("postprocess",self.debug_mode > 0):
            res = aidemo.face_det_post_process(self.confidence_threshold,self.nms_threshold,self.model_input_size[0],self.anchors,self.rgb888p_size,results)
            if len(res)==0:
                return res,res
            else:
                return res[0],res[1]

    def get_pad_param(self):
        dst_w = self.model_input_size[0]
        dst_h = self.model_input_size[1]
        # 计算最小的缩放比例，等比例缩放
        ratio_w = dst_w / self.rgb888p_size[0]
        ratio_h = dst_h / self.rgb888p_size[1]
        if ratio_w < ratio_h:
            ratio = ratio_w
        else:
            ratio = ratio_h
        new_w = (int)(ratio * self.rgb888p_size[0])
        new_h = (int)(ratio * self.rgb888p_size[1])
        dw = (dst_w - new_w) / 2
        dh = (dst_h - new_h) / 2
        top = (int)(round(0))
        bottom = (int)(round(dh * 2 + 0.1))
        left = (int)(round(0))
        right = (int)(round(dw * 2 - 0.1))
        return [0,0,0,0,top, bottom, left, right]

# 自定义人脸注册任务类
class FaceRegistrationApp(AIBase):
    def __init__(self,kmodel_path,model_input_size,rgb888p_size=[1920,1080],display_size=[1920,1080],debug_mode=0):
        super().__init__(kmodel_path,model_input_size,rgb888p_size,debug_mode)
        # kmodel路径
        self.kmodel_path=kmodel_path
        # 检测模型输入分辨率
        self.model_input_size=model_input_size
        # sensor给到AI的图像分辨率，宽16字节对齐
        self.rgb888p_size=[ALIGN_UP(rgb888p_size[0],16),rgb888p_size[1]]
        # 视频输出VO分辨率，宽16字节对齐
        self.display_size=[ALIGN_UP(display_size[0],16),display_size[1]]
        # debug模式
        self.debug_mode=debug_mode
        # 标准5官
        self.umeyama_args_112 = [
            38.2946 , 51.6963 ,
            73.5318 , 51.5014 ,
            56.0252 , 71.7366 ,
            41.5493 , 92.3655 ,
            70.7299 , 92.2041
        ]
        self.ai2d=Ai2d(debug_mode)
        self.ai2d.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT,nn.ai2d_format.NCHW_FMT,np.uint8, np.uint8)

    # 配置预处理操作，这里使用了affine，Ai2d支持crop/shift/pad/resize/affine，具体代码请打开/sdcard/app/libs/AI2D.py查看
    def config_preprocess(self,landm,input_image_size=None):
        with ScopedTiming("set preprocess config",self.debug_mode > 0):
            ai2d_input_size=input_image_size if input_image_size else self.rgb888p_size
            # 计算affine矩阵，并设置仿射变换预处理
            affine_matrix = self.get_affine_matrix(landm)
            self.ai2d.affine(nn.interp_method.cv2_bilinear,0, 0, 127, 1,affine_matrix)
            # 构建预处理流程,参数为预处理输入tensor的shape和预处理输出的tensor的shape
            self.ai2d.build([1,3,ai2d_input_size[1],ai2d_input_size[0]],[1,3,self.model_input_size[1],self.model_input_size[0]])

    # 自定义后处理
    def postprocess(self,results):
        with ScopedTiming("postprocess",self.debug_mode > 0):
            return results[0][0]

    def svd22(self,a):
        # svd
        s = [0.0, 0.0]
        u = [0.0, 0.0, 0.0, 0.0]
        v = [0.0, 0.0, 0.0, 0.0]
        s[0] = (math.sqrt((a[0] - a[3]) ** 2 + (a[1] + a[2]) ** 2) + math.sqrt((a[0] + a[3]) ** 2 + (a[1] - a[2]) ** 2)) / 2
        s[1] = abs(s[0] - math.sqrt((a[0] - a[3]) ** 2 + (a[1] + a[2]) ** 2))
        v[2] = math.sin((math.atan2(2 * (a[0] * a[1] + a[2] * a[3]), a[0] ** 2 - a[1] ** 2 + a[2] ** 2 - a[3] ** 2)) / 2) if \
        s[0] > s[1] else 0
        v[0] = math.sqrt(1 - v[2] ** 2)
        v[1] = -v[2]
        v[3] = v[0]
        u[0] = -(a[0] * v[0] + a[1] * v[2]) / s[0] if s[0] != 0 else 1
        u[2] = -(a[2] * v[0] + a[3] * v[2]) / s[0] if s[0] != 0 else 0
        u[1] = (a[0] * v[1] + a[1] * v[3]) / s[1] if s[1] != 0 else -u[2]
        u[3] = (a[2] * v[1] + a[3] * v[3]) / s[1] if s[1] != 0 else u[0]
        v[0] = -v[0]
        v[2] = -v[2]
        return u, s, v

    def image_umeyama_112(self,src):
        # 使用Umeyama算法计算仿射变换矩阵
        SRC_NUM = 5
        SRC_DIM = 2
        src_mean = [0.0, 0.0]
        dst_mean = [0.0, 0.0]
        for i in range(0,SRC_NUM * 2,2):
            src_mean[0] += src[i]
            src_mean[1] += src[i + 1]
            dst_mean[0] += self.umeyama_args_112[i]
            dst_mean[1] += self.umeyama_args_112[i + 1]
        src_mean[0] /= SRC_NUM
        src_mean[1] /= SRC_NUM
        dst_mean[0] /= SRC_NUM
        dst_mean[1] /= SRC_NUM
        src_demean = [[0.0, 0.0] for _ in range(SRC_NUM)]
        dst_demean = [[0.0, 0.0] for _ in range(SRC_NUM)]
        for i in range(SRC_NUM):
            src_demean[i][0] = src[2 * i] - src_mean[0]
            src_demean[i][1] = src[2 * i + 1] - src_mean[1]
            dst_demean[i][0] = self.umeyama_args_112[2 * i] - dst_mean[0]
            dst_demean[i][1] = self.umeyama_args_112[2 * i + 1] - dst_mean[1]
        A = [[0.0, 0.0], [0.0, 0.0]]
        for i in range(SRC_DIM):
            for k in range(SRC_DIM):
                for j in range(SRC_NUM):
                    A[i][k] += dst_demean[j][i] * src_demean[j][k]
                A[i][k] /= SRC_NUM
        T = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        U, S, V = self.svd22([A[0][0], A[0][1], A[1][0], A[1][1]])
        T[0][0] = U[0] * V[0] + U[1] * V[2]
        T[0][1] = U[0] * V[1] + U[1] * V[3]
        T[1][0] = U[2] * V[0] + U[3] * V[2]
        T[1][1] = U[2] * V[1] + U[3] * V[3]
        scale = 1.0
        src_demean_mean = [0.0, 0.0]
        src_demean_var = [0.0, 0.0]
        for i in range(SRC_NUM):
            src_demean_mean[0] += src_demean[i][0]
            src_demean_mean[1] += src_demean[i][1]
        src_demean_mean[0] /= SRC_NUM
        src_demean_mean[1] /= SRC_NUM
        for i in range(SRC_NUM):
            src_demean_var[0] += (src_demean_mean[0] - src_demean[i][0]) * (src_demean_mean[0] - src_demean[i][0])
            src_demean_var[1] += (src_demean_mean[1] - src_demean[i][1]) * (src_demean_mean[1] - src_demean[i][1])
        src_demean_var[0] /= SRC_NUM
        src_demean_var[1] /= SRC_NUM
        scale = 1.0 / (src_demean_var[0] + src_demean_var[1]) * (S[0] + S[1])
        T[0][2] = dst_mean[0] - scale * (T[0][0] * src_mean[0] + T[0][1] * src_mean[1])
        T[1][2] = dst_mean[1] - scale * (T[1][0] * src_mean[0] + T[1][1] * src_mean[1])
        T[0][0] *= scale
        T[0][1] *= scale
        T[1][0] *= scale
        T[1][1] *= scale
        return T

    def get_affine_matrix(self,sparse_points):
        # 获取affine变换矩阵
        with ScopedTiming("get_affine_matrix", self.debug_mode > 1):
            # 使用Umeyama算法计算仿射变换矩阵
            matrix_dst = self.image_umeyama_112(sparse_points)
            matrix_dst = [matrix_dst[0][0],matrix_dst[0][1],matrix_dst[0][2],
                          matrix_dst[1][0],matrix_dst[1][1],matrix_dst[1][2]]
            return matrix_dst

# 人脸识别任务类
class FaceRecognition:
    def __init__(self,face_det_kmodel,face_reg_kmodel,det_input_size,reg_input_size,database_dir,anchors,confidence_threshold=0.25,nms_threshold=0.3,face_recognition_threshold=0.75,rgb888p_size=[1280,720],display_size=[1920,1080],debug_mode=0):
        # 人脸检测模型路径
        self.face_det_kmodel=face_det_kmodel
        # 人脸识别模型路径
        self.face_reg_kmodel=face_reg_kmodel
        # 人脸检测模型输入分辨率
        self.det_input_size=det_input_size
        # 人脸识别模型输入分辨率
        self.reg_input_size=reg_input_size
        self.database_dir=database_dir
        # anchors
        self.anchors=anchors
        # 置信度阈值
        self.confidence_threshold=confidence_threshold
        # nms阈值
        self.nms_threshold=nms_threshold
        self.face_recognition_threshold=face_recognition_threshold
        # sensor给到AI的图像分辨率，宽16字节对齐
        self.rgb888p_size=[ALIGN_UP(rgb888p_size[0],16),rgb888p_size[1]]
        # 视频输出VO分辨率，宽16字节对齐
        self.display_size=[ALIGN_UP(display_size[0],16),display_size[1]]
        # debug_mode模式
        self.debug_mode=debug_mode
        self.max_register_face = 100                  # 数据库最多人脸个数
        self.feature_num = 128                        # 人脸识别特征维度
        self.valid_register_face = 0                  # 已注册人脸数
        self.db_name= []
        self.db_data= []
        self.face_det=FaceDetApp(self.face_det_kmodel,model_input_size=self.det_input_size,anchors=self.anchors,confidence_threshold=self.confidence_threshold,nms_threshold=self.nms_threshold,rgb888p_size=self.rgb888p_size,display_size=self.display_size,debug_mode=0)
        self.face_reg=FaceRegistrationApp(self.face_reg_kmodel,model_input_size=self.reg_input_size,rgb888p_size=self.rgb888p_size,display_size=self.display_size)
        self.face_det.config_preprocess()
        # 人脸数据库初始化
        self.database_init()

    # run函数
    def run(self, input_np):
        det_boxes, landms = self.face_det.run(input_np)
        recg_res = []
        for landm in landms:
            self.face_reg.config_preprocess(landm)
            feature = self.face_reg.run(input_np)
            recg_res.append(self.database_search(feature))
        # 现在返回三个量
        return det_boxes, landms, recg_res

    def database_init(self):
        # 数据初始化，构建数据库人名列表和数据库特征列表
        with ScopedTiming("database_init", self.debug_mode > 1):
            db_file_list = os.listdir(self.database_dir)
            for db_file in db_file_list:
                if not db_file.endswith('.bin'):
                    continue
                if self.valid_register_face >= self.max_register_face:
                    break
                valid_index = self.valid_register_face
                full_db_file = self.database_dir + db_file
                with open(full_db_file, 'rb') as f:
                    data = f.read()
                feature = np.frombuffer(data, dtype=np.float)
                self.db_data.append(feature)
                name = db_file.split('.')[0]
                self.db_name.append(name)
                self.valid_register_face += 1

    def database_reset(self):
        # 数据库清空
        with ScopedTiming("database_reset", self.debug_mode > 1):
            print("database clearing...")
            self.db_name = []
            self.db_data = []
            self.valid_register_face = 0
            print("database clear Done!")

    def database_search(self,feature):
        # 数据库查询
        with ScopedTiming("database_search", self.debug_mode > 1):
            v_id = -1
            v_score_max = 0.0
            # 将当前人脸特征归一化
            feature /= np.linalg.norm(feature)
            # 遍历当前人脸数据库，统计最高得分
            for i in range(self.valid_register_face):
                db_feature = self.db_data[i]
                db_feature /= np.linalg.norm(db_feature)
                # 计算数据库特征与当前人脸特征相似度
                v_score = np.dot(feature, db_feature)/2 + 0.5
                if v_score > v_score_max:
                    v_score_max = v_score
                    v_id = i
            if v_id == -1:
                # 数据库中无人脸
                return 'unknown'
            elif v_score_max < self.face_recognition_threshold:
                # 小于人脸识别阈值，未识别
                return 'unknown'
            else:
                # 识别成功
                result = 'name: {}, score:{}'.format(self.db_name[v_id],v_score_max)
                return result

    # ⭐ 修复点 1：将 draw_result 的方法签名恢复原状
    def draw_result(self,pl,dets,recg_results):
        # ⭐ 修复点 2：在函数内部直接访问全局模式变量
        global g_current_mode
        show_touch_buttons(pl, g_current_mode)
        pl.osd_img.draw_string_advanced(10, 10, 24, "人脸识别中(exit退出)", color=(255, 255, 0, 0))
        
        if dets:
            for i,det in enumerate(dets):
                # （1）画人脸框
                x1, y1, w, h = map(lambda x: int(round(x, 0)), det[:4])
                x1 = x1 * self.display_size[0]//self.rgb888p_size[0]
                y1 = y1 * self.display_size[1]//self.rgb888p_size[1]
                w =  w * self.display_size[0]//self.rgb888p_size[0]
                h = h * self.display_size[1]//self.rgb888p_size[1]
                pl.osd_img.draw_rectangle(x1,y1, w, h, color=(255,0, 0, 255), thickness = 4)
                # （2）写人脸识别结果
                recg_text = recg_results[i]
                pl.osd_img.draw_string_advanced(x1,y1,32,recg_text,color=(255, 255, 0, 0))

task_should_stop = False

# ==============================================================================
# 人脸识别子程序 (已按您的参考代码风格修改)
# ==============================================================================
def run_face_recognition(pl, pipeline_input_size, uart_device):
    global g_uart_obj, is_mqtt_connected, CLIENT_ID, g_current_mode # ⭐ 引入 g_current_mode
    g_uart_obj = uart_device

    # 参数设置
    INIT_ANGLE = 40   # 初始角度 20°
    ACTIVE_ANGLE = 130 # 动作角度 120°
    SERVO_PIN_NUM = 20 
    # GPIO 映射
    FPIOA().set_function(SERVO_PIN_NUM, getattr(FPIOA, f"GPIO{SERVO_PIN_NUM}"))
    servo_pin = Pin(SERVO_PIN_NUM, Pin.OUT)

    # ⭐ 参考风格：在AI初始化之前，先进行网络连接并提供屏幕反馈
    pl.osd_img.clear()
    pl.osd_img.draw_string_advanced(10, 10, 24, "Initializing Face Recognition...", color=(255, 255, 255, 0))
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







    def angle_to_pulse_us(angle):
        """
        将角度映射到脉宽，范围500-2500us。
        500us对应0度，2500us对应180度
        """
        pulse_width = int(500 + (angle / 180.0) * 2000)
        return pulse_width

    def move_servo(angle, duration=1.0):
        """
        软件 PWM 控制舵机角度
        - angle: 目标角度 0~180
        - duration: 持续时间秒数
        """
        pulse_width = angle_to_pulse_us(angle)
        print(f"设置角度: {angle}° -> 脉宽: {pulse_width}us")

        period_us = 20000  # 20ms周期
        cycles = int(duration * 1000 / 20)  # 持续多少个20ms周期

        for _ in range(cycles):
            servo_pin.value(1)
            utime.sleep_us(pulse_width)
            servo_pin.value(0)
            utime.sleep_us(period_us - pulse_width)

    time.sleep(0.5)

    face_det_kmodel_path = "/sdcard/examples/kmodel/face_detection_320.kmodel"
    face_reg_kmodel_path = "/sdcard/examples/kmodel/face_recognition.kmodel"
    anchors_path = "/sdcard/examples/utils/prior_data_320.bin"
    database_dir = "/sdcard/examples/utils/db/"
    face_det_input_size = [320, 320]
    face_reg_input_size = [112, 112]
    confidence_threshold = 0.5
    nms_threshold = 0.2
    anchor_len = 4200
    det_dim = 4
    anchors = np.fromfile(anchors_path, dtype=np.float)
    anchors = anchors.reshape((anchor_len, det_dim))
    face_recognition_threshold = 0.75
    display_size = [960, 540]

    fr = None
    servo_busy = False
    servo_start_time = 0
    tp = TOUCH(0)

    last_reconnect_attempt = 0 # ⭐ 参考风格：初始化重连计时器

    try:
        fr = FaceRecognition(
            face_det_kmodel=face_det_kmodel_path,
            face_reg_kmodel=face_reg_kmodel_path,
            det_input_size=face_det_input_size,
            reg_input_size=face_reg_input_size,
            database_dir=database_dir,
            anchors=anchors,
            confidence_threshold=confidence_threshold,
            nms_threshold=nms_threshold,
            face_recognition_threshold=face_recognition_threshold,
            rgb888p_size=pipeline_input_size,
            display_size=display_size
        )

        # ⭐ 修改：根据初始模式显示按钮
        show_touch_buttons(pl, g_current_mode)
        last_touch = None
        
        
        # ⭐ 修改：为不同事件类型设置独立的冷却计时器
        last_recognized_person = None
        last_recognition_time = 0
        last_unauthorized_time = 0
        
        # ... (各种计时器变量初始化不变) ...
        last_mode = g_current_mode # ⭐ 新增：用于检测模式变化的变量 

        # ⭐ 修改：用于跟踪当前帧是否已经有授权人员，以避免同时上报未授权
        authorized_person_in_frame = False
        # ⭐ 新增：用于“失忆”缓冲的计时器和常量
        authorized_person_disappeared_time = None
        AUTH_RESET_BUFFER_MS = 3000 # 2秒缓冲时间

        # ⭐ 新增：用于“未授权人员”二次确认的计时器和常量
        unauthorized_pending_start_time = None
        UNAUTHORIZED_CONFIRM_DELAY_MS = 1000 # 1秒确认延迟

        # ⭐ 新增：用于“授权人员”二次确认的计时器和常量
        authorized_pending_start_time = None
        authorized_pending_user_name = None
        AUTHORIZED_CONFIRM_DELAY_MS = 1000 # 同样设置1秒确认延迟

        move_servo(INIT_ANGLE, duration=2.0)


        while True:
            # ⭐ 新增：检测模式是否从外部被改变，如果改变则刷新UI
            if last_mode != g_current_mode:
                show_touch_buttons(pl, g_current_mode)
                last_mode = g_current_mode

            # ⭐ 参考风格：主循环中增加对MQTT消息的检查和自动重连
            if is_mqtt_connected:
                try:
                    mqtt_client.check_msg()
                except Exception as e:
                    print(f"检查MQTT消息时出错: {e}")
                    is_mqtt_connected = False
                    last_reconnect_attempt = time.time()
            
            if not is_mqtt_connected and (time.time() - last_reconnect_attempt > 5):
                print("人脸识别模块: MQTT连接断开，尝试重连...")
                mqtt_connect()
                last_reconnect_attempt = time.time()

            img = pl.get_frame()
            det_boxes, landms, recg_res = fr.run(img)
            current_time = time.ticks_ms()

            # if servo_busy and time.ticks_diff(current_time, servo_start_time) > 8000:
            #     move_servo(INIT_ANGLE)
            #     servo_busy = False

            # ⭐ 核心修改：仅在访客模式下，才执行事件上报和舵机动作
            if g_current_mode == MODE_VISITOR:
                # ⭐ 1. 初始化本帧状态
                authorized_person_in_frame = False
                has_unknown_in_frame = any(r == 'unknown' for r in recg_res)

                # 首先，从当前帧的识别结果中找出第一个授权人员
                first_authorized_user_in_frame = None
                if recg_res:
                    for res in recg_res:
                        if isinstance(res, str) and res.startswith("name:"):
                            try:
                                first_authorized_user_in_frame = res.split(',')[0].split(':')[1].strip()
                                authorized_person_in_frame = True # 标记本帧有授权人员(供后续未授权逻辑使用)
                                break # 找到一个就够了，退出内循环
                            except IndexError:
                                continue

                # --- 新的延迟确认逻辑 ---
                if first_authorized_user_in_frame:
                    # 判断此人是否为“新候选人”（不是上次刚开过门的人，或者冷却时间已过）
                    is_new_candidate = (first_authorized_user_in_frame != last_recognized_person) or \
                                        (time.ticks_diff(current_time, last_recognition_time) > 10000)

                    if is_new_candidate:
                        # A. 如果当前没有正在确认的人，则为这个新候选人启动计时。
                        if authorized_pending_start_time is None:
                            print(f"[INFO] 初步识别授权人员({first_authorized_user_in_frame})，启动{AUTHORIZED_CONFIRM_DELAY_MS/1000}秒确认...")
                            authorized_pending_start_time = current_time
                            authorized_pending_user_name = first_authorized_user_in_frame
                        
                        # B. 如果当前帧的人和正在确认的是同一个人
                        elif first_authorized_user_in_frame == authorized_pending_user_name:
                            # 检查确认时间是否已到
                            if time.ticks_diff(current_time, authorized_pending_start_time) > AUTHORIZED_CONFIRM_DELAY_MS:
                                # 时间到，确认成功！执行所有操作
                                print(f"[EVENT] 确认授权人员: {authorized_pending_user_name}，准备上报")
                                
                                move_servo(ACTIVE_ANGLE, duration=2.0)

                                servo_start_time = current_time
                                servo_busy = True
                                
                                payload = {
                                    "event_type": "face_entry",
                                    "status_code": hex(STATUS_FACE_RECOGNIZED),
                                    "status_text": STATUS_TEXT_MAP.get(STATUS_FACE_RECOGNIZED),
                                    "user_name": authorized_pending_user_name,
                                }
                                publish_mqtt_event(payload)

                                last_recognized_person = authorized_pending_user_name
                                last_recognition_time = current_time

                                authorized_pending_start_time = None
                                authorized_pending_user_name = None
                        
                        # C. 如果当前帧的人和正在确认的不是同一个人，则重置计时器给新人
                        else:
                            print(f"[INFO] 候选人变更: 从 {authorized_pending_user_name} -> {first_authorized_user_in_frame}。重置计时...")
                            authorized_pending_start_time = current_time
                            authorized_pending_user_name = first_authorized_user_in_frame

                # 如果当前画面没有授权人员了
                else:
                    # 如果刚才还在确认某人，但他现在消失了，则取消确认
                    if authorized_pending_start_time is not None:
                        print(f"[INFO] 待确认的授权人员({authorized_pending_user_name})在确认期内消失，取消操作。")
                        authorized_pending_start_time = None
                        authorized_pending_user_name = None

                
                # ⭐ 3. 带延迟确认地处理未授权人员事件
                if not authorized_person_in_frame and has_unknown_in_frame:
                    # 仅在画面中无授权人员时，才启动未授权人员的判断逻辑
                    if unauthorized_pending_start_time is None:
                        # 第一次检测到，启动确认计时器
                        print("[INFO] 初步检测到未授权人员，启动1秒确认计时...")
                        unauthorized_pending_start_time = current_time
                    else:
                        # 已经处于确认等待中，检查是否超过1秒
                        if time.ticks_diff(current_time, unauthorized_pending_start_time) > UNAUTHORIZED_CONFIRM_DELAY_MS:
                            # 确认时间已到，并且距离上次发送超过10秒冷却期
                            if time.ticks_diff(current_time, last_unauthorized_time) > 10000:
                                print("[EVENT] 确认检测到未授权人员，准备上报")
                                payload = {
                                    "status_code": hex(STATUS_UNAUTHORIZED_PERSON),
                                    "status_text": STATUS_TEXT_MAP.get(STATUS_UNAUTHORIZED_PERSON)
                                }
                                publish_mqtt_event(payload)
                                last_unauthorized_time = current_time
                            
                            # 无论是否发送，都重置确认计时器，以准备下一次的初步检测
                            unauthorized_pending_start_time = None 
                else:
                    # 如果画面中没有未授权人员了，或者有授权人员出现，则必须取消确认计时
                    if unauthorized_pending_start_time is not None:
                        print("[INFO] 未授权人员在确认期内消失或有授权人员出现，取消上报。")
                        unauthorized_pending_start_time = None

                #  4. 带缓冲地重置“最后识别的人”的记忆
                if authorized_person_in_frame:
                    # 如果画面中仍有授权人员，则取消“失忆”计时
                    authorized_person_disappeared_time = None
                else:
                    # 如果画面中没有授权人员，则启动或检查“失忆”计时器
                    if authorized_person_disappeared_time is None:
                        # 如果是第一帧没看到授权人员，则启动计时器
                        authorized_person_disappeared_time = current_time
                    else:
                        # 如果已经看不到有一段时间了，检查是否超过缓冲期
                        if time.ticks_diff(current_time, authorized_person_disappeared_time) > AUTH_RESET_BUFFER_MS:
                            # 缓冲期已过，可以安全地忘记上一个人了
                            if last_recognized_person is not None:
                                print(f"[INFO] 授权人员({last_recognized_person})已离开超过缓冲期，重置记忆。")
                                last_recognized_person = None
                            authorized_person_disappeared_time = None # 重置计时器

            
            # ⭐ 修复点 3：调用 fr.draw_result 时，不再传入 g_current_mode
            fr.draw_result(pl, det_boxes, recg_res)
            pl.show_image()

            # ⭐ 修改触摸处理逻辑
            points = tp.read()
            if points and len(points) > 0:
                p = points[0]
                tx, ty = 960 - p.x, 536 - p.y

                if (not last_touch) or abs(tx - last_touch[0]) > 10 or abs(ty - last_touch[1]) > 10:
                    last_touch = (tx, ty)
                    
                    # --- 'exit' 按钮逻辑修复 ---
                    if is_in_area(tx, ty, *letter_positions['exit']):
                        if g_current_mode == MODE_REGISTRATION:
                            # 在注册模式下，退出到访客模式
                            print("[触摸] Exit: 切换到访客模式")
                            g_current_mode = MODE_VISITOR
                            payload = {"event_type": "mode_change", "mode": "visitor"}
                            publish_mqtt_event(payload)
                        else: # 当前是访客模式
                            # 在访客模式下，终止程序
                            print("[触摸] Exit: 终止程序")
                            break # 跳出主循环，执行finally中的清理代码

                    # 仅在注册模式下响应 register 和 clear 按钮
                    elif g_current_mode == MODE_REGISTRATION:
                        if is_in_area(tx, ty, *letter_positions['exit']):
                            print("[触摸] Exit 被触发，退出到访客模式")
                            g_current_mode = MODE_VISITOR
                            # ⭐ 发送状态变更通知给服务器
                            payload = {"event_type": "mode_change", "mode": "visitor"}
                            publish_mqtt_event(payload)

                        elif is_in_area(tx, ty, *letter_positions['clear']):
                            print("[触摸] Clear 被触发，清空人脸数据库")
                            try:
                                files = os.listdir(database_dir)
                                for file_name in files:
                                    os.remove(database_dir + file_name)
                                    print(f"  已删除: {file_name}")
                                uart_device.write(b"Database cleared.\n")
                                fr.database_reset()
                                fr.database_init()
                            except Exception as e:
                                print(f"清空数据库错误: {e}")
                                sys.print_exception(e)

                        elif is_in_area(tx, ty, *letter_positions['register']):
                            print("[触摸] Register 被触发，开始注册")
                            if len(det_boxes) == 0:
                                print("未检测到人脸")
                            else:
                                areas = det_boxes[:, 2] * det_boxes[:, 3]
                                landm_idx = int(np.argmax(areas))
                                largest_landm = landms[landm_idx]
                                fr.face_reg.config_preprocess(largest_landm)
                                feature = fr.face_reg.run(img)
                                new_path = next_db_filename(database_dir)
                                with open(new_path, "wb") as f:
                                    f.write(feature.tobytes())
                                user_name = new_path.split('/')[-1].split('.')[0]
                                print(f"  注册成功 -> {user_name}")
                                uart_device.write(f"Register success: {user_name}\n".encode())
                                fr.database_reset()
                                fr.database_init()
                    
            gc.collect()

    except Exception as e:
        print("人脸识别错误:", e)
        sys.print_exception(e)
    finally:
        print("--- 人脸识别模块开始清理 ---")
        if fr:
            fr.face_det.deinit()
            fr.face_reg.deinit()
        print("--- 人脸识别模块清理完成 ---")
