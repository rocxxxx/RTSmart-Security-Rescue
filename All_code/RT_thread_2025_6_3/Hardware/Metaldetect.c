#include "stm32f10x.h"                  // Device header
#include "Delay.h"
//#include "Countsensor.h"
#include "OLED.h"

//extern uint8_t metal;
//extern volatile char temp;
//extern int temp1;
void Metaldetect_Init()
{
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOE,ENABLE);//初始化探测端口E14
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_Out_PP;//上拉输入
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_14|GPIO_Pin_0;
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOE,&GPIO_InitStructure);
	//GPIO_SetBits(GPIOA,GPIO_Pin_0);//高电平
	GPIO_ResetBits(GPIOE,GPIO_Pin_14);//低电平
	
	////类似于读取按键来读取金属探测输出电平
	
	
}

void Light_Sound()//声光信息
{
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOE, ENABLE);
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_Out_PP;
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_8|GPIO_Pin_9;//初始化端口E8,E0
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOE,&GPIO_InitStructure);
	GPIO_SetBits(GPIOE,GPIO_Pin_8);//给外接蜂鸣器置高电平
	
	GPIO_ResetBits(GPIOE,GPIO_Pin_8);GPIO_SetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_SetBits(GPIOE,GPIO_Pin_8);GPIO_ResetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_ResetBits(GPIOE,GPIO_Pin_8);GPIO_SetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_SetBits(GPIOE,GPIO_Pin_8);GPIO_ResetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_ResetBits(GPIOE,GPIO_Pin_8);GPIO_SetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_SetBits(GPIOE,GPIO_Pin_8);GPIO_ResetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_ResetBits(GPIOE,GPIO_Pin_8);GPIO_SetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_SetBits(GPIOE,GPIO_Pin_8);GPIO_ResetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_ResetBits(GPIOE,GPIO_Pin_8);GPIO_SetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_SetBits(GPIOE,GPIO_Pin_8);GPIO_ResetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	
}
void Light_Sound2()//声光信息
{
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOE, ENABLE);
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_Out_PP;
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_8|GPIO_Pin_9;//初始化端口E8,E0
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOE,&GPIO_InitStructure);
	GPIO_SetBits(GPIOE,GPIO_Pin_8);//给外接蜂鸣器置高电平
	
	GPIO_ResetBits(GPIOE,GPIO_Pin_8);GPIO_SetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_SetBits(GPIOE,GPIO_Pin_8);GPIO_ResetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_ResetBits(GPIOE,GPIO_Pin_8);GPIO_SetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	GPIO_SetBits(GPIOE,GPIO_Pin_8);GPIO_ResetBits(GPIOE,GPIO_Pin_9);
	Delay_ms (500);
	
}
