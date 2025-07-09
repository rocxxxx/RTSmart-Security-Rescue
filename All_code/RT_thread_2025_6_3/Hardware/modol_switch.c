#include "stm32f10x.h"                  // Device header
#include "PWM.h"
#include "modol_switch.h"
#include "agree.h"
#include "Key.h"
#include "modol_switch.h"
#include "Delay.h"
#include "PID.h"
#include "HC_serial.h"


u8 keyNum;  
u8 count1=0,count2=0; //����ģʽ 
u8 basis=30;  //��׼�ٶ� extern
u8 basis_temp1;
u8 basis_temp2;
uint16_t distance;
u8 mode;  //ģʽ  extern
// ��һλdata1 ΪCar_mode   ����ģʽָ��
// �ڶ�λdata2 ΪCar_stop   �ӳ�ָֹͣ��
// ����λdata3 ΪCar_quan   ����Ȧָ��
u8 Car_mode=0; // ���������ӳ� ����ģʽָ�� 01 02 03 04
u8 Car_stop; // ���������ӳ�ָֹͣ��  0x1B ���ӳ����յ�0x1B��  �ӳ�����ֹͣ
u8 Car_quan=1; // ���������ӳ� ����Ȧָ��
u8 count_Mv_IsRoad_2 = 0;
u8 mode3_chalu;  //��·��Ȧ��־λ
//extern 
//
void key_switch()
{
	keyNum=Key_GetNum();
	
     if (keyNum == 0)
        {
        }
        else if (keyNum == 1) // �����ٶ� ��Ϊ  0.3m/s   0.5m/s   1.0m/s
        {
            count1++; // ��������++/
            if (count1 == 1)
            {
                basis_temp1 = 30; // 0.3m/s  �����ٶ�Ϊ30  0.3m/s
            }
            else if (count1 == 2)
            {
                basis_temp1 = 50; // 0.5m/s  �ٶ�Ϊ50      0.5m/s
            }
            else if (count1 == 3)
            {
                basis_temp1 = 80; // 1.0m/s  �ٶ�Ϊ100    1m/s
            }
            else if (count1 >3 ) 
            {
				count1 = 0;
                basis_temp1 = 30; // ���� �ٶ�Ϊ30
            }
        }
        else if (keyNum == 2) // ����ģʽ  ��Ϊ���ģʽ
        {
            count2++; // ��������++
			if(count2>4)
				count2=0;
        }
        else if (keyNum == 3) // ȷ����ť
        {
            mode = count2;          // ѡ��ģʽ ģʽȷ��
            basis = basis_temp1; // ѡ���ٶ� �ٶ�ȷ��
            set_motor_enable();
        }
	}
	
	
	
void modol_init()
{
    // �����߼�����
        if (mode == 0)
        {
            Car_mode = 0; // ����ģʽ0 ���͸��ӳ�Ҳ��ģʽ0  ͨ���������з���
       //     mv_mode = 0;  // ����mv ����ģʽ0 ͨ�����ڽ��з���

            // Mv_ISRoad = 0;       // С����ʼֹͣλ�ж�Ϊ0
            // Mv_Line = 4;         // С����ʼ Ѳ��ƫ��Ϊ 4  ������Ѳ��ƫ��Ϊ4

            set_motor_disable(); // С��û���°���ʱ С�����ʧ��
         //   LED_GREEN = 0;
        }
        else if (mode == 1) // ģʽ1   ��Ŀ1
        {

            Car_mode = 1; // ����ģʽ1 ���͸��ӳ�Ҳ��ģʽ1  ͨ���������з���
			basis = 30; // �ٶȴ��Ϊ0.3m/s        //200 0.3m/s   240  240  330  0.5m/s   460 8s   560 7s

		
			
			
            if (count_Mv_IsRoad >= 2) // ����ֹͣ�� ��13��   0.3m/s���ٶ�
            {
                Car_stop = 0x1B;
   
                set_motor_disable(); // ����һȦ
				TIM_Cmd(TIM1,DISABLE);
				//SYN_FrameInfo(2,"[v7][m1][t5]����ֹͣ");
            }
        }
        else if (mode == 2) // ģʽ2  ��Ŀ2
        {
            // ��mv�ʹӳ�������Ϣ
			Car_mode = 2; // ����ģʽ2 ���͸��ӳ�Ҳ��ģʽ2  ͨ���������з���  
            // ģʽ2  �ٶȲ�����0.5m/s
            // �ӳ�����E����ʾ����   ����������
            // �ӳ�����׷������     �������Ҫ��20cm
            // ����Ȧ��ʻ��Ȧֹͣ
            // ֹͣʱ �������ļ��Ϊ20cm  ������6cm
 			basis = 46;
            // delay_ms(3000);
            // pid_speed1.target_val = 330; // �ٶȴ��Ϊ0.5m/s  330
            // pid_speed2.target_val = 330;

            if (count_Mv_IsRoad>= 4) // ����ֹͣ��  0.5m/s���ٶ�  ��Ȧͣ��Ϊ4
            {
                //flag = 1;
                Car_stop = 0x1B;

                set_motor_disable(); // ����һȦ
            }

			
        }
        else if (mode == 3) // ģʽ3   ��Ŀ3
        {
			Car_mode = 3;
			basis = 30;	
           if(count_Mv_IsRoad>=2&&count_Mv_IsRoad<=4)

       {
	      basis = 25;
}
			else if(count_Mv_IsRoad>4&&count_Mv_IsRoad<8)

{
	     basis = 33;
}

			else if(count_Mv_IsRoad>=9)
			  {
				Car_stop = 0x1B;				
			    set_motor_disable(); 
			  }

		    }
	     			// ģʽ3    ����������   �������Ҫ��20cm   �ٶȲ�����0.3m/s  �����Ȧ  ֹͣʱ �������ļ��Ϊ20cm  ������6cm      }
       
		else if (mode == 4) // ģʽ4
        {
            
			p=3.5,i=1.6,d=0.7;
			p2=3.5,i2=1.6,d2=0.7;
			// ��mv�ʹӳ�������Ϣ
            Car_mode = 4; // ����ģʽ1 ���͸��ӳ�Ҳ��ģʽ1  ͨ���������з���  		
			basis = 50;
			if (count_Mv_IsRoad >=1&&count_Mv_IsRoad_2==0 ) // ����ֹͣ�� ��9��  1m/s���ٶ�  
            {
				
                Car_stop = 0x1B;
				HC_SendData();
				Delay_ms(30);	//50  
         //       count_Mv_IsRoad = 0;  //����
                set_motor_disable(); // ���˰�Ȧ��ֹͣ��
				Delay_ms(1000);
				Delay_ms(1000);
				Delay_ms(1000);
				Delay_ms(1000);
				Delay_ms(1000);
				set_motor_enable();	
				count_Mv_IsRoad_2=count_Mv_IsRoad;
				Car_stop = 0;
				Delay_ms(150);		

            }
			else if(count_Mv_IsRoad > count_Mv_IsRoad_2 +1)
			{	
				
				Car_stop = 0x1B;
				set_motor_disable();//��һȦֹͣ��
				HC_SendData();	
			//	Car_stop = 0;				

			}
//			
		}

}

