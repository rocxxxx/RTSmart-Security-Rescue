#ifndef __OLED_H
#define __OLED_H
#include <stdint.h>

void OLED_Init(void);
// OLED 初始化函数：用于初始化 OLED 显示屏的硬件和通信接口

void OLED_Clear(void);
// OLED 清屏函数：清除屏幕上的所有显示内容（通常填充为黑色或空白）

void OLED_ShowChar(uint8_t Line, uint8_t Column, char Char);
// 在指定行（1~4）、列（1~16）显示一个字符

void OLED_ShowString(uint8_t Line, uint8_t Column, char *String);
// 在指定行、列位置显示一个字符串（以 '\0' 结尾的字符数组）

void OLED_ShowNum(uint8_t Line, uint8_t Column, uint32_t Number, uint8_t Length);
// 在指定位置显示一个无符号十进制整数，长度为 Length 位（不足补零）

void OLED_ShowSignedNum(uint8_t Line, uint8_t Column, int32_t Number, uint8_t Length);
// 显示带符号的十进制整数（可正负数），长度为 Length 位

void OLED_ShowHexNum(uint8_t Line, uint8_t Column, uint32_t Number, uint8_t Length);
// 显示十六进制数（如 0x1A3F），Length 表示显示的位数

void OLED_ShowBinNum(uint8_t Line, uint8_t Column, uint32_t Number, uint8_t Length);
// 显示二进制数（如 101010），Length 表示显示的位数


#endif
