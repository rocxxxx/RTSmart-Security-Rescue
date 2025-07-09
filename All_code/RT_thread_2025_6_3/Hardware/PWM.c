#include "stm32f10x.h"                  // Device header

// PWM 初始化函数：使用 TIM2 通道 3 和通道 4，GPIOA 的 PA2 和 PA3 输出 PWM 信号
void PWM_Init()
{	
	// 1. 开启 GPIOA 时钟，为后续配置 PA2、PA3 作为 PWM 输出做准备
	RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);

	// 2. 配置 GPIOA 的 PA2 和 PA3 为复用推挽输出模式（用于输出 PWM）
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode = GPIO_Mode_AF_PP;           // 复用推挽输出
	GPIO_InitStructure.GPIO_Pin = GPIO_Pin_2 | GPIO_Pin_3;    // 配置 PA2、PA3
	GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;         // 输出速率 50MHz
	GPIO_Init(GPIOA, &GPIO_InitStructure);

	// 3. 开启 TIM2 定时器的时钟（在 APB1 总线上）
	RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM2, ENABLE);

	// 4. 设置 TIM2 使用内部时钟（默认就是内部时钟）
	TIM_InternalClockConfig(TIM2);

	// 5. 初始化 TIM2 的时基单元（即 PWM 的频率设置）
	TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStruct;
	TIM_TimeBaseInitStruct.TIM_ClockDivision = TIM_CKD_DIV1;         // 时钟分频，不分频
	TIM_TimeBaseInitStruct.TIM_CounterMode = TIM_CounterMode_Up;     // 向上计数模式
	TIM_TimeBaseInitStruct.TIM_Period = 100 - 1;                     // 自动重装载值 ARR，PWM周期
	TIM_TimeBaseInitStruct.TIM_Prescaler = 720 - 1;                  // 预分频器 PSC
	TIM_TimeBaseInitStruct.TIM_RepetitionCounter = 0;                // 重复计数器，TIM2 不用
	TIM_TimeBaseInit(TIM2, &TIM_TimeBaseInitStruct);

	// 计算 PWM 周期：
	// PWM 周期 = (PSC + 1) × (ARR + 1) / TIM_CLK = 720 × 100 / 72MHz = 1ms（即频率为 1kHz）

	// 6. 配置输出比较单元为 PWM 模式
	TIM_OCInitTypeDef TIM_OCInitStruct;
	TIM_OCStructInit(&TIM_OCInitStruct);                     // 初始化结构体默认值
	TIM_OCInitStruct.TIM_OCMode = TIM_OCMode_PWM1;           // 设置为 PWM1 模式
	TIM_OCInitStruct.TIM_OCPolarity = TIM_OCPolarity_High;   // 高电平有效
	TIM_OCInitStruct.TIM_OutputState = ENABLE;               // 使能输出
	TIM_OCInitStruct.TIM_Pulse = 0;                          // 初始比较值（占空比为 0%）

	// 7. 初始化 TIM2 的通道 3 和通道 4 为 PWM 输出
	TIM_OC3Init(TIM2, &TIM_OCInitStruct);    // 对应 PA2
	TIM_OC4Init(TIM2, &TIM_OCInitStruct);    // 对应 PA3

	// 8. 启动 TIM2 定时器，开始输出 PWM
	TIM_Cmd(TIM2, ENABLE);
}


// 设置 TIM2 通道 3 的比较值（控制 PWM 占空比）
void PWM_SetCompare3(uint16_t Compare)
{
	TIM_SetCompare3(TIM2, Compare);  // 设置 CCR3 值，占空比 = CCR / ARR
}


// 设置 TIM2 通道 4 的比较值（控制 PWM 占空比）
void PWM_SetCompare4(uint16_t Compare)
{
	TIM_SetCompare4(TIM2, Compare);  // 设置 CCR4 值，占空比 = CCR / ARR
}


/*打开电机*/
void set_motor_enable(void)
{	
	TIM_Cmd(TIM2,ENABLE);
}


/*关闭电机*/
void set_motor_disable(void)
{
	PWM_SetCompare3(0);
	PWM_SetCompare4(0);	
	TIM_Cmd(TIM2,DISABLE);
}



