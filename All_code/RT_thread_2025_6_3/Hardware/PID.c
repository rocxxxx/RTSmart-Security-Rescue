#include "stm32f10x.h"                  // Device header
#include <stdint.h>
#include <string.h>
#include "PID.h"


//���������������������������������������� PID ������������ ��������������������������������������
// �⻷�����򻷣�PID ϵ������λΪǧ��֮һ��-----------------------����ERR��������ٶ�
#define DIR_KP_I    1000    // �����Ӱ��ƫ�������ٶ�
#define DIR_KI_I     0    // �����������̬���
#define DIR_KD_I    100    // ΢�������ƫ��仯��������

#define MAX_ADJUST   90     // ��������������ֹ�������
#define MAX_SPEED    90     // ��������趨ֵ�������ٶȣ�

// �ڻ����ٶȻ���PID ϵ������λΪǧ��֮һ��---------------------- ���������ٶ������ʵ�ٶ�
#define SPD_KP_I    2000    // �����Ӱ���ٶ������������
#define SPD_KI_I     100    // ����������ٶ���̬���
#define SPD_KD_I     200    // ΢��������ٶȱ仯��������

#define MAX_PWM    90     // ��� PWM ������ֵ������ƽ̨�趨��

// �������� ����������ӳ����� ��������  
// ʵ�⣺PWM=50 ʱ���� 0.1s �ж�������ı�������������Լ�� 15
#define SAMPLE_CNT_50   15  
#define REF_PWM         50   // �ο� PWM ֵ

//���������������������������������������� PID ��ʷ״̬���� ��������������������������������������
// �⻷ PID ��ʷ���ֵ
static int16_t dir_e1 = 0;   // ��һ��ƫ�� e(k-1)
static int16_t dir_e2 = 0;   // ���ϴ�ƫ�� e(k-2)
static int32_t dir_u1 = 0;   // ��һ�η��������� u(k-1)

static PIDState pidL = {0};   // ���� PID ״̬
static PIDState pidR = {0};   // �ҵ�� PID ״̬

/**
 * @brief  �⻷ PID ���ƣ����ݳ���ƫ����������ֵ�Ŀ���ٶ�
 * @param  err       ��ǰƫ�ERR > 0 ��ʾƫ����Ҫ���ֿ죩
 * @param  baseSpeed �����ٶȣ�Ѳ���ٶȣ�
 * @param  vL_set    �������Ŀ���ٶ�
 * @param  vR_set    �������Ŀ���ٶ�
 */
void DirectionPID(int16_t err, int16_t baseSpeed,
                  int16_t *vL_set, int16_t *vR_set)
{
    // ���� 1. �������� ��u ����
    int32_t du =  (int32_t)DIR_KP_I * (err - dir_e1)
                + (int32_t)DIR_KI_I *  err
                + (int32_t)DIR_KD_I * (err - 2*dir_e1 + dir_e2);
    du /= 1000;  // ǧ���ƻ���

    // ���� 2. �ۼ��������޷� ����
    int32_t u = dir_u1 + du;
    if (u >  MAX_ADJUST) u =  MAX_ADJUST;
    if (u < -MAX_ADJUST) u = -MAX_ADJUST;

    // ���� 3. ����������Ŀ���ٶ� ����
    *vL_set = baseSpeed + u;
    *vR_set = baseSpeed - u;

    // �޷�����
    if (*vL_set >  MAX_SPEED) *vL_set =  MAX_SPEED;
    if (*vL_set < -MAX_SPEED) *vL_set = -MAX_SPEED;
    if (*vR_set >  MAX_SPEED) *vR_set =  MAX_SPEED;
    if (*vR_set < -MAX_SPEED) *vR_set = -MAX_SPEED;

    // ���� 4. ������ʷ������� ����
    dir_e2 = dir_e1;
    dir_e1 = err;
    dir_u1 = u;
}

/**
 * @brief  ͨ���ٶȻ� PID ���ƣ�����Ŀ���ٶ���ʵ���ٶȣ���� PWM
 * @param  v_set   ��ǰĿ���ٶ�
 * @param  v_act   ������ʵ�ʲ���ٶ�
 * @param  state   PID ״ָ̬�루���ҵ������ʹ�ã�
 * @return         ���������PWM�������ţ�
 */
