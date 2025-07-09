#ifndef _HC_SERIAL_H
#define _HC_SERIAL_H
#include <stdint.h>


void HC_Init(void);
void Uart3_Serial_SendByte(uint8_t Byte);
void Serial_SendArray(uint8_t *Array,uint16_t Length);
void Serial_SendString(char *String);
uint32_t Serial_Pow(uint32_t x, uint32_t y);
void Uart3_Serial_SendNum(uint32_t Number,uint8_t Length);
void Serial_SendPacket(void);
uint8_t Serial_GetRxFlag(void);
void HC_SendData(void);
void HC_GetData(void);

#endif

