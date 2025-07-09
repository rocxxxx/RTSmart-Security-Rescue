#include "stm32f10x.h"
#include "Delay.h"
#include "Motor.h"
#include "math.h"
#include "Timer.h"

//extern int8_t speed1,speed2;
//extern uint16_t Num;//左轮子速度
//extern uint16_t Num1;//右轮子速度
//extern uint8_t WayKey;

void id_init()
{
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
	
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_2;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_1;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_12;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_13;
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_14;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOB,&GPIO_InitStructure);
}
//
uint8_t detection0()
{
	return GPIO_ReadInputDataBit(GPIOB,GPIO_Pin_12);//返回0表示低电平，即有黑线10
}
uint8_t detection1()
{
	return GPIO_ReadInputDataBit(GPIOB,GPIO_Pin_13);//返回1表示高电平，无黑线11
}
uint8_t detection3()
{
	return GPIO_ReadInputDataBit(GPIOB,GPIO_Pin_1);
}
uint8_t detection4()
{
	return GPIO_ReadInputDataBit(GPIOB,GPIO_Pin_2);
}


int8_t Rate_Adjust(int8_t speed1,int8_t speed2)
{
//	int i=0;
//	Motor_SetSpeed2(speed2+7);
//	Motor_SetSpeed1(speed1);
//	while(fabs(Num1-Num-1)>2&&i<6)//实测速度差值大于一，循环校正
//	{
//		i++;
//		if(Num>Num1)//左大于右，左减的多
//		{
//			speed1=speed1-1;
//			Motor_SetSpeed2(speed2);
//			Motor_SetSpeed1(speed1);
//		}
//		if(Num<Num1)//左小于右，右加的少
//		{
//			speed1=speed1+1;
//			Motor_SetSpeed2(speed2);
//			Motor_SetSpeed1(speed1);
//		}
//		
//	}
//	return speed1;
}

