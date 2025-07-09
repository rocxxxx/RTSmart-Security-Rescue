#ifndef __MODOL_SWITCH_H
#define __MODOL_SWITCH_H


extern u8 keyNum;  
extern u8 basis;  //基准速度 externu8 mode=0;  //模式  extern
extern u8 Car_mode; // 主车发给从车 运行模式指令 01 02 03 04 05
extern u8 Car_stop; // 主车发给从车停止指令  0x2B 当从车接收到0x2B后  从车立刻停止
extern u8 Car_quan; // 主车发给从车 内外圈指令
extern u8 count1,count2; //速度  模式  
extern u8 mode;
extern u8 mode3_chalu;
extern uint16_t distance;
void modol_init(void);
void key_switch(void);
#endif
