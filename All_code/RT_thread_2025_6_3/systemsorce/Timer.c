#include "stm32f10x.h" // �豸ͷ�ļ����������мĴ�����������躯������

/**
 * @brief ��ʱ�� TIM1 ��ʼ����������������һ��������ʱ�ж�
 *        �˴�����Ϊ������ 10ms��100Hz �жϣ���ʹ�� APB2 �����ϵ� TIM1
 */
void Timer_1_Init(void)
{
    // 1. �� TIM1 ��ʱ����ʱ�ӣ�TIM1 λ�� APB2 ���ߣ�
    RCC_APB2PeriphClockCmd(RCC_APB2Periph_TIM1, ENABLE);
    
    // 2. ���� TIM1 ʹ���ڲ�ʱ��Դ��Ĭ�Ͼ����ڲ�ʱ�ӣ�
    TIM_InternalClockConfig(TIM1);
    
    // 3. ���� TIM1 �Ļ���ʱ���������ʱ��ʱ�����ã�
    TIM_TimeBaseInitTypeDef TIM_TimeBaseInitStructure;
    TIM_TimeBaseInitStructure.TIM_ClockDivision = TIM_CKD_DIV1;       // ����Ƶ���˲���ʱ�� = tDTS
    TIM_TimeBaseInitStructure.TIM_CounterMode = TIM_CounterMode_Up;   // ���ϼ���ģʽ
    TIM_TimeBaseInitStructure.TIM_Period = 100 - 1;                    // �Զ���װ��ֵ ARR=99��ÿ 100 ���������һ��
    TIM_TimeBaseInitStructure.TIM_Prescaler = 7200 - 1;                // Ԥ��Ƶ�� PSC=7199��T = 7200*100 / 72M = 0.01s
    TIM_TimeBaseInitStructure.TIM_RepetitionCounter = 0;              // �߼���ʱ���ظ���������һ������Ϊ 0��
    TIM_TimeBaseInit(TIM1, &TIM_TimeBaseInitStructure);
    
    // 4. ��������жϱ�־λ����ֹ�������ͽ���һ���ж�
    TIM_ClearFlag(TIM1, TIM_FLAG_Update);
    
    // 5. ������ʱ�������жϣ�������жϣ�
    TIM_ITConfig(TIM1, TIM_IT_Update, ENABLE);
    
    // 6. ���� NVIC ���ȼ����飨����2��2λ��ռ���ȼ���2λ�����ȼ���
    NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);
    
    // 7. ���� NVIC �жϿ�����
    NVIC_InitTypeDef NVIC_InitStructure;
    NVIC_InitStructure.NVIC_IRQChannel = TIM1_UP_IRQn;        // TIM1 �����ж�ͨ��
    NVIC_InitStructure.NVIC_IRQChannelCmd = ENABLE;           // �����ж�ͨ��
    NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority = 2; // ��ռ���ȼ� 2
    NVIC_InitStructure.NVIC_IRQChannelSubPriority = 2;        // �����ȼ� 2
    NVIC_Init(&NVIC_InitStructure);
    
    // 8. ���� TIM1 ��ʱ��
    TIM_Cmd(TIM1, ENABLE);
}
