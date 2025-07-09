#include "stm32f10x.h"  // STM32 外设库头文件
#include "OLED.h"
#include "PID.h"


/**************openmv相关参量***************/
int16_t  start_state,circle_count,symbol,work_star, ERR = 0;
int8_t  openmv_buf[7];      // 存储一帧完整的 OpenMV 数据
int      buf_pos = 0;        // 当前接收位置
/**************openmv相关参量***************/

/**************蓝牙相关参量***************/
uint8_t hc_buf[4];    // 缓存接收数据（帧长固定：帧头2 + 数据1 + 尾1 = 4）
uint8_t hc_buf_pos = 0;
uint8_t site = 0;     // 从串口3接收到的数据字段
/**************蓝牙相关参量***************/


/**
 * @brief  解析并提取 OpenMV 传输的数据
 * @note   [0x2C, 0x42, err, start_state, circle_count,char, 0x5B]
 */
void Process_OpenMV_Frame(void)
{
	// 偏差值（8 位中直接是带符号值或用户协议范围内）
    ERR = openmv_buf[2];
    // 起始线
    start_state = openmv_buf[3];
	//圆形计次
	circle_count = openmv_buf[4];
	//误差符号
	symbol = openmv_buf[5];
	work_star = openmv_buf[6];
	
	if(symbol == 0x01)			//车右偏为负，左偏为正
	{
		ERR = -ERR;
	}
	else if(symbol == 0x03)
	{
		ERR = ERR;
	}
	
    
    // 清零缓存准备下一帧
    buf_pos = 0;
}

/**
 * @brief  串口接收回调，逐字节接收并解析 OpenMV 发送的协议数据
 * @param  data 接收到的一个字节数据
 * @note   帧格式: [0]=0x2C, [1]=0x42, [2]=0xA5,
 *                     [3]=保留(0), [4]=标记序号, [5]=保留(0),
 *                     [6]=偏差值(int8), [7]=0x5B
 */
void Openmv_Receive_Data(uint8_t data)
{
    switch (buf_pos) {
        case 0:
            if (data == 0x2C) { openmv_buf[buf_pos++] = data; }
            break;
        case 1:
            if (data == 0x42) { openmv_buf[buf_pos++] = data; }
            else { buf_pos = 0; }
            break;
        case 2:
            openmv_buf[buf_pos++] = data;  //ERR
            break;
        case 3:
            openmv_buf[buf_pos++] = data;  // start_state
            break;
        case 4:
            openmv_buf[buf_pos++] = data;  // circle_count
            break;
        case 5:
            openmv_buf[buf_pos++] = data;  // symbol
            break;
        case 6:
            if (data == 0x5B) {
                openmv_buf[buf_pos] = data;
                // 完整一帧接收完成，解析数据
                Process_OpenMV_Frame();
            }
            // 无论是否正确帧尾，都重置开始下一帧
            buf_pos = 0;
            break;
        default:
            buf_pos = 0;
            break;
    }
}


/**************蓝牙相关参量***************/
void Process_HC_Frame(void)
{
    site = hc_buf[2];  // 提取 site 值
}

void HC_Receive_Data(uint8_t data)
{
    switch (hc_buf_pos)
    {
        case 0:
            if (data == 0x2C)
            {
                hc_buf[hc_buf_pos++] = data;
            }
            break;
        case 1:
            if (data == 0x43)
            {
                hc_buf[hc_buf_pos++] = data;
            }
            else
            {
                hc_buf_pos = 0;  // 帧头错误，重置
            }
            break;
        case 2:
            hc_buf[hc_buf_pos++] = data;  // site 值
            break;
        case 3:
            if (data == 0x5B)
            {
                hc_buf[hc_buf_pos] = data; // 保存帧尾
                // 完整接收一帧，处理数据
                Process_HC_Frame();
            }
            hc_buf_pos = 0;  // 成功或失败都重置
            break;
        default:
            hc_buf_pos = 0;
            break;
    }
}
/**************蓝牙相关参量***************/

