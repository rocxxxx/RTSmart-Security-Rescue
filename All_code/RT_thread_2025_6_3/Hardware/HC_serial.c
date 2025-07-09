#include "stm32f10x.h"                  // Device header
#include <stdio.h>
#include <stdarg.h>


uint8_t HC_RxData;
uint8_t HC_RxFlag;
uint8_t HC_RxPacket[4];
uint8_t HC_TxPacket[4];
uint8_t Car_mode=0,Car_stop=0,Car_quan=0;


/****蓝牙数据配置意义****/
void HC_Init(void)
	{	//TX:B10	RX:B11
	RCC_APB1PeriphClockCmd (RCC_APB1Periph_USART3,ENABLE);//开时钟
	RCC_APB2PeriphClockCmd (RCC_APB2Periph_GPIOB,ENABLE);
	GPIO_InitTypeDef GPIO_InitStructure;
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_AF_PP;//TX为输出脚，复用推挽输出；RX为输入模式；
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_10;
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOB,&GPIO_InitStructure);
	
	GPIO_InitStructure.GPIO_Mode=GPIO_Mode_IPU;//TX为输出脚，复用推挽输出；RX为输入模式,上拉输入；GPIO_Mode_IN_FLOATING浮空
	GPIO_InitStructure.GPIO_Pin=GPIO_Pin_11;
	GPIO_InitStructure.GPIO_Speed=GPIO_Speed_50MHz;
	GPIO_Init(GPIOB,&GPIO_InitStructure);
	
	USART_InitTypeDef USART_InitStructure;
	USART_InitStructure.USART_BaudRate=115200;//波特率
	USART_InitStructure.USART_HardwareFlowControl=USART_HardwareFlowControl_None;//流控
	USART_InitStructure.USART_Mode=USART_Mode_Tx|USART_Mode_Rx;//模式，发送或接收
	USART_InitStructure.USART_Parity=USART_Parity_No;//校验位
	USART_InitStructure.USART_StopBits=USART_StopBits_1;//停止位
	USART_InitStructure.USART_WordLength=USART_WordLength_8b;//字长
	USART_Init(USART3 ,&USART_InitStructure);//串口3初始化
	
	//把接收放在中断里
	USART_ITConfig(USART3 ,USART_IT_RXNE,ENABLE);
	NVIC_PriorityGroupConfig(NVIC_PriorityGroup_2);//通道
	NVIC_InitTypeDef NVIC_InitStructure;//初始化
	NVIC_InitStructure.NVIC_IRQChannel=USART3_IRQn;
	NVIC_InitStructure.NVIC_IRQChannelCmd=ENABLE ;
	NVIC_InitStructure.NVIC_IRQChannelPreemptionPriority=2;
	NVIC_InitStructure.NVIC_IRQChannelSubPriority=2;
	NVIC_Init(&NVIC_InitStructure);
	
	
	USART_Cmd (USART3 ,ENABLE);

}

void Uart3_Serial_SendByte(uint8_t Byte)//Byte可以是单引号里的字符
{
	USART_SendData(USART3 ,Byte);//写入数据到寄存器
	while(USART_GetFlagStatus (USART3 ,USART_FLAG_TXE)==RESET);//读取标志位，判断完成写入,不需手动清零
	
}

void Serial_SendArray(uint8_t *Array,uint16_t Length)//发送一个数组
{
	uint16_t i;
	for(i=0;i<Length ;i++)
	{
		Uart3_Serial_SendByte(Array [i]);
	}
}

void Serial_SendString(char *String)//发送一个字符串
{
	uint8_t i;
	for(i=0;String [i]!='\0' ;i++)
	{
		Uart3_Serial_SendByte(String [i]);
	}
}

uint32_t Serial_Pow(uint32_t x, uint32_t y)
{
	uint32_t Result=1;
	while(y--)
	{
		Result *=x;
	}
	return Result ;
}

void Uart3_Serial_SendNum(uint32_t Number,uint8_t Length)//发送数字,数字拆开，一位一位的发
{
	uint8_t i;
	for(i=0;i<Length ;i++)
	{
		Uart3_Serial_SendByte(Number/Serial_Pow(10,Length -i-1)%10+'0');
	}

}
	


//数据包发送
void Serial_SendPacket(void)
{
	Uart3_Serial_SendByte(0xFF);//头
	Serial_SendArray(HC_TxPacket,4);
	Uart3_Serial_SendByte(0xFE);//尾

}


uint8_t Serial_GetRxFlag(void)//人工的读取标志位后清除函数
{
	if(HC_RxFlag==1)
	{
		HC_RxFlag=0;
		return 1;
	}
	return 0;

}

void HC_SendData(void)
{
		HC_TxPacket[0]=Car_mode;
		HC_TxPacket[1]=Car_stop;
		HC_TxPacket[2]=Car_quan;
		Serial_SendPacket();
}
	

void HC_GetData(void)
{
	if(Serial_GetRxFlag()==1)//如果数据包接收完成
	{
		Car_mode=HC_RxPacket[0];
		Car_stop=HC_RxPacket[1];
		Car_quan=HC_RxPacket[2];

	}

}

//void USART3_IRQHandler(void)
//{
//	static uint8_t RxState=0;//状态机
//	static uint8_t pRxState=0;//指示接收个数
//	if(USART_GetITStatus(USART3 ,USART_IT_RXNE)==SET)
//	{
//		uint8_t RxData=USART_ReceiveData(USART3);
//		if(RxState==0)	
//		{
//			if(RxData==0xFF&&HC_RxFlag==0)//用这个的话就要给Serial_RxFlag手动清零
//			{
//				RxState=1;
//				pRxState=0;
//			}
//		}
//		else if(RxState==1)	
//		{
//			HC_RxPacket[pRxState]=RxData;
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
//				HC_RxFlag=1;
//				HC_GetData();
//			}
//		}
//	
//		USART_ClearITPendingBit(USART3,USART_IT_RXNE);
//	}

//}

//n//

int fputc(int ch,FILE *f)//打印函数原型重定向到串口
{
	Uart3_Serial_SendByte(ch);
	return ch;
	
}

//对sprinttf进行封装（可变参数）
void Serial_Printf(char *format,...)
{
	char String[100];
	va_list arg;
	va_start (arg,format);
	vsprintf (String ,format,arg);
	va_end(arg);
	Serial_SendString(String);
}
