#include "stm32f10x.h"  // STM32 外设库头文件

// 初始化编码器接口（TIM3：PA6, PA7；TIM4：PB6, PB7）
void Encoder_Init(void)
{
    // ========= TIM3 - 配置编码器1使用 PA6 和 PA7 =========
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM3, ENABLE);   // 使能 TIM3 时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOA, ENABLE);  // 使能 GPIOA 时钟

    // 配置 PA6 和 PA7 为上拉输入模式（用于接收编码器 A、B 相信号）
    GPIO_InitTypeDef GPIO_InitStructure;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;            // 上拉输入
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;   // PA6、PA7
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);

    // 配置 TIM3 的时基单元
    TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure;
    TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;       // 不分频
    TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up;   // 向上计数模式
    TIM_TimeBaseInitStructure.TIM_Period = 65535;                     // 最大计数值 65535
    TIM_TimeBaseInitStructure.TIM_Prescaler = 0;                      // 不预分频
    TIM_TimeBaseInitStructure.TIM_RepetitionCounter = 0;
    TIM_TimeBaseInit(TIM3, &TIM_TimeBaseInitStructure);

    // 输入捕获结构体初始化
    TIM_ICInitTypeDef TIM_ICInitStructure;
    TIM_ICStructInit(&TIM_ICInitStructure);  // 初始化为默认值

    // 配置通道1
    TIM_ICInitStructure.TIM_Channel = TIM_Channel_1;
    TIM_ICInitStructure.TIM_ICFilter = 0xF;   // 输入滤波器：滤除干扰
    TIM_ICInit(TIM3, &TIM_ICInitStructure);

    // 配置通道2
    TIM_ICInitStructure.TIM_Channel = TIM_Channel_2;
    TIM_ICInitStructure.TIM_ICFilter = 0xF;
    TIM_ICInit(TIM3, &TIM_ICInitStructure);

    // 设置 TIM3 为编码器接口模式（TI1 和 TI2 双通道编码器模式）
    TIM_EncoderInterfaceConfig(
        TIM3,
        TIM_EncoderMode_TI12,
        TIM_ICPolarity_Rising,
        TIM_ICPolarity_Rising
    );

    // 启动 TIM3 计数器
    TIM_Cmd(TIM3, ENABLE);

    // ========= TIM4 - 配置编码器2使用 PB6 和 PB7 =========
    RCC_APB1PeriphClockCmd(RCC_APB1Periph_TIM4, ENABLE);   // 使能 TIM4 时钟
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_GPIOB, ENABLE);  // 使能 GPIOB 时钟

    // 配置 PB6 和 PB7 为上拉输入
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_IPU;
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_6 | GPIO_Pin_7;  // PB6、PB7
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOB, &GPIO_InitStructure);

    // TIM4 的时基单元配置（同 TIM3）
    TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;
    TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up;
    TIM_TimeBaseInitStructure.TIM_Period = 65535;
    TIM_TimeBaseInitStructure.TIM_Prescaler = 0;
    TIM_TimeBaseInitStructure.TIM_RepetitionCounter = 0;
    TIM_TimeBaseInit(TIM4, &TIM_TimeBaseInitStructure);

    // 输入捕获配置
    TIM_ICStructInit(&TIM_ICInitStructure);
    TIM_ICInitStructure.TIM_Channel = TIM_Channel_1;
    TIM_ICInitStructure.TIM_ICFilter = 0xF;
    TIM_ICInit(TIM4, &TIM_ICInitStructure);

    TIM_ICInitStructure.TIM_Channel = TIM_Channel_2;
    TIM_ICInitStructure.TIM_ICFilter = 0xF;
    TIM_ICInit(TIM4, &TIM_ICInitStructure);

    // 设置 TIM4 为编码器接口模式
    TIM_EncoderInterfaceConfig(
        TIM4,
        TIM_EncoderMode_TI12,
        TIM_ICPolarity_Rising,
        TIM_ICPolarity_Rising
    );

    // 启动 TIM4 计数器
    TIM_Cmd(TIM4, ENABLE);
}

// 读取编码器1（TIM3）的值，然后清零
int16_t Encoder_1_Get(void)
{
    int16_t Temp;
    Temp = TIM_GetCounter(TIM3);   // 读取当前计数值
    TIM_SetCounter(TIM3, 0);       // 读取后清零，为下次使用准备
    return Temp;                   // 返回增量值（PA6/PA7）
}

// 读取编码器2（TIM4）的值，然后清零
int16_t Encoder_2_Get(void)
{
    int16_t Temp;
    Temp = TIM_GetCounter(TIM4);   // 读取当前计数值
    TIM_SetCounter(TIM4, 0);       // 清零
    return Temp;                   // 返回增量值（PB6/PB7）
}
