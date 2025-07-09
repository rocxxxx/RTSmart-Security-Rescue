import time
import os
from media.media import *   # 导入 media 模块，用于初始化 vb buffer
from media.pyaudio import * # 导入 pyaudio 模块，用于采集和播放音频
import media.wave as wave   # 导入 wav 模块，用于保存和加载 wav 音频文件
import sys

sys.path.append("/sdcard/examples/02-Media")
from audio import play_audio  # 从 audio.py 中导入播放函数

# 网格参数
GRID_ROWS = 3
GRID_COLS = 3
CELL_WIDTH = 320
CELL_HEIGHT = 180
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 540

# 判断触摸位置是否在指定网格单元格
def get_grid_index(tx, ty):
    col = tx // CELL_WIDTH
    row = ty // CELL_HEIGHT
    if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
        index = row * GRID_COLS + col + 1  # 返回 1~9
        if index <= 6:  # 只允许 1~6
            return index
    return None

# 判断是否触摸了退出按钮区域
def is_exit_area(tx, ty):
    return tx >= 860 and ty >= 440  # 右下角区域

# 绘制数字网格界面和退出按钮
def draw_play_grid(pl):
    pl.osd_img.clear()

    # 绘制数字（1~6，居中显示）
    font_size = 30
    text_color = (100, 100, 255, 255)
    for i in range(GRID_ROWS):
        for j in range(GRID_COLS):
            num = i * GRID_COLS + j + 1
            if num > 6:
                continue  # 跳过 7~9
            x = j * CELL_WIDTH + (CELL_WIDTH - font_size) // 2
            y = i * CELL_HEIGHT + (CELL_HEIGHT - font_size) // 2
            pl.osd_img.draw_string_advanced(x, y, font_size, str(num), color=text_color)

    # 绘制 exit 按钮
    pl.osd_img.draw_string_advanced(870, 446, 30, "exit", color=(255, 0, 0, 255))

    pl.show_image()

# 主播放界面循环
def run_audio_play(pl, tp):
    print(">>> 播放模块启动")
    draw_play_grid(pl)

    last_touching = False  # 防止连续触发

    while True:
        points = tp.read()
        touching = points and len(points) > 0

        if touching and not last_touching:
            p = points[0]
            tx, ty = 960 - p.x, 536 - p.y
            print(f"[播放界面] 触摸坐标: ({tx}, {ty})")

            if is_exit_area(tx, ty):
                print(">>> 退出播放界面")
                break

            grid_index = get_grid_index(tx, ty)
            if grid_index:
                audio_path = f"/sdcard/app/留言{grid_index}.wav"
                print(f">>> 播放音频：{audio_path}")

                try:
                    # 停止摄像头采集显示
                    pl.sensor.stop()

                    # 清屏防止残留画面
                    pl.osd_img.clear()
                    pl.show_image()

                    # 播放音频
                    play_audio(audio_path)

                except Exception as e:
                    print(f"播放失败: {e}")

                finally:
                    # 先重置再启动摄像头采集显示，避免reset错误
                    pl.sensor.reset()
                    pl.sensor.run()

                    # 重新绘制数字网格界面
                    draw_play_grid(pl)

        last_touching = touching
        time.sleep(0.05)
