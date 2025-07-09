# 音频输入和输出示例
#
# 注意：运行此示例需要一个 SD 卡。
#
# 您可以播放WAV文件或捕获音频并保存为 WAV 格式。

import os
from media.media import *
from media.pyaudio import *
import media.wave as wave
import struct

def exit_check():
    try:
        os.exitpoint()
    except KeyboardInterrupt as e:
        print("user stop: ", e)
        return True
    return False

def record_audio(filename, duration):
    CHUNK = 44100//25  #设置音频chunk值
    FORMAT = paInt16       #设置采样精度,支持16bit(paInt16)/24bit(paInt24)/32bit(paInt32)
    CHANNELS = 2           #设置声道数,支持单声道(1)/立体声(2)
    RATE = 44100           #设置采样率

    try:
        p = PyAudio()
        p.initialize(CHUNK)    #初始化PyAudio对象
        MediaManager.init()    #vb buffer初始化

        #创建音频输入流
        stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        stream.volume(LEFT,70)
        stream.volume(RIGHT,85)
        print("volume :",stream.volume())

        #启用音频3A功能：自动噪声抑制(ANS)
        stream.enable_audio3a(AUDIO_3A_ENABLE_ANS)

        frames = []
        #采集音频数据并存入列表
        for i in range(0, int(RATE / CHUNK * duration)):
            data = stream.read()
            frames.append(data)
            if exit_check():
                break
        #将列表中的数据保存到wav文件中
        wf = wave.open(filename, 'wb') #创建wav 文件
        wf.set_channels(CHANNELS) #设置wav 声道数
        wf.set_sampwidth(p.get_sample_size(FORMAT))  #设置wav 采样精度
        wf.set_framerate(RATE)  #设置wav 采样率
        wf.write_frames(b''.join(frames)) #存储wav音频数据
        wf.close() #关闭wav文件
    except BaseException as e:
            print(f"Exception {e}")
    finally:
        stream.stop_stream() #停止采集音频数据
        stream.close()#关闭音频输入流
        p.terminate()#释放音频对象
        MediaManager.deinit() #释放vb buffer

