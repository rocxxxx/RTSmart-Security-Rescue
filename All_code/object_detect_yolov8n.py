#from libs.PipeLine import PipeLine, ScopedTiming
#from libs.AIBase import AIBase
#from libs.AI2D import Ai2d
#import os, ujson, random, gc, sys
#import nncase_runtime as nn   # 用于模型推理（Kmodel）
#import ulab.numpy as np       # 嵌入式版 numpy，节省资源
#import time, utime, image     # 嵌入式时间、图像模块
#import aidemo                 # 项目自定义模块，未具体展示
#from machine import Pin, FPIOA
#def ALIGN_UP(x, align):
#    return (x + (align - 1)) // align * align
#    # 实例化FPIOA
#fpioa = FPIOA()

## 设置行和列引脚
#fpioa.set_function(28, FPIOA.GPIO28)
#fpioa.set_function(29, FPIOA.GPIO29)
#fpioa.set_function(30, FPIOA.GPIO30)
#fpioa.set_function(31, FPIOA.GPIO31)

#fpioa.set_function(18, FPIOA.GPIO18)
#fpioa.set_function(19, FPIOA.GPIO19)
#fpioa.set_function(33, FPIOA.GPIO33)
#fpioa.set_function(35, FPIOA.GPIO35)

## 创建行对象
#row_pins = [28, 29, 30, 31]
#col_pins = [18, 19, 33, 35]

#rows = [Pin(p, Pin.IN, Pin.PULL_DOWN) for p in row_pins]
#cols = [Pin(p, Pin.OUT) for p in col_pins]

## 键盘矩阵
#names = [
#    ["1", "2", "3", "4"],
#    ["5", "6", "7", "8"],
#    ["9", "10", "11", "12"],
#    ["13", "14", "15", "16"]
#]


#def scan_key():
#    for i, col in enumerate(cols):
#        for c in cols:
#            c.value(0)
#        col.value(1)
#        time.sleep_ms(10)
#        for j, row in enumerate(rows):
#            if row.value():
#                return names[j][i]
#    return None



#class ObjectDetectionApp(AIBase):
#    def __init__(self,kmodel_path,labels,model_input_size,max_boxes_num,confidence_threshold=0.5,nms_threshold=0.2,rgb888p_size=[224,224],display_size=[1920,1080],debug_mode=0):
#        super().__init__(kmodel_path,model_input_size,rgb888p_size,debug_mode)
#        self.kmodel_path=kmodel_path
#        self.labels=labels
#        # 模型输入分辨率
#        self.model_input_size=model_input_size
#        # 阈值设置
#        self.confidence_threshold=confidence_threshold
#        self.nms_threshold=nms_threshold
#        self.max_boxes_num=max_boxes_num
#        # sensor给到AI的图像分辨率
#        self.rgb888p_size=[ALIGN_UP(rgb888p_size[0],16),rgb888p_size[1]]
#        # 显示分辨率
#        self.display_size=[ALIGN_UP(display_size[0],16),display_size[1]]
#        self.debug_mode=debug_mode
#        # 检测框预置颜色值
#        self.color_four=[(255, 220, 20, 60), (255, 119, 11, 32), (255, 0, 0, 142), (255, 0, 0, 230),
#                         (255, 106, 0, 228), (255, 0, 60, 100), (255, 0, 80, 100), (255, 0, 0, 70),
#                         (255, 0, 0, 192), (255, 250, 170, 30), (255, 100, 170, 30), (255, 220, 220, 0),
#                         (255, 175, 116, 175), (255, 250, 0, 30), (255, 165, 42, 42), (255, 255, 77, 255),
#                         (255, 0, 226, 252), (255, 182, 182, 255), (255, 0, 82, 0), (255, 120, 166, 157)]
#        # 宽高缩放比例
#        self.x_factor = float(self.rgb888p_size[0])/self.model_input_size[0]
#        self.y_factor = float(self.rgb888p_size[1])/self.model_input_size[1]
#        # Ai2d实例，用于实现模型预处理
#        self.ai2d=Ai2d(debug_mode)
#        # 设置Ai2d的输入输出格式和类型
#        self.ai2d.set_ai2d_dtype(nn.ai2d_format.NCHW_FMT,nn.ai2d_format.NCHW_FMT,np.uint8, np.uint8)

