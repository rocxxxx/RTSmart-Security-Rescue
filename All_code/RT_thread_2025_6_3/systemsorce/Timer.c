#include "stm32f10x.h" // 设备头文件，包含所有寄存器定义和外设函数声明

/**
 * @brief 定时器 TIM1 初始化函数，用于配置一个基础定时中断
 *        此处配置为：周期 10ms（100Hz 中断），使用 APB2 总线上的 TIM1
 */
void Timer_1_Init(void)
{
    // 1. 打开 TIM1 定时器的时钟（TIM1 位于 APB2 总线）
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM1, ENABLE);
    
    // 2. 配置 TIM1 使用内部时钟源（默认就是内部时钟）
    TIM_InternalClockConfig(TIM1);
    
    // 3. 设置 TIM1 的基本时间参数（定时器时基配置）
    TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure;
    TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;       // 不分频，滤波器时钟 = tDTS
    TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up;   // 向上计数模式
    TIM_TimeBaseInitStructure.TIM_Period = 100 - 1;                    // 自动重装载值 ARR=99，每 100 个计数溢出一次
    TIM_TimeBaseInitStructure.TIM_Prescaler = 7200 - 1;                // 预分频器 PSC=7199，T = 7200*100 / 72M = 0.01s
    TIM_TimeBaseInitStructure.TIM_RepetitionCounter = 0;              // 高级定时器重复计数器（一般设置为 0）
    TIM_TimeBaseInit(TIM1, &TIM_TimeBaseInitStructure);
    
    // 4. 清除更新中断标志位，防止刚启动就进入一次中断
    TIM_ClearFlag(TIM1, TIM_FLAG_Update);
    
    // 5. 开启定时器更新中断（即溢出中断）
    TIM_ITConfig(TIM1, TIM_IT_Update, ENABLE);
    
    // 6. 设置 NVIC 优先级分组（分组2：2位抢占优先级，2位子优先级）
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
    
    // 7. 配置 NVIC 中断控制器
    NVIC_InitTypeDef NVIC_InitStructure;
    NVIC_InitStructure.NVIC_IRQChannel = TIM1_UP_IRQn;        // TIM1 更新中断通道
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;           // 启用中断通道
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 2; // 抢占优先级 2
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 2;        // 子优先级 2
    NVIC_Init(&NVIC_InitStructure);
    
    // 8. 启动 TIM1 定时器
    TIM_Cmd(TIM1, ENABLE);
}
