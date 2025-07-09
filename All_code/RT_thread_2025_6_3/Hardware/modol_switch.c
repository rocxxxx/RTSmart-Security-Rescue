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
u8 count1=0,count2=0; //按键模式 
u8 basis=30;  //基准速度 extern
u8 basis_temp1;
u8 basis_temp2;
uint16_t distance;
u8 mode;  //模式  extern
// 第一位data1 为Car_mode   运行模式指令
// 第二位data2 为Car_stop   从车停止指令
// 第三位data3 为Car_quan   内外圈指令
u8 Car_mode=0; // 主车发给从车 运行模式指令 01 02 03 04
u8 Car_stop; // 主车发给从车停止指令  0x1B 当从车接收到0x1B后  从车立刻停止
u8 Car_quan=1; // 主车发给从车 内外圈指令
u8 count_Mv_IsRoad_2 = 0;
u8 mode3_chalu;  //岔路内圈标志位
//extern 
//
void key_switch()
{
	keyNum=Key_GetNum();
	
     if (keyNum == 0)
        {
        }
        else if (keyNum == 1) // 设置速度 分为  0.3m/s   0.5m/s   1.0m/s
        {
            count1++; // 计数变量++/
            if (count1 == 1)
            {
                basis_temp1 = 30; // 0.3m/s  基础速度为30  0.3m/s
            }
            else if (count1 == 2)
            {
                basis_temp1 = 50; // 0.5m/s  速度为50      0.5m/s
            }
            else if (count1 == 3)
            {
                basis_temp1 = 80; // 1.0m/s  速度为100    1m/s
            }
            else if (count1 >3 ) 
            {
				count1 = 0;
                basis_temp1 = 30; // 否则 速度为30
            }
        }
        else if (keyNum == 2) // 设置模式  分为五个模式
        {
            count2++; // 计数变量++
			if(count2>4)
				count2=0;
        }
        else if (keyNum == 3) // 确定按钮
        {
            mode = count2;          // 选择模式 模式确定
            basis = basis_temp1; // 选择速度 速度确定
            set_motor_enable();
        }
	}
	
	
	
void modol_init()
{
    // 主车逻辑部分
        if (mode == 0)
        {
            Car_mode = 0; // 主车模式0 发送给从车也是模式0  通过蓝牙进行发送
       //     mv_mode = 0;  // 告诉mv 这是模式0 通过串口进行发送

            // Mv_ISRoad = 0;       // 小车初始停止位判断为0
            // Mv_Line = 4;         // 小车初始 巡线偏差为 4  放正后巡线偏差为4

            set_motor_disable(); // 小车没按下按键时 小车电机失能
         //   LED_GREEN = 0;
        }
        else if (mode == 1) // 模式1   题目1
        {

            Car_mode = 1; // 主车模式1 发送给从车也是模式1  通过蓝牙进行发送
			basis = 30; // 速度大概为0.3m/s        //200 0.3m/s   240  240  330  0.5m/s   460 8s   560 7s

		
			
			
            if (count_Mv_IsRoad >= 2) // 到达停止线 过13次   0.3m/s的速度
            {
                Car_stop = 0x1B;
   
                set_motor_disable(); // 跑了一圈
				TIM_Cmd(TIM1,DISABLE);
				//SYN_FrameInfo(2,"[v7][m1][t5]车辆停止");
            }
        }
        else if (mode == 2) // 模式2  题目2
        {
            // 给mv和从车发送信息
			Car_mode = 2; // 主车模式2 发送给从车也是模式2  通过蓝牙进行发送  
            // 模式2  速度不低于0.5m/s
            // 从车放在E点所示区域   两辆车跟随
            // 从车快速追上主车     跟随距离要求20cm
            // 沿外圈行驶两圈停止
            // 停止时 与主车的间距为20cm  误差不大于6cm
 			basis = 46;
            // delay_ms(3000);
            // pid_speed1.target_val = 330; // 速度大概为0.5m/s  330
            // pid_speed2.target_val = 330;

            if (count_Mv_IsRoad>= 4) // 到达停止线  0.5m/s的速度  两圈停车为4
            {
                //flag = 1;
                Car_stop = 0x1B;

                set_motor_disable(); // 跑了一圈
            }

			
        }
        else if (mode == 3) // 模式3   题目3
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
	     			// 模式3    两辆车跟随   跟随距离要求20cm   速度不低于0.3m/s  完成三圈  停止时 与主车的间距为20cm  误差不大于6cm      }
       
		else if (mode == 4) // 模式4
        {
            
			p=3.5,i=1.6,d=0.7;
			p2=3.5,i2=1.6,d2=0.7;
			// 给mv和从车发送信息
            Car_mode = 4; // 主车模式1 发送给从车也是模式1  通过蓝牙进行发送  		
			basis = 50;
			if (count_Mv_IsRoad >=1&&count_Mv_IsRoad_2==0 ) // 到达停止线 过9次  1m/s的速度  
            {
				
                Car_stop = 0x1B;
				HC_SendData();
				Delay_ms(30);	//50  
         //       count_Mv_IsRoad = 0;  //测试
                set_motor_disable(); // 跑了半圈到停止点
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
				set_motor_disable();//跑一圈停止；
				HC_SendData();	
			//	Car_stop = 0;				

			}
//			
		}

}

