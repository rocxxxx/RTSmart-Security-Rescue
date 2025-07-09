#ifndef __PID_H
#define __PID_H
#include <stdint.h>


void DirectionPID(int16_t err, int16_t baseSpeed,int16_t *vL_set, int16_t *vR_set);
typedef struct {
    int16_t e1;   // ��һ���ٶ���� e(k-1)
    int16_t e2;   // ���ϴ��ٶ���� e(k-2)
    int32_t u1;   // ��һ�� PWM ��� u(k-1)
} PIDState;
int16_t SpeedPID(int16_t v_set, int16_t v_act, PIDState *state);
void ClosedLoopControl(int16_t line_err, int16_t baseSpeed,int16_t vL_act, int16_t vR_act,int16_t *pwmL, int16_t *pwmR);
int smooth_err(int new_err);
int median_filter(int new_err);

#endif
