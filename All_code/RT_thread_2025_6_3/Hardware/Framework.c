#include "stm32f10x.h"                  // Device header
#include "Infrared detection.h"
#include "Motor.h"
#include "Delay.h"

uint8_t  Destination()//终点判断
{
	uint8_t EndKey=1;//循环允许标志
	if(detection1()==0&&detection2()==0&&detection3()==0&&detection4()==0&&detection0()==0)
	{
		Motor_SetSpeed1(0);Motor_SetSpeed2(0);EndKey=0;
	}
	return EndKey;
}

	//GPIO_SetBits(GPIOA,GPIO_Pin_0);//高电平
	//GPIO_ResetBits(GPIOA,GPIO_Pin_0);//低电平

