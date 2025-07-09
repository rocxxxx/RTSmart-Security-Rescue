#include "stm32f10x.h"                  // Device header
#include "Delay.h"
#include "OLED.h"
#include "Timer.h"
#include "Motor.h"
#include "Serial.h"
#include "agree.h"
#include "PID.h"
#include "PWM.h"
#include "Key.h"
#include "HC_serial.h"
#include "BMencoder.h"

int16_t speed1, speed2;
int16_t real_speed1, real_speed2;
int8_t mv_RxData,hc_RxData;                  // 串口接收的单字节数据
uint8_t time_i=0;				//定时器计次


/******蓝牙相关量******/
extern uint8_t site;
/******蓝牙相关量******/

/******openmv相关量******/
extern int16_t start_state;
extern int16_t circle_count;
extern int16_t symbol;
extern int16_t work_star;
extern int16_t ERR;
/******openmv相关量******/

/******标志位******/
uint8_t circle_flag = 0;
/******标志位******/



int main()
{
	OLED_Init();             // 初始化 OLED 屏幕
	Motor_Init();            // 初始化电机 PWM 输出
	Encoder_Init();          // 初始化电机编码器输入
	Timer_1_Init();            // 初始化定时器（用于定时 PID 控制）

	//Key_Init();              // 初始化按键
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);  // 设置中断优先级分组
	Uart1_Serial_Init();           // 初始化串口 USART1（用于接收 OpenMV 数据）
	HC_Init();               // 初始化蓝牙串口（HC-05/06 等模块）
	
	
	//Delay_ms(3000);
	//site = 2;//模拟传入的地点
	OLED_ShowString(1, 1, "ERR:");
	OLED_ShowString(2, 1, "v1:");
	OLED_ShowString(2, 9, "v2:");
	OLED_ShowString(3, 1, "cir:");
	OLED_ShowString(3, 9, "site:");
	OLED_ShowString(4, 1, "stop:");
	
	//right(-50);
	//left(-50);
	
	while(1) 
	{
		OLED_ShowSignedNum(1, 5, ERR, 3);
		OLED_ShowSignedNum(2, 4, Encoder_1_Get(), 2);
		OLED_ShowSignedNum(2, 12, Encoder_2_Get(), 2);
		OLED_ShowSignedNum(3, 5, circle_count, 2);
		OLED_ShowSignedNum(4, 6, start_state, 2);
		if(site != 0&& work_star == 0x5B)
		{
			left(speed1);          // 设置左电机 PWM
			right(speed2);         // 设置右电机 PWM
		
		}
		if(start_state >=1)
		{
			set_motor_disable();
		
		}
		if(circle_count == site && circle_flag == 0)
		{
			OLED_ShowSignedNum(3, 5, circle_count, 2);
			circle_flag = 1;
			set_motor_disable();
			Delay_s(2);
			set_motor_enable();
		
		}
		
				

	}
}


void TIM1_UP_IRQHandler(void)
{
	if (TIM_GetITStatus(TIM1, TIM_IT_Update) == SET)
	{
		if(time_i == 10)//0.1s进一次
		{
			real_speed1 = Encoder_1_Get();
			real_speed2 = Encoder_2_Get();
			
			ClosedLoopControl(ERR, 80, real_speed1, real_speed2, &speed1, &speed2);
			time_i = 0;
		}
		else
			time_i++;

		TIM_ClearITPendingBit(TIM1, TIM_IT_Update);  // 清除中断标志
	}
}


void USART1_IRQHandler(void)//用于openmv
{   
	if (USART_GetITStatus(USART1, USART_IT_RXNE) == SET)  // 数据接收中断
	{  
		USART_ClearITPendingBit(USART1, USART_IT_RXNE);     // 清除标志位
		mv_RxData = USART_ReceiveData(USART1);                 // 接收数据
		Openmv_Receive_Data(mv_RxData);                        // 处理 OpenMV 视觉误差数据
	}  
}


void USART3_IRQHandler(void)
{
	if(USART_GetITStatus(USART3 ,USART_IT_RXNE) == SET)
	{
		USART_ClearITPendingBit(USART3,USART_IT_RXNE);
		hc_RxData = USART_ReceiveData(USART3);
		HC_Receive_Data(hc_RxData);
		//Uart3_Serial_SendByte(site);
		OLED_ShowNum(3, 14, site, 2);

		
	}

}

