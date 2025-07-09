#include "stm32f10x.h"                  // Device header
#include <stdint.h>
#include <string.h>
#include "PID.h"


//———————————————————— PID 参数配置区域 ———————————————————
// 外环（方向环）PID 系数（单位为千分之一）-----------------------根据ERR算出期望速度
#define DIR_KP_I    1000    // 比例项，影响偏差修正速度
#define DIR_KI_I     0    // 积分项，修正稳态误差
#define DIR_KD_I    100    // 微分项，抑制偏差变化带来的震荡

#define MAX_ADJUST   90     // 最大方向调整量（防止输出过大）
#define MAX_SPEED    90     // 最大轮速设定值（期望速度）

// 内环（速度环）PID 系数（单位为千分之一）---------------------- 根据期望速度算出真实速度
#define SPD_KP_I    2000    // 比例项，影响速度误差修正快慢
#define SPD_KI_I     100    // 积分项，修正速度稳态误差
#define SPD_KD_I     200    // 微分项，抑制速度变化带来的震荡

#define MAX_PWM    90     // 电机 PWM 输出最大值（根据平台设定）

// ———— 新增：脉冲映射参数 ————  
// 实测：PWM=50 时，在 0.1s 中断里读到的编码器脉冲数大约是 15
#define SAMPLE_CNT_50   15  
#define REF_PWM         50   // 参考 PWM 值

//———————————————————— PID 历史状态变量 ———————————————————
// 外环 PID 历史误差值
static int16_t dir_e1 = 0;   // 上一次偏差 e(k-1)
static int16_t dir_e2 = 0;   // 上上次偏差 e(k-2)
static int32_t dir_u1 = 0;   // 上一次方向控制输出 u(k-1)

static PIDState pidL = {0};   // 左电机 PID 状态
static PIDState pidR = {0};   // 右电机 PID 状态

/**
 * @brief  外环 PID 控制：根据车道偏差调整左右轮的目标速度
 * @param  err       当前偏差（ERR > 0 表示偏左，需要左轮快）
 * @param  baseSpeed 基础速度（巡航速度）
 * @param  vL_set    输出左轮目标速度
 * @param  vR_set    输出右轮目标速度
 */
void DirectionPID(int16_t err, int16_t baseSpeed,
                  int16_t *vL_set, int16_t *vR_set)
{
    // —— 1. 计算增量 Δu ——
    int32_t du =  (int32_t)DIR_KP_I * (err - dir_e1)
                + (int32_t)DIR_KI_I *  err
                + (int32_t)DIR_KD_I * (err - 2*dir_e1 + dir_e2);
    du /= 1000;  // 千分制换算

    // —— 2. 累加增量并限幅 ——
    int32_t u = dir_u1 + du;
    if (u >  MAX_ADJUST) u =  MAX_ADJUST;
    if (u < -MAX_ADJUST) u = -MAX_ADJUST;

    // —— 3. 设置左右轮目标速度 ——
    *vL_set = baseSpeed + u;
    *vR_set = baseSpeed - u;

    // 限幅保护
    if (*vL_set >  MAX_SPEED) *vL_set =  MAX_SPEED;
    if (*vL_set < -MAX_SPEED) *vL_set = -MAX_SPEED;
    if (*vR_set >  MAX_SPEED) *vR_set =  MAX_SPEED;
    if (*vR_set < -MAX_SPEED) *vR_set = -MAX_SPEED;

    // —— 4. 更新历史误差和输出 ——
    dir_e2 = dir_e1;
    dir_e1 = err;
    dir_u1 = u;
}

/**
 * @brief  通用速度环 PID 控制：根据目标速度与实际速度，输出 PWM
 * @param  v_set   当前目标速度
 * @param  v_act   编码器实际测得速度
 * @param  state   PID 状态指针（左右电机独立使用）
 * @return         控制输出（PWM，带符号）
 */
int16_t SpeedPID(int16_t v_set, int16_t v_act, PIDState *state)
{
    int16_t err = v_set - v_act;  // 当前速度误差

    // —— 1. 计算增量 Δu ——
    int32_t du =  (int32_t)SPD_KP_I * (err - state->e1)
                + (int32_t)SPD_KI_I *  err
                + (int32_t)SPD_KD_I * (err - 2*state->e1 + state->e2);
    du /= 1000;

    // —— 2. 累加增量并限幅 ——
    int32_t u = state->u1 + du;
    if (u >  MAX_PWM) u =  MAX_PWM;
    if (u < -MAX_PWM) u = -MAX_PWM;

    // —— 3. 更新历史误差和输出 ——
    state->e2 = state->e1;
    state->e1 = err;
    state->u1 = u;

    return (int16_t)u;
}

/**
 * @brief  闭环主控函数：方向控制 + 脉冲域速度闭环控制
 * @param  line_err   当前车道偏差
 * @param  baseSpeed  巡航基准速度（0~MAX_SPEED，对应 PWM 也在此范围）
 * @param  vL_act     左轮 0.1s 内实际脉冲数
 * @param  vR_act     右轮 0.1s 内实际脉冲数
 * @param  pwmL       左轮 PWM 输出（结果）
 * @param  pwmR       右轮 PWM 输出（结果）
 */
void ClosedLoopControl(int16_t line_err, int16_t baseSpeed,
                       int16_t vL_act, int16_t vR_act,
                       int16_t *pwmL, int16_t *pwmR)
{
    int16_t vL_set, vR_set;
    // —— 外环：计算左右“期望速度” ——
    DirectionPID(line_err, baseSpeed, &vL_set, &vR_set);

    // —— 脉冲域映射 ——  
    // 将“期望速度”v_set映射成“期望脉冲数/0.1s”
    // v_set / REF_PWM * SAMPLE_CNT_50
    int16_t vL_goal = (int32_t)vL_set * SAMPLE_CNT_50 / REF_PWM;
    int16_t vR_goal = (int32_t)vR_set * SAMPLE_CNT_50 / REF_PWM;

//    // —— 内环：脉冲闭环 PID，输出真正的 PWM ——
//    *pwmL = SpeedPID(vL_goal, vL_act, &pidL);
//    *pwmR = SpeedPID(vR_goal, vR_act, &pidR);
	//----暂时关掉内环
    *pwmL = vL_set;
    *pwmR = vR_set;
}




/*********ERR处理函数，使之平滑少毛刺**********/
//滑动滤波器
#define ERR_FILTER_SIZE 15  // 平滑窗口大小，可调为3~7，使用几个历史数据进行平滑

int ERR_Buffer[ERR_FILTER_SIZE] = {0};
uint8_t err_index = 0;

int smooth_err(int new_err)
{
    // 加入新数据
    ERR_Buffer[err_index] = new_err;
    err_index = (err_index + 1) % ERR_FILTER_SIZE;

    // 求平均
    int sum = 0;
    for(int i = 0; i < ERR_FILTER_SIZE; i++)
    {
        sum += ERR_Buffer[i];
    }

    return sum / ERR_FILTER_SIZE;
}

//中值滤波器
#define MEDIAN_SIZE 15  // 建议用奇数个

int median_buffer[MEDIAN_SIZE] = {0};
uint8_t median_index = 0;

int median_filter(int new_err)
{
    // 添加新数据（循环更新）
    median_buffer[median_index] = new_err;
    median_index = (median_index + 1) % MEDIAN_SIZE;

    // 拷贝用于排序
    int temp[MEDIAN_SIZE];
    for(int i = 0; i < MEDIAN_SIZE; i++)
        temp[i] = median_buffer[i];

    // 冒泡排序
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

    // 返回中位数
    return temp[MEDIAN_SIZE / 2];
}

