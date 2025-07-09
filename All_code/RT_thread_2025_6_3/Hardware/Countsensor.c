#include "stm32f10x.h"                  // Device head
#include "OLED.h"

uint16_t Countsensor_count;
extern double Distance;

void Contsensor_Init(void)
{
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOE,ENABLE);//开启GPIOB的时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_AFIO,ENABLE);//开启外设AFIO的时钟
	
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_IPD;//选择浮空，上拉，下拉输入中的一个模式
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_14;
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOE,&GPIO_InitStructure);
	GPIO_EXTILineConfig(GPIO_PortSourceGPIOE,GPIO_PinSource14);//AFIO中断引脚配置选择
	
	EXTI_InitTypeDef EXTI_InitStructure;//外设的结构体定义
	EXTI_InitStructure.EXTI_Line=EXTI_Line14;//线路14
	EXTI_InitStructure.EXTI_LineCmd=ENABLE;//开启中断
	EXTI_InitStructure.EXTI_Mode=EXTI_Mode_Interrupt;//模式
	EXTI_InitStructure.EXTI_Trigger=EXTI_Trigger_Falling;//下降沿触发
	EXTI_Init(&EXTI_InitStructure);
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);//整个芯片只能有一种分组方式
	NVIC_InitTypeDef NVIC_Initstructure;
	NVIC_Initstructure.NVIC_IRQChannel=EXTI15_10_IRQn;//通道
	NVIC_Initstructure.NVIC_IRQChannelCmd=ENABLE;
	NVIC_Initstructure.NVIC_IRQChannelPreemptionPriority=2; //抢占优先级
	NVIC_Initstructure.NVIC_IRQChannelSubPriority=2; //响应优先级
	NVIC_Init(&NVIC_Initstructure);
	
}

uint16_t Countsensor_get()
{
	return Countsensor_count;
	
}
void EXTI15_10_IRQHandler()//中断函数
{
	if((EXTI_GetITStatus(EXTI_Line14))==SET)//判断中断源是否正确
	{
		Countsensor_count++;
		if(Countsensor_count<=3)
		//OLED_ShowSignedNum(Countsensor_count,4,Distance,6);
		EXTI_ClearITPendingBit(EXTI_Line14);//清楚中断标志位
		
	}
	
	
}