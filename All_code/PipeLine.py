import os
import ujson
from media.sensor import *
from media.display import *
from media.media import *
from libs.Utils import ScopedTiming
import nncase_runtime as nn
import ulab.numpy as np
import image
import gc
import sys
import time

def ALIGN_UP(x, align):
    """ 将数值向上对齐到指定倍数 """
    return (x + align - 1) & ~(align - 1)

def ALIGN_DOWN(x, align):
    """ 将数值向下对齐到指定倍数 """
    return x & ~(align - 1)

# PipeLine类
class PipeLine:
    def __init__(self,rgb888p_size=[224,224],display_mode="hdmi",display_size=None,osd_layer_num=1,debug_mode=0):
        # sensor给AI的图像分辨率
        self.rgb888p_size=[ALIGN_UP(rgb888p_size[0],16),rgb888p_size[1]]
        # 视频输出VO图像分辨率
        if display_size is None:
            self.display_size=None
        else:
            self.display_size=[display_size[0],display_size[1]]
        # 视频显示模式，支持："lcd"(default st7701 800*480)，"hdmi"(default lt9611)，"lt9611"，"st7701"，"hx8399"
        self.display_mode=display_mode
        # sensor对象
        self.sensor=None
        # osd显示Image对象
        self.osd_img=None
        self.cur_frame=None
        self.debug_mode=debug_mode
        self.osd_layer_num = osd_layer_num

    # PipeLine初始化函数
    def create(self,sensor=None,hmirror=None,vflip=None,fps=30):
        with ScopedTiming("init PipeLine",self.debug_mode > 0):
            nn.shrink_memory_pool()
            # 初始化并配置sensor
            brd=os.uname()[-1]
            if brd=="k230d_canmv_bpi_zero":
                self.sensor = Sensor(fps=30) if sensor is None else sensor
            elif brd=="k230_canmv_lckfb":
                self.sensor = Sensor(fps=30) if sensor is None else sensor
            elif brd=="k230d_canmv_atk_dnk230d":
                self.sensor = Sensor(fps=30) if sensor is None else sensor
            else:
                self.sensor = Sensor(fps=fps) if sensor is None else sensor
            self.sensor.reset()
            if hmirror is not None and (hmirror==True or hmirror==False):
                self.sensor.set_hmirror(hmirror)
            if vflip is not None and (vflip==True or vflip==False):
                self.sensor.set_vflip(vflip)

            # 初始化显示
            if self.display_mode=="hdmi":
                # 设置为LT9611显示，默认1920x1080
                if self.display_size==None:
                    Display.init(Display.LT9611,osd_num=self.osd_layer_num, to_ide = True)
                else:
                    Display.init(Display.LT9611, width=self.display_size[0], height=self.display_size[1],osd_num=self.osd_layer_num, to_ide = True)
            elif self.display_mode=="lcd":
                # 默认设置为NT35516显示
                if self.display_size==None:
                    Display.init(Display.NT35516, osd_num=self.osd_layer_num, to_ide=True, flag=Display.FLAG_ROTATION_270)
                else:
                    Display.init(Display.NT35516, width=self.display_size[0], height=self.display_size[1], osd_num=self.osd_layer_num, to_ide=True, flag=Display.FLAG_ROTATION_270)
            elif self.display_mode=="nt35516":
                # nt35516
                if self.display_size==None:
                    Display.init(Display.NT35516, osd_num=self.osd_layer_num, to_ide=True)
                else:
                    Display.init(Display.NT35516, width=self.display_size[0], height=self.display_size[1], osd_num=self.osd_layer_num, to_ide=True)
            elif self.display_mode=="lt9611":
                # 设置为LT9611显示，默认1920x1080
                if self.display_size==None:
                    Display.init(Display.LT9611,osd_num=self.osd_layer_num, to_ide = True)
                else:
                    Display.init(Display.LT9611, width=self.display_size[0], height=self.display_size[1],osd_num=self.osd_layer_num, to_ide = True)
            elif self.display_mode=="st7701":
                # 设置为ST7701显示，480x800
                if self.display_size==None:
                    Display.init(Display.ST7701, osd_num=self.osd_layer_num, to_ide=True)
                else:
                    Display.init(Display.ST7701, width=self.display_size[0], height=self.display_size[1], osd_num=self.osd_layer_num, to_ide=True)
            elif self.display_mode=="hx8399":
                # 设置为HX8399显示
                if self.display_size==None:
                    Display.init(Display.HX8399, osd_num=self.osd_layer_num, to_ide=True)
                else:
                    Display.init(Display.HX8399, width=self.display_size[0], height=self.display_size[1], osd_num=self.osd_layer_num, to_ide=True)
            else:
                # 设置为LT9611显示，默认1920x1080
                Display.init(Display.LT9611,osd_num=self.osd_layer_num, to_ide = True)
            
            # 获取真实的显示分辨率
            self.display_size=[Display.width(),Display.height()]
            
            # ======================= [关键修复] =======================
            # 硬件要求视频(YUV)输入层的宽度必须是8像素的倍数。
            # 在这里将从驱动获取的实际宽度向下对齐到最接近的8的倍数。
            self.display_size[1] = ALIGN_DOWN(self.display_size[1], 8)
            self.display_size[0] = ALIGN_DOWN(self.display_size[0], 8)            
            # ==========================================================
            
            # 通道0直接给到显示VO，格式为YUV420
            # 使用对齐后的宽度来设置sensor输出
            self.sensor.set_framesize(w = self.display_size[0], h = self.display_size[1])
            self.sensor.set_pixformat(PIXEL_FORMAT_YUV_SEMIPLANAR_420)
            
            # 通道2给到AI做算法处理，格式为RGB888
            self.sensor.set_framesize(w = self.rgb888p_size[0], h = self.rgb888p_size[1], chn=CAM_CHN_ID_2)
            self.sensor.set_pixformat(PIXEL_FORMAT_RGB_888_PLANAR, chn=CAM_CHN_ID_2)

            self.osd_img = image.Image(self.display_size[0], self.display_size[1], image.ARGB8888)

            sensor_bind_info = self.sensor.bind_info(x = 0, y = 0, chn = CAM_CHN_ID_0)
            Display.bind_layer(**sensor_bind_info, layer = Display.LAYER_VIDEO1)

            # media初始化
            MediaManager.init()
            # 启动sensor
            self.sensor.run()

    # 获取一帧图像数据，返回格式为ulab的array数据
    def get_frame(self):
        with ScopedTiming("get a frame",self.debug_mode > 0):
            self.cur_frame = self.sensor.snapshot(chn=CAM_CHN_ID_2)
            input_np=self.cur_frame.to_numpy_ref()
            return input_np

    # 在屏幕上显示osd_img
    def show_image(self):
        with ScopedTiming("show result",self.debug_mode > 0):
            Display.show_image(self.osd_img, 0, 0, Display.LAYER_OSD0)

    def get_display_size(self):
        return self.display_size

    # PipeLine销毁函数
    def destroy(self):
        with ScopedTiming("deinit PipeLine",self.debug_mode > 0):
            os.exitpoint(os.EXITPOINT_ENABLE_SLEEP)
            # stop sensor
            self.sensor.stop()
            # deinit lcd
            Display.deinit()
            time.sleep_ms(50)
            # deinit media buffer
            MediaManager.deinit()
