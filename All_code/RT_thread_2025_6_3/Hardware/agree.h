#ifndef __agree_H
#define __agree_H
#include <stdint.h>


void Process_OpenMV_Frame(void);
void Openmv_Receive_Data(uint8_t data); // ����Openmv������������
void Process_HC_Frame(void);
void HC_Receive_Data(uint8_t data);


#endif

