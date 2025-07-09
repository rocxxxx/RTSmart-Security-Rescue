#include "stm32f10x.h"  // STM32 �����ͷ�ļ�
#include "OLED.h"
#include "PID.h"


/**************openmv��ز���***************/
int16_t  start_state,circle_count,symbol,work_star, ERR = 0;
int8_t  openmv_buf[7];      // �洢һ֡������ OpenMV ����
int      buf_pos = 0;        // ��ǰ����λ��
/**************openmv��ز���***************/

/**************������ز���***************/
uint8_t hc_buf[4];    // ����������ݣ�֡���̶���֡ͷ2 + ����1 + β1 = 4��
uint8_t hc_buf_pos = 0;
uint8_t site = 0;     // �Ӵ���3���յ��������ֶ�
/**************������ز���***************/


/**
 * @brief  ��������ȡ OpenMV ���������
 * @note   [0x2C, 0x42, err, start_state, circle_count,char, 0x5B]
 */
void Process_OpenMV_Frame(void)
{
	// ƫ��ֵ��8 λ��ֱ���Ǵ�����ֵ���û�Э�鷶Χ�ڣ�
    ERR = openmv_buf[2];
    // ��ʼ��
    start_state = openmv_buf[3];
	//Բ�μƴ�
	circle_count = openmv_buf[4];
	//������
	symbol = openmv_buf[5];
	work_star = openmv_buf[6];
	
	if(symbol == 0x01)			//����ƫΪ������ƫΪ��
	{
		ERR = -ERR;
	}
	else if(symbol == 0x03)
	{
		ERR = ERR;
	}
	
    
    // ���㻺��׼����һ֡
    buf_pos = 0;
}

/**
 * @brief  ���ڽ��ջص������ֽڽ��ղ����� OpenMV ���͵�Э������
 * @param  data ���յ���һ���ֽ�����
 * @note   ֡��ʽ: [0]=0x2C, [1]=0x42, [2]=0xA5,
 *                     [3]=����(0), [4]=������, [5]=����(0),
 *                     [6]=ƫ��ֵ(int8), [7]=0x5B
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
                // ����һ֡������ɣ���������
                Process_OpenMV_Frame();
            }
            // �����Ƿ���ȷ֡β�������ÿ�ʼ��һ֡
            buf_pos = 0;
            break;
        default:
            buf_pos = 0;
            break;
    }
}


/**************������ز���***************/
void Process_HC_Frame(void)
{
    site = hc_buf[2];  // ��ȡ site ֵ
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
                hc_buf_pos = 0;  // ֡ͷ��������
            }
            break;
        case 2:
            hc_buf[hc_buf_pos++] = data;  // site ֵ
            break;
        case 3:
            if (data == 0x5B)
            {
                hc_buf[hc_buf_pos] = data; // ����֡β
                // ��������һ֡����������
                Process_HC_Frame();
            }
            hc_buf_pos = 0;  // �ɹ���ʧ�ܶ�����
            break;
        default:
            hc_buf_pos = 0;
            break;
    }
}
/**************������ز���***************/

