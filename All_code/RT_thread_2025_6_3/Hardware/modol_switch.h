#ifndef __MODOL_SWITCH_H
#define __MODOL_SWITCH_H


extern u8 keyNum;  
extern u8 basis;  //��׼�ٶ� externu8 mode=0;  //ģʽ  extern
extern u8 Car_mode; // ���������ӳ� ����ģʽָ�� 01 02 03 04 05
extern u8 Car_stop; // ���������ӳ�ָֹͣ��  0x2B ���ӳ����յ�0x2B��  �ӳ�����ֹͣ
extern u8 Car_quan; // ���������ӳ� ����Ȧָ��
extern u8 count1,count2; //�ٶ�  ģʽ  
extern u8 mode;
extern u8 mode3_chalu;
extern uint16_t distance;
void modol_init(void);
void key_switch(void);
#endif