def moving_average_filter(samples, window_size=5):
    filtered = []
    length = len(samples)
    for i in range(length):
        total = 0
        count = 0
        for j in range(i - window_size // 2, i + window_size // 2 + 1):
            if 0 <= j < length:
                total += samples[j]
                count += 1
        filtered.append(total // count)
    return filtered

def play_audio(filename):
    wf = None
    p = None
    stream = None

    try:
        wf = wave.open(filename, 'rb')  # 打开WAV文件

        # CHUNK可以根据需要设置，1024或2048都是不错的选择
        CHUNK = 512 
        p = PyAudio()
        p.initialize(CHUNK)

        stream = p.open(format=p.get_format_from_width(wf.get_sampwidth()),
                       channels=1,
                       rate=wf.get_framerate(),
                       output=True,
                       frames_per_buffer=CHUNK)

        # 设置一个合适的音量
        stream.volume(vol=90)

        print("开始播放 (无实时滤波)...")
        data = wf.read_frames(CHUNK)
        while data:
            # 直接写入，不进行任何计算
            stream.write(data)
            data = wf.read_frames(CHUNK)

    except Exception as e:
        print("[播放异常]", e)

    finally:
        try:
            if stream:
                stream.stop_stream()
                stream.close()
            if p:
                p.terminate()
            if wf:
                wf.close()
        except Exception as e:
            print("[释放资源异常]", e)

def loop_audio(duration):
    CHUNK = 44100//25#设置音频chunck
    FORMAT = paInt16 #设置音频采样精度,支持16bit(paInt16)/24bit(paInt24)/32bit(paInt32)
    CHANNELS = 2 #设置音频声道数，支持单声道(1)/立体声(2)
    RATE = 44100 #设置音频采样率

    try:
        p = PyAudio()
        p.initialize(CHUNK)#初始化PyAudio对象
        MediaManager.init()    #vb buffer初始化

        #创建音频输入流
        input_stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        #设置音频输入流的音量
        input_stream.volume(LEFT,70)
        input_stream.volume(RIGHT,85)
        print("input volume :",input_stream.volume())

        #启用音频3A功能：自动噪声抑制(ANS)
        input_stream.enable_audio3a(AUDIO_3A_ENABLE_ANS)

        #创建音频输出流
        output_stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,frames_per_buffer=CHUNK)

        #设置音频输出流的音量
        output_stream.volume(vol=85)

        #从音频输入流中获取数据写入到音频输出流中
        for i in range(0, int(RATE / CHUNK * duration)):
            output_stream.write(input_stream.read())
            if exit_check():
                break
    except BaseException as e:
            print(f"Exception {e}")
    finally:
        input_stream.stop_stream()#停止音频输入流
        output_stream.stop_stream()#停止音频输出流
        input_stream.close() #关闭音频输入流
        output_stream.close() #关闭音频输出流
        p.terminate() #释放音频对象

        MediaManager.deinit() #释放vb buffer

def audio_recorder(filename, duration):
    CHUNK = 44100//25      #设置音频chunk值
    FORMAT = paInt16       #设置采样精度,支持16bit(paInt16)/24bit(paInt24)/32bit(paInt32)
    CHANNELS = 1           #设置声道数,支持单声道(1)/立体声(2)
    RATE = 44100           #设置采样率

    p = PyAudio()
    p.initialize(CHUNK)    #初始化PyAudio对象
    MediaManager.init()    #vb buffer初始化

    try:
        #创建音频输入流
        input_stream = p.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        input=True,
                        frames_per_buffer=CHUNK)

        input_stream.volume(LEFT,70)
        input_stream.volume(RIGHT,85)
        print("input volume :",input_stream.volume())

        #启用音频3A功能：自动噪声抑制(ANS)
        input_stream.enable_audio3a(AUDIO_3A_ENABLE_ANS)
        print("enable audio 3a:ans")

        print("start record...")
        frames = []
        #采集音频数据并存入列表
        for i in range(0, int(RATE / CHUNK * duration)):
            data = input_stream.read()
            frames.append(data)
            if exit_check():
                break
        print("stop record...")
        #将列表中的数据保存到wav文件中
        wf = wave.open(filename, 'wb') #创建wav 文件
        wf.set_channels(CHANNELS) #设置wav 声道数
        wf.set_sampwidth(p.get_sample_size(FORMAT))  #设置wav 采样精度
        wf.set_framerate(RATE)  #设置wav 采样率
        wf.write_frames(b''.join(frames)) #存储wav音频数据
        wf.close() #关闭wav文件
    except BaseException as e:
            print(f"Exception {e}")
    finally:
        input_stream.stop_stream() #停止采集音频数据
        input_stream.close()#关闭音频输入流

    try:
        wf = wave.open(filename, 'rb')#打开wav文件
        CHUNK = int(wf.get_framerate()/25)#设置音频chunk值

        #创建音频输出流，设置的音频参数均为wave中获取到的参数
        output_stream = p.open(format=p.get_format_from_width(wf.get_sampwidth()),
                    channels=wf.get_channels(),
                    rate=wf.get_framerate(),
                    output=True,frames_per_buffer=CHUNK)

        #设置音频输出流的音量
        output_stream.volume(vol=85)
        print("output volume :",output_stream.volume())

        print("start play...")
        data = wf.read_frames(CHUNK)#从wav文件中读取数一帧数据

        while data:
            output_stream.write(data)  #将帧数据写入到音频输出流中
            data = wf.read_frames(CHUNK) #从wav文件中读取数一帧数据
            if exit_check():
                break
        print("stop play...")
    except BaseException as e:
            print(f"Exception {e}")
    finally:
        output_stream.stop_stream() #停止音频输出流
        output_stream.close()#关闭音频输出流

    p.terminate() #释放音频对象
    MediaManager.deinit() #释放vb buffer

if __name__ == "__main__":
    os.exitpoint(os.EXITPOINT_ENABLE)
    print("音频示例开始")
    # record_audio('/sdcard/examples/test.wav', 15)  # 录制WAV文件
    play_audio('/sdcard/examples/test.wav')  # 播放WAV文件
    # loop_audio(15)  # 采集音频并输出
    #audio_recorder('/sdcard/examples/test.wav', 15) #录制15秒音频并播放
    print("音频示例完成")