int16_t SpeedPID(int16_t v_set, int16_t v_act, PIDState *state)
{
    int16_t err = v_set - v_act;  // ��ǰ�ٶ����

    // ���� 1. �������� ��u ����
    int32_t du =  (int32_t)SPD_KP_I * (err - state->e1)
                + (int32_t)SPD_KI_I *  err
                + (int32_t)SPD_KD_I * (err - 2*state->e1 + state->e2);
    du /= 1000;

    // ���� 2. �ۼ��������޷� ����
    int32_t u = state->u1 + du;
    if (u >  MAX_PWM) u =  MAX_PWM;
    if (u < -MAX_PWM) u = -MAX_PWM;

    // ���� 3. ������ʷ������� ����
    state->e2 = state->e1;
    state->e1 = err;
    state->u1 = u;

    return (int16_t)u;
}

/**
 * @brief  �ջ����غ������������ + �������ٶȱջ�����
 * @param  line_err   ��ǰ����ƫ��
 * @param  baseSpeed  Ѳ����׼�ٶȣ�0~MAX_SPEED����Ӧ PWM Ҳ�ڴ˷�Χ��
 * @param  vL_act     ���� 0.1s ��ʵ��������
 * @param  vR_act     ���� 0.1s ��ʵ��������
 * @param  pwmL       ���� PWM ����������
 * @param  pwmR       ���� PWM ����������
 */
void ClosedLoopControl(int16_t line_err, int16_t baseSpeed,
                       int16_t vL_act, int16_t vR_act,
                       int16_t *pwmL, int16_t *pwmR)
{
    int16_t vL_set, vR_set;
    // ���� �⻷���������ҡ������ٶȡ� ����
    DirectionPID(line_err, baseSpeed, &vL_set, &vR_set);

    // ���� ������ӳ�� ����  
    // ���������ٶȡ�v_setӳ��ɡ�����������/0.1s��
    // v_set / REF_PWM * SAMPLE_CNT_50
    int16_t vL_goal = (int32_t)vL_set * SAMPLE_CNT_50 / REF_PWM;
    int16_t vR_goal = (int32_t)vR_set * SAMPLE_CNT_50 / REF_PWM;

//    // ���� �ڻ�������ջ� PID����������� PWM ����
//    *pwmL = SpeedPID(vL_goal, vL_act, &pidL);
//    *pwmR = SpeedPID(vR_goal, vR_act, &pidR);
	//----��ʱ�ص��ڻ�
    *pwmL = vL_set;
    *pwmR = vR_set;
}




/*********ERR��������ʹ֮ƽ����ë��**********/
//�����˲���
#define ERR_FILTER_SIZE 15  // ƽ�����ڴ�С���ɵ�Ϊ3~7��ʹ�ü�����ʷ���ݽ���ƽ��

int ERR_Buffer[ERR_FILTER_SIZE] = {0};
uint8_t err_index = 0;

int smooth_err(int new_err)
{
    // ����������
    ERR_Buffer[err_index] = new_err;
    err_index = (err_index + 1) % ERR_FILTER_SIZE;

    // ��ƽ��
    int sum = 0;
    for(int i = 0; i < ERR_FILTER_SIZE; i++)
    {
        sum += ERR_Buffer[i];
    }

    return sum / ERR_FILTER_SIZE;
}

//��ֵ�˲���
#define MEDIAN_SIZE 15  // ������������

int median_buffer[MEDIAN_SIZE] = {0};
uint8_t median_index = 0;

int median_filter(int new_err)
{
    // ��������ݣ�ѭ�����£�
    median_buffer[median_index] = new_err;
    median_index = (median_index + 1) % MEDIAN_SIZE;

    // ������������
    int temp[MEDIAN_SIZE];
    for(int i = 0; i < MEDIAN_SIZE; i++)
        temp[i] = median_buffer[i];

    // ð������
    for(int i = 0; i < MEDIAN_SIZE - 1; i++)
    {
        for(int j = 0; j < MEDIAN_SIZE - 1 - i; j++)
        {
            if(temp[j] > temp[j+1])
            {
                int t = temp[j];
                temp[j] = temp[j+1];
                temp[j+1] = t;
            }
        }
    }

    // ������λ��
    return temp[MEDIAN_SIZE / 2];
}