#    # 配置预处理操作，这里使用了resize，Ai2d支持crop/shift/pad/resize/affine，具体代码请打开/sdcard/app/libs/AI2D.py查看
#    def config_preprocess(self,input_image_size=None):  # 图像预处理
#        with ScopedTiming("set preprocess config",self.debug_mode > 0):
#            # 初始化ai2d预处理配置，默认为sensor给到AI的尺寸，您可以通过设置input_image_size自行修改输入尺寸
#            ai2d_input_size=input_image_size if input_image_size else self.rgb888p_size
#            self.ai2d.resize(nn.interp_method.tf_bilinear, nn.interp_mode.half_pixel)
#            print(f"Configuring Ai2d: Input {ai2d_input_size}, Output {self.model_input_size}")
#            self.ai2d.build([1,3,ai2d_input_size[1],ai2d_input_size[0]],[1,3,self.model_input_size[1],self.model_input_size[0]])

#    # 自定义当前任务的后处理
#    def postprocess(self,results):
#        with ScopedTiming("postprocess",self.debug_mode > 0):
#            result=results[0]
#            result = result.reshape((result.shape[0] * result.shape[1], result.shape[2]))
#            output_data = result.transpose()
#            boxes_ori = output_data[:,0:4]
#            scores_ori = output_data[:,4:]
#            confs_ori = np.max(scores_ori,axis=-1)
#            inds_ori = np.argmax(scores_ori,axis=-1)
#            boxes,scores,inds = [],[],[]
#            for i in range(len(boxes_ori)):
#                if confs_ori[i] > self.confidence_threshold:
#                    scores.append(confs_ori[i])
#                    inds.append(inds_ori[i])
#                    x = boxes_ori[i,0]
#                    y = boxes_ori[i,1]
#                    w = boxes_ori[i,2]
#                    h = boxes_ori[i,3]
#                    left = int((x - 0.5 * w) * self.x_factor)
#                    top = int((y - 0.5 * h) * self.y_factor)
#                    right = int((x + 0.5 * w) * self.x_factor)
#                    bottom = int((y + 0.5 * h) * self.y_factor)
#                    boxes.append([left,top,right,bottom])
#            if len(boxes)==0:
#                return []
#            boxes = np.array(boxes)
#            scores = np.array(scores)
#            inds = np.array(inds)
#            # NMS过程
#            keep = self.nms(boxes,scores,self.nms_threshold)
#            dets = np.concatenate((boxes, scores.reshape((len(boxes),1)), inds.reshape((len(boxes),1))), axis=1)
#            dets_out = []
#            for keep_i in keep:
#                dets_out.append(dets[keep_i])
#            dets_out = np.array(dets_out)
#            dets_out = dets_out[:self.max_boxes_num, :]
#            return dets_out

#    # 绘制结果
#    def draw_result(self,pl,dets):
#        with ScopedTiming("display_draw",self.debug_mode >0):
#            if dets:
#                pl.osd_img.clear()
#                for det in dets:
#                    x1, y1, x2, y2 = map(lambda x: int(round(x, 0)), det[:4])
#                    x= x1*self.display_size[0] // self.rgb888p_size[0]
#                    y= y1*self.display_size[1] // self.rgb888p_size[1]
#                    w = (x2 - x1) * self.display_size[0] // self.rgb888p_size[0]
#                    h = (y2 - y1) * self.display_size[1] // self.rgb888p_size[1]
#                    pl.osd_img.draw_rectangle(x,y, w, h, color=self.get_color(int(det[5])),thickness=4)
#                    pl.osd_img.draw_string_advanced( x , y-50,32," " + self.labels[int(det[5])] + " " + str(round(det[4],2)) , color=self.get_color(int(det[5])))
#            else:
#                pl.osd_img.clear()


