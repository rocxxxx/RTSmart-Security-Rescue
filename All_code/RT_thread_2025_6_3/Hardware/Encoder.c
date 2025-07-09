#include "stm32f10x.h"                  // Device header

uint16_t Encoder_Count;

void Encoder_Init_0()
{
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB,ENABLE);//开启GPIOB的时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO,ENABLE);//开启外设AFIO的时钟
	
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_IPU;//选择浮空，上拉，下拉输入中的一个模式
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_0|GPIO_Pin_1;
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOB,&GPIO_InitStructure);
	GPIO_EXTILineConfig(GPIO_PortSourceGPIOB,GPIO_PinSource0);//AFIO中断引脚配置选择
	GPIO_EXTILineConfig(GPIO_PortSourceGPIOB,GPIO_PinSource1);//AFIO中断引脚配置选择
	
	EXTI_InitTypeDef EXTI_InitStructure;//外设的结构体定义
	EXTI_InitStructure.EXTI_Line=EXTI_Line0|EXTI_Line1;//线路与引脚对应
	EXTI_InitStructure.EXTI_LineCmd=ENABLE;//开启中断
	EXTI_InitStructure.EXTI_Mode=EXTI_Mode_Interrupt;//模式
	EXTI_InitStructure.EXTI_Trigger=EXTI_Trigger_Falling;//下降沿触发
	
	EXTI_Init(&EXTI_InitStructure);
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);//整个芯片只能有一种分组方式
	NVIC_InitTypeDef NVIC_Initstructure;
	NVIC_Initstructure.NVIC_IRQChannel=EXTI0_IRQn;//通道与引脚对应
	NVIC_Initstructure.NVIC_IRQChannelCmd=ENABLE;
	NVIC_Initstructure.NVIC_IRQChannelPreemptionPriority=1; //抢占优先级
	NVIC_Initstructure.NVIC_IRQChannelSubPriority=1; //响应优先级
	NVIC_Init(&NVIC_Initstructure);
//结构体可重复使用，直接新的赋值即可
	NVIC_Initstructure.NVIC_IRQChannel=EXTI1_IRQn;//通道与引脚对应
	NVIC_Initstructure.NVIC_IRQChannelCmd=ENABLE;
	NVIC_Initstructure.NVIC_IRQChannelPreemptionPriority=1; //抢占优先级
	NVIC_Initstructure.NVIC_IRQChannelSubPriority=2; //响应优先级
	NVIC_Init(&NVIC_Initstructure);
}	

uint16_t Encoder_Get_0()
{
	uint16_t temp;
	temp=Encoder_Count;
	Encoder_Count=0;
	return temp;

}

//各通道的中断函数
void EXTI0_IRQHandler()
{
	if((EXTI_GetITStatus(EXTI_Line0))==SET)//判断中断源是否正确
	{
		if(GPIO_ReadInputDataBit(GPIOB,GPIO_Pin_1)==0)//判断正转与否，读引脚是高还是低电平
			Encoder_Count--;
		EXTI_ClearITPendingBit(EXTI_Line0);//清楚中断标志位
	}

}
void EXTI1_IRQHandler()
{
	if((EXTI_GetITStatus(EXTI_Line1))==SET)//判断中断源是否正确
	{
		if(GPIO_ReadInputDataBit(GPIOB,GPIO_Pin_0)==0)//判断正转与否，读引脚是高还是低电平
			Encoder_Count++;
		EXTI_ClearITPendingBit(EXTI_Line1);//清楚中断标志位
	}
}
