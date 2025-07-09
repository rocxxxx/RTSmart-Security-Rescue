#include "stm32f10x.h"                  // Device header

void IC_Init()
{
	///////初始化定时器
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA,ENABLE);//开启GPIOA_0引脚的时钟，借此引脚输出PWM
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_IPU;//选择上拉输入中的一个模式
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_6;
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOA,&GPIO_InitStructure);
	//
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3,ENABLE);//开启外设时钟
	TIM_InternalClockConfig(TIM3);//此时TIM2的时基单元就由内部时钟驱动
	
	TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStruct;
	TIM_TimeBaseInitStruct.TIM_ClockDivision=TIM_CKD_DIV1;//指定时钟分频，随便
	TIM_TimeBaseInitStruct.TIM_CounterMode=TIM_CounterMode_Up;//计数器模式,向上
	TIM_TimeBaseInitStruct.TIM_Period=65536-1;//使ARR可满量程技术
	TIM_TimeBaseInitStruct.TIM_Prescaler=72-1;//PSC
	TIM_TimeBaseInitStruct.TIM_RepetitionCounter=0;//用不着
	TIM_TimeBaseInit(TIM3,&TIM_TimeBaseInitStruct);//时基单元配置完成
	
	//////////开启输入捕获单元
	TIM_ICInitTypeDef TIM_ICInitStruct;
	TIM_ICInitStruct.TIM_Channel=TIM_Channel_1;//选择定时器通道
	TIM_ICInitStruct.TIM_ICFilter=0xF;//；滤波器
	TIM_ICInitStruct.TIM_ICPolarity=TIM_ICPolarity_Rising;//边沿检测
	TIM_ICInitStruct.TIM_ICPrescaler=TIM_ICPSC_DIV1;//分频器，不分频就是每次触发都有效，2分频即每隔一次有效一次
	TIM_ICInitStruct.TIM_ICSelection=TIM_ICSelection_DirectTI;//触发信号从哪个引脚输入
	TIM_ICInit(TIM3,&TIM_ICInitStruct );
	
	TIM_PWMIConfig (TIM3,&TIM_ICInitStruct);//自动初始化另一通道
	
	///配置触发源
	TIM_SelectInputTrigger(TIM3,TIM_TS_TI1FP1);
	TIM_SelectSlaveMode(TIM3,TIM_SlaveMode_Reset);//配置从模式
	TIM_Cmd(TIM3,ENABLE);//启动定时器，会一直自增，信号来后在从模式作用下清零

}
uint32_t IC_GetFreg()
{
	return 1000000/(TIM_GetCapture1(TIM3)+1);//函数作用为获取TIMx输入捕获值

}

uint32_t IC_GetDuty()//计算占空比函数
{
	return (TIM_GetCapture2(TIM3)+1)*100/(TIM_GetCapture1(TIM3)+1);

}