//第二种	
void Tracking()//有线是0，无为1
{

//	int Speed;
//	//直行
//	if(detection1()==0&&detection0()==1&&detection3()==0&&detection4()==1)//00_00
//	{	
//		Speed= 50;
//		speed1=Rate_Adjust(Speed,Speed);//校正直线速度
//		//Motor_SetSpeed2(30);
//		//Motor_SetSpeed1(31);
//		
//	}
//	//左小转
//	if(detection1()==1&&detection0()==1&&detection3()==0&&detection4()==1)//01_00
//	{
//	    //Motor_SetSpeed2(50);
//		//Motor_SetSpeed1(-50);
//		//Delay_ms(30);
//		Motor_SetSpeed2(45);
//	    Motor_SetSpeed1(38);
		
//	}
//	//右小转
//	if(detection1()==0&&detection0()==1&&detection3()==1&&detection4()==1)//00_10
//	{
//		//Motor_SetSpeed1(51);
//		//Motor_SetSpeed2(-50);
//		//Delay_ms(30);
//		Motor_SetSpeed2(38);
//	    Motor_SetSpeed1(45);
//	}
//	//左转
//	if(detection1()==1&&detection0()==1&&detection3()==0&&detection4()==0)//11_00
//	{
//		
//	    Motor_SetSpeed2(30);
//	    Motor_SetSpeed1(-41);
//	}
//	//右转
//	if(detection1()==0&&detection0()==0&&detection3()==1&&detection4()==1)//00_11
//	{
//	
//		Motor_SetSpeed1(30);
//        Motor_SetSpeed2(-40);
//	}
//		//左大转
//	if(detection1()==1&&detection0()==1&&detection3()==1&&detection4()==0)//10_00
//	{
//		
//	    Motor_SetSpeed2(90);
//	    Motor_SetSpeed1(-81);
//		Delay_ms(60);
//		
//	}
//	//右大转
//	if(detection1()==1&&detection0()==0&&detection3()==1&&detection4()==1)//00_01
//	{
//		
//		Motor_SetSpeed1(90);
//        Motor_SetSpeed2(-81);
//		Delay_ms(60);
//	}
//	//全0过渡
//	if(detection1()==1&&detection0()==1&&detection3()==1&&detection4()==1)//00_00
//	{
//		
//		Motor_SetSpeed1(40);
//        Motor_SetSpeed2(40);
//	}
//	//终点判断
//		if(detection1()==0&&detection3()==0&&detection4()==0&&detection0()==0)
//	{	
//		//Motor_SetSpeed2(0);
//		//Motor_SetSpeed1(0);
//		//Motor_SetSpeed2(41);
//		//Motor_SetSpeed1(40);
//		//Delay_ms(600);
//		//Delay_ms(100);
//		Motor_SetSpeed2(0);
//		Motor_SetSpeed1(0);
//		WayKey=0;
//		Motor_SetSpeed2(41);
//		Motor_SetSpeed1(40);
//		Delay_ms(600);
//		Motor_SetSpeed2(0);
//		Motor_SetSpeed1(0);
//		TIM_Cmd(TIM4, DISABLE);
//		
//	}
//		if(detection1()==1&&detection3()==0&&detection4()==0&&detection0()==0)
//	{	//Motor_SetSpeed2(0);
//		//Motor_SetSpeed1(0);
//		//Motor_SetSpeed2(41);
//		//Motor_SetSpeed1(40);
//		//Delay_ms(600);
//		//Delay_ms(100);
//		Motor_SetSpeed2(0);
//		Motor_SetSpeed1(0);
//		WayKey=0;
//		Motor_SetSpeed2(41);
//		Motor_SetSpeed1(40);
//		Delay_ms(600);
//		Motor_SetSpeed2(0);
//		Motor_SetSpeed1(0);
//		TIM_Cmd(TIM4, DISABLE);
//		
//	}
//	if(detection1()==0&&detection3()==1&&detection4()==0&&detection0()==0)
//	{	//Motor_SetSpeed2(0);
//		//Motor_SetSpeed1(0);
//		//Motor_SetSpeed2(41);
//		//Motor_SetSpeed1(40);
//		//Delay_ms(600);
//		//Delay_ms(100);
//		Motor_SetSpeed2(0);
//		Motor_SetSpeed1(0);
//		WayKey=0;
//		Motor_SetSpeed2(41);
//		Motor_SetSpeed1(40);
//		Delay_ms(600);
//		Motor_SetSpeed2(0);
//		Motor_SetSpeed1(0);
//		TIM_Cmd(TIM4, DISABLE);
//		
//	}
//	if(detection1()==0&&detection3()==0&&detection4()==1&&detection0()==0)
//	{	//Motor_SetSpeed2(0);
//		//Motor_SetSpeed1(0);
//		//Motor_SetSpeed2(41);
//		//Motor_SetSpeed1(40);
//		//Delay_ms(600);
//		//Delay_ms(100);
//		Motor_SetSpeed2(0);
//		Motor_SetSpeed1(0);
//		WayKey=0;
//		Motor_SetSpeed2(41);
//		Motor_SetSpeed1(40);
//		Delay_ms(600);
//		Motor_SetSpeed2(0);
//		Motor_SetSpeed1(0);
//		TIM_Cmd(TIM4, DISABLE);
//		
//	}
//	if(detection1()==0&&detection3()==0&&detection4()==0&&detection0()==1)
//	{	//Motor_SetSpeed2(0);
//		//Motor_SetSpeed1(0);
//		//Motor_SetSpeed2(41);
//		//Motor_SetSpeed1(40);
//		//Delay_ms(600);
//		//Delay_ms(100);
//		Motor_SetSpeed2(0);
//		Motor_SetSpeed1(0);
//		WayKey=0;
//		Motor_SetSpeed2(41);
//		Motor_SetSpeed1(40);
//		Delay_ms(600);
//		Motor_SetSpeed2(0);
//		Motor_SetSpeed1(0);
//		TIM_Cmd(TIM4, DISABLE);
//	}
}










	