#    # 多目标检测 非最大值抑制方法实现
#    def nms(self,boxes,scores,thresh):
#        """Pure Python NMS baseline."""
#        x1,y1,x2,y2 = boxes[:, 0],boxes[:, 1],boxes[:, 2],boxes[:, 3]
#        areas = (x2 - x1 + 1) * (y2 - y1 + 1)
#        order = np.argsort(scores,axis = 0)[::-1]
#        keep = []
#        while order.size > 0:
#            i = order[0]
#            keep.append(i)
#            new_x1,new_y1,new_x2,new_y2,new_areas = [],[],[],[],[]
#            for order_i in order:
#                new_x1.append(x1[order_i])
#                new_x2.append(x2[order_i])
#                new_y1.append(y1[order_i])
#                new_y2.append(y2[order_i])
#                new_areas.append(areas[order_i])
#            new_x1 = np.array(new_x1)
#            new_x2 = np.array(new_x2)
#            new_y1 = np.array(new_y1)
#            new_y2 = np.array(new_y2)
#            xx1 = np.maximum(x1[i], new_x1)
#            yy1 = np.maximum(y1[i], new_y1)
#            xx2 = np.minimum(x2[i], new_x2)
#            yy2 = np.minimum(y2[i], new_y2)
#            w = np.maximum(0.0, xx2 - xx1 + 1)
#            h = np.maximum(0.0, yy2 - yy1 + 1)
#            inter = w * h
#            new_areas = np.array(new_areas)
#            ovr = inter / (areas[i] + new_areas - inter)
#            new_order = []
#            for ovr_i,ind in enumerate(ovr):
#                if ind < thresh:
#                    new_order.append(order[ovr_i])
#            order = np.array(new_order,dtype=np.uint8)
#        return keep

#    # 根据当前类别索引获取框的颜色
#    def get_color(self, x):
#        idx=x%len(self.color_four)
#        return self.color_four[idx]


#def run_object_detection(pl, pipeline_input_size):
#    # 模型路径
#    kmodel_path="/sdcard/examples/my_kmodel/object_detect_yolov8n/yolov8n_320_best.kmodel"
#    labels = ["person", "fall", "hand", "cigarette", "lighter"]
#    # 其它参数设置
#    confidence_threshold = 0.2      # 置信度
#    nms_threshold = 0.2             # IOU
#    max_boxes_num = 50              # 框上限
##    rgb888p_size=[320,320]          # 摄像头采集原始图像尺寸
#    model_input_size = [320, 320]   # 模型输入尺寸

#    pipeline_rgb_size = [1920, 1080]
#    display_size = [800, 480] # LCD屏幕分辨率

#    # 1. 在 try 块开始之前，将所有需要清理的资源对象初始化为 None

#    ob_det = None
#    try:
#        # 初始化自定义目标检测实例
#        ob_det=ObjectDetectionApp(kmodel_path,labels=labels,model_input_size=model_input_size,max_boxes_num=max_boxes_num,confidence_threshold=confidence_threshold,nms_threshold=nms_threshold,rgb888p_size=pipeline_input_size,display_size=display_size,debug_mode=0)
#        ob_det.config_preprocess(input_image_size=pipeline_input_size)
#        while True:
#            os.exitpoint()
#            with ScopedTiming("total",1):
#                # 获取当前帧数据
#                img=pl.get_frame()
#                # 推理当前帧
#                res=ob_det.run(img)
#                # 绘制结果到PipeLine的osd图像
#                ob_det.draw_result(pl,res)
#                # 显示当前的绘制结果
#                pl.show_image()
#                gc.collect()
#                key = scan_key()
#                if key == "4":
#                    print("【键4】被按下，退出目标检测程序...")
#                    break  # 退出这个 while True 循环
#    except Exception as e:
#        sys.print_exception(e)
#    finally:
#        # 3. 现在，这里的安全检查可以确保程序在任何情况下都能正确清理
#        print("--- 开始执行清理程序 ---")

#        # 检查 ob_det 对象是否被成功创建
#        if ob_det is not None:
#            print("正在清理 ob_det 对象...")
#            ob_det.deinit()

#        print("--- 清理完成 ---")
#####################以上为基础代码####################


####################以下为串口修改版#######
# -*- coding: UTF-8 -*-
from libs.PipeLine import PipeLine, ScopedTiming
from libs.AIBase import AIBase
from libs.AI2D import Ai2d
import os, ujson, random, gc, sys
import nncase_runtime as nn
import ulab.numpy as np
import time, utime, image
import aidemo
from machine import Pin, FPIOA, UART

# ==============================================================================
# 模块专属的串口通信协议与功能 (保持不变)
# ==============================================================================
PACKET_HEADER = b'\xAA'
PACKET_FOOTER = b'\x55'
STATUS_OD_IDLE = 0x10
STATUS_PERSON_DETECTED = 0x11
STATUS_FALL_DETECTED = 0x12
STATUS_SMOKING_DETECTED = 0x13

