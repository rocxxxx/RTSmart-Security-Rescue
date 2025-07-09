#ifndef _PWM_H
#define _PWM_H
#include <stdint.h>

void PWM_Init(void);
void PWM_SetCompare3(uint16_t Compare);
void PWM_SetCompare4(uint16_t Compare);
void set_motor_enable(void);
void set_motor_disable(void);
#endif
