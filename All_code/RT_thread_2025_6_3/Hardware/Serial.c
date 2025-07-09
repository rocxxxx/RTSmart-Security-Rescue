#include "stm32f10x.h"                  // Device header
#include <stdio.h>
#include <stdarg.h>


void Uart1_Serial_Init(void)
	{	//TX:A9	RX:A10
	RCC_APB2PeriphClockCmd (RCC_APB2Periph_USART1,ENABLE);//��ʱ��
	RCC_APB2PeriphClockCmd (RCC_APB2Periph_GPIOA,ENABLE);
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_AF_PP;//TXΪ����ţ��������������RXΪ����ģʽ��
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_9;
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOA,&GPIO_InitStructure);
	
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_IPU;//TXΪ����ţ��������������RXΪ����ģʽ,�������룻
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_10;
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOA,&GPIO_InitStructure);
	
	USART_InitTypeDef USART_InitStructure;
	USART_InitStructure.USART_BaudRate=9600;//������
	USART_InitStructure.USART_HardwareFlowControl=USART_HardwareFlowControl_None;//����
	USART_InitStructure.USART_Mode=USART_Mode_Tx|USART_Mode_Rx;//ģʽ�����ͻ����
	USART_InitStructure.USART_Parity=USART_Parity_No;//У��λ
	USART_InitStructure.USART_StopBits=USART_StopBits_1;//ֹͣλ
	USART_InitStructure.USART_WordLength=USART_WordLength_8b;//�ֳ�
	USART_Init(USART1 ,&USART_InitStructure);//����1��ʼ��
	
	//�ѽ��շ����ж���
	USART_ITConfig(USART1 ,USART_IT_RXNE,ENABLE);
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);//ͨ��
	NVIC_InitTypeDef NVIC_InitStructure;//��ʼ��
	NVIC_InitStructure.NVIC_IRQChannel=USART1_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelCmd=ENABLE ;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority=3;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority=3;
	NVIC_Init(&NVIC_InitStructure);
	
	
	USART_Cmd (USART1 ,ENABLE);

}

void Uart1_Serial_SendByte(uint8_t Byte)//Byte�����ǵ���������ַ�
{
	USART_SendData(USART1 ,Byte);//д�����ݵ��Ĵ���
	while(USART_GetFlagStatus (USART1 ,USART_FLAG_TXE)==RESET);//��ȡ��־λ���ж����д��,�����ֶ�����
	
}

//void Serial_SendArray(uint8_t *Array,uint16_t Length)//����һ������
//{
//	uint16_t i;
//	for(i=0;i<Length ;i++)
//	{
//		Serial_SendByte(Array [i]);
//	}
//}

//void Serial_SendString(char *String)//����һ���ַ���
//{
//	uint8_t i;
//	for(i=0;String [i]!='\0' ;i++)
//	{
//		Serial_SendByte(String [i]);
//	}
//}

//uint32_t Serial_Pow(uint32_t x, uint32_t y)
//{
//	uint32_t Result=1;
//	while(y--)
//	{
//		Result *=x;
//	}
//	return Result ;
//}

//void Serial_SendNum(uint32_t Number,uint8_t Length)//��������,���ֲ𿪣�һλһλ�ķ�
//{
//	uint8_t i;
//	for(i=0;i<Length ;i++)
//	{
//		Serial_SendByte(Number/Serial_Pow(10,Length -i-1)%10+'0');
//	}

//}
//	
//int fputc(int ch,FILE *f)//��ӡ����ԭ���ض��򵽴���
//{
//	Serial_SendByte(ch);
//	return ch;
//	
//}

////��sprinttf���з�װ���ɱ������
//void Serial_Printf(char *format,...)
//{
//	char String[100];
//	va_list arg;
//	va_start (arg,format);
//	vsprintf (String ,format,arg);
//	va_end(arg);
//	Serial_SendString(String);
//	
//}

////���ݰ�����
//void Serial_SendPacket(void)
//{
//	Serial_SendByte(0xFF);//ͷ
//	Serial_SendArray(Serial_TxPacket,4);
//	Serial_SendByte(0xFE);//β

//}


//uint8_t Serial_GetRxFlag(void)//�˹��Ķ�ȡ��־λ���������
//{
//	if(Serial_RxFlag==1)
//	{
//		Serial_RxFlag=0;
//		return 1;
//	}
//	return 0;

//}

//uint8_t Serial_GetRxData(void)
//{
//	return Serial_RxData;

//}

//void USART1_IRQHandler(void)
//{
//	if(USART_GetITStatus(USART1 ,USART_IT_RXNE)==SET)
//	{
//		Serial_RxData=USART_ReceiveData(USART1);
//		Serial_RxFlag=1;
//		USART_ClearITPendingBit(USART1,USART_IT_RXNE);	
//	
//	}

////}
//void USART1_IRQHandler(void)
//{
//	static uint8_t RxState=0;//״̬��
//	static uint8_t pRxState=0;//ָʾ���ո���
//	if(USART_GetITStatus(USART1 ,USART_IT_RXNE)==SET)
//	{
//		uint8_t RxData=USART_ReceiveData(USART1);
//		
//		if(RxState==0)	
//		{
//			if(RxData==0xFF&&Serial_RxFlag==0)//������Ļ���Ҫ��Serial_RxFlag�ֶ�����
//			{
//				RxState=1;
//				pRxState=0;
//			}
//		}
//		else if(RxState==1)	
//		{
//			Serial_RxPacket[pRxState]=RxData;
//			pRxState++;
//			if(pRxState>=4)
//			{
//				RxState=2;
//			}
//			
//		}
//		else if(RxState==2)	
//		{
//			if(RxData==0xFE)
//			{
//				RxState=0;
//				Serial_RxFlag=1;
//			}
//		}
//	
//		USART_ClearITPendingBit(USART1,USART_IT_RXNE);
//	}



//}