def _send_ai_status_packet(uart_obj, status_code):
    if uart_obj:
        payload_byte = status_code.to_bytes(1, 'big')
        packet = PACKET_HEADER + payload_byte + PACKET_FOOTER
        uart_obj.write(packet)
        # ⭐ 打印到终端的功能在这里实现 ⭐
        print(f"UART Sent Status: {hex(status_code)}")
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

#    # 绘制结果
#    def draw_result(self,pl,dets):
#        with ScopedTiming("display_draw",self.debug_mode >0):
#            if dets:
#                pl.osd_img.clear()
#                for det in dets:
#                    x1, y1, x2, y2 = map(lambda x: int(round(x, 0)), det[:4])
#                    x= x1*self.display_size[0] // self.rgb888p_size[0]
#                    y= y1*self.display_size[1] // self.rgb888p_size[1]
#                    w = (x2 - x1) * self.display_size[0] // self.rgb888p_size[0]
#                    h = (y2 - y1) * self.display_size[1] // self.rgb888p_size[1]
#                    pl.osd_img.draw_rectangle(x,y, w, h, color=self.get_color(int(det[5])),thickness=4)
#                    pl.osd_img.draw_string_advanced( x , y-50,32," " + self.labels[int(det[5])] + " " + str(round(det[4],2)) , color=self.get_color(int(det[5])))
#            else:
#                pl.osd_img.clear()


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


    # ⭐ 修复：修改此函数以提高健壮性
    def draw_result(self,pl,dets):
        with ScopedTiming("display_draw",self.debug_mode >0):
            pl.osd_img.clear()
            # 始终显示状态文本，提供更好的用户体验
            pl.osd_img.draw_string_advanced(10, 10, 24, "目标检测中...(按4退出)", color=(255, 255, 0, 0))

            # ⭐ 使用 len() 代替 .size，使其能同时处理 list 和 numpy array
            # 并添加 dets is not None 的检查，增加代码健壮性。
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
# 模块入口函数 (与上一版相同)
# ==============================================================================
def run_object_detection(pl, pipeline_input_size, uart_obj=None):
    kmodel_path = "/sdcard/examples/my_kmodel/object_detect_yolov8n/yolov8n_320_best.kmodel"
    labels = ["person", "fall", "hand", "cigarette", "lighter"]
    confidence_threshold, nms_threshold = 0.2, 0.2
    max_boxes_num, model_input_size = 50, [320, 320]
    display_size = [960, 540]

    ob_det = None
    last_sent_status = -1

    try:
        ob_det = ObjectDetectionApp(kmodel_path,labels=labels,model_input_size=model_input_size,
                                    max_boxes_num=max_boxes_num,confidence_threshold=confidence_threshold,
                                    nms_threshold=nms_threshold,rgb888p_size=pipeline_input_size,
                                    display_size=display_size,debug_mode=0)
        ob_det.config_preprocess(input_image_size=pipeline_input_size)

        while True:
            if scan_key() == "7":
                print("【键4】被按下，退出目标检测程序...")
                break

            img = pl.get_frame()
            res = ob_det.run(img)
            ob_det.draw_result(pl, res)
            pl.show_image()

            current_status = STATUS_OD_IDLE
            # ⭐ 同样使用len()来检查res，保持一致性
            if res is not None and len(res) > 0:
                has_fall, has_person, has_hand, has_smoke_item = False, False, False, False
                for det in res:
                    class_name = labels[int(det[5])]
                    if class_name == 'fall': has_fall = True
                    elif class_name == 'person': has_person = True
                    elif class_name == 'hand': has_hand = True
                    elif class_name in ['cigarette', 'lighter']: has_smoke_item = True

                if has_fall: current_status = STATUS_FALL_DETECTED
                elif has_hand and has_smoke_item: current_status = STATUS_SMOKING_DETECTED
                elif has_person: current_status = STATUS_PERSON_DETECTED

            if current_status != last_sent_status:
                _send_ai_status_packet(uart_obj, current_status)
                last_sent_status = current_status

            gc.collect()

    except Exception as e:
        sys.print_exception(e)
    finally:
        print("--- 开始执行清理程序 ---")
        if ob_det is not None:
            ob_det.deinit()
            del ob_det
        _send_ai_status_packet(uart_obj, STATUS_OD_IDLE)
        print("--- 目标检测模块清理完成 ---")
