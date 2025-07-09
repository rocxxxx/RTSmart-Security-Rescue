#ifndef __OLED_H
#define __OLED_H
#include <stdint.h>

void OLED_Init(void);
// OLED ��ʼ�����������ڳ�ʼ�� OLED ��ʾ����Ӳ����ͨ�Žӿ�

void OLED_Clear(void);
// OLED ���������������Ļ�ϵ�������ʾ���ݣ�ͨ�����Ϊ��ɫ��հף�

void OLED_ShowChar(uint8_t Line, uint8_t Column, char Char);
// ��ָ���У�1~4�����У�1~16����ʾһ���ַ�

void OLED_ShowString(uint8_t Line, uint8_t Column, char *String);
// ��ָ���С���λ����ʾһ���ַ������� '\0' ��β���ַ����飩

void OLED_ShowNum(uint8_t Line, uint8_t Column, uint32_t Number, uint8_t Length);
// ��ָ��λ����ʾһ���޷���ʮ��������������Ϊ Length λ�����㲹�㣩

void OLED_ShowSignedNum(uint8_t Line, uint8_t Column, int32_t Number, uint8_t Length);
// ��ʾ�����ŵ�ʮ��������������������������Ϊ Length λ

void OLED_ShowHexNum(uint8_t Line, uint8_t Column, uint32_t Number, uint8_t Length);
// ��ʾʮ������������ 0x1A3F����Length ��ʾ��ʾ��λ��

void OLED_ShowBinNum(uint8_t Line, uint8_t Column, uint32_t Number, uint8_t Length);
// ��ʾ������������ 101010����Length ��ʾ��ʾ��λ��


#endif
