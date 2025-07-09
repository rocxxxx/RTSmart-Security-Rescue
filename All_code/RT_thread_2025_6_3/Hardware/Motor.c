#include "stm32f10x.h"      // STM32 标准库头文件
#include "PWM.h"            // 自定义 PWM 控制头文件

// ========================
// 电机初始化函数
// ========================
void Motor_Init()
{
    GPIO_InitTypeDef GPIO_InitStructure;

	// 启用 GPIOA、GPIOB 和 GPIOG 时钟
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOG, ENABLE);  // 添加这一行，启用 GPIOG

	// 配置 PA4 和 PA5 为推挽输出（左电机方向控制）
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_4 | GPIO_Pin_5;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;  // 推挽输出
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	// 配置 PB3 和 PB5 为推挽输出（右电机方向控制）
	// 你原来写错了注释，这一行为 PB3 和 PB5，而不是 PB4 和 PB5
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_3 | GPIO_Pin_5;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOB, &GPIO_InitStructure);

	// 配置 PG15 为推挽输出（你新增的）
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_15;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
	GPIO_Init(GPIOG, &GPIO_InitStructure);

	// 初始化 PWM（由外部 PWM_Init 实现）
	PWM_Init();

}

// ========================
// 控制左电机转动函数
// Speed1: -100 ~ 100，正数正转，负数反转
// ========================
void left(int8_t Speed1)
{
    if(Speed1 >= 0)  // 正转
    {
        GPIO_SetBits(GPIOA, GPIO_Pin_4);   // IN1 高电平
        GPIO_ResetBits(GPIOA, GPIO_Pin_5); // IN2 低电平
        PWM_SetCompare3(Speed1);           // 设置 PWM 占空比（速度）
    }
    else             // 反转
    {
        GPIO_ResetBits(GPIOA, GPIO_Pin_4); // IN1 低电平
        GPIO_SetBits(GPIOA, GPIO_Pin_5);   // IN2 高电平
        PWM_SetCompare3(-Speed1);          // 设置 PWM 占空比（取正值）
    }
}

// ========================
// 控制右电机转动函数
// Speed2: -100 ~ 100，正数正转，负数反转
// ========================
void right(int8_t Speed2)
{
    if(Speed2 >= 0)  // 正转
    {
        GPIO_SetBits(GPIOG, GPIO_Pin_15);   // IN1 高电平
        GPIO_ResetBits(GPIOB, GPIO_Pin_5); // IN2 低电平
        PWM_SetCompare4(Speed2);           // 设置 PWM 占空比
    }
    else             // 反转
    {
        GPIO_ResetBits(GPIOG, GPIO_Pin_15); // IN1 低电平
        GPIO_SetBits(GPIOB, GPIO_Pin_5);   // IN2 高电平
        PWM_SetCompare4(-Speed2);          // 设置 PWM 占空比
    }
}
