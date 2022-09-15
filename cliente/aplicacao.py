#####################################################
# Camada Física da Computação
#Carareto
#11/08/2022
#Aplicação
####################################################


#esta é a camada superior, de aplicação do seu software de comunicação serial UART.
#para acompanhar a execução e identificar erros, construa prints ao longo do código! 


from enlace import *
import time
import numpy as np
import random
import threading

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

#use uma das 3 opcoes para atribuir à variável a porta usada
serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)
#serialName = "COM11"                  # Windows(variacao de)


def espera_resposta(com1, start_time, tamanho, esperando):
    while time.process_time() - start_time < 5:
        if not com1.rx.getIsEmpty():
            rxBuffer , _ = com1.getData(tamanho)
            print(rxBuffer)
            print(esperando)
            if rxBuffer == esperando:
                print("A mensagem foi enviada com sucesso")
                return True
            else:
                print("Erro de interpretacao")
                com1.disable()
                return False
    print("Erro de timeout")
    return False

def handshake(com1, start_time):
    while(True):
        start_time = time.process_time()
        txBuffer = b'\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF'
        print(txBuffer)
        com1.sendData(np.asarray(txBuffer))
        print("Handshake enviado, esperando resposta")
        handshake_respondido = espera_resposta(com1, start_time, 14, b'\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\xFF\xFF\xFF\xFF')
        if (handshake_respondido):
            print("Handshake respondido")
            return True
        else:
            print("Handshake não respondido")
            while(True):
                continuar = input("Quer continuar? S/n")
                if continuar == "S":
                    break
                elif continuar == "n":
                    return False
                else:
                    print("Input invalido")

def divide_pacotes(mensagem):
    pacotes = []
    pacote = b''
    for byte in mensagem:
        if len(pacote) < 114:
            pacote += byte
        else:
            pacotes.append(pacote)
            pacote = b''
    pacotes.append(pacote)
    return pacotes
    
    

def monta_datagrama(payload, payloads, i):
    header = b'\x02' + len(payload).to_bytes(1, 'big') + len(payloads).to_bytes(1, 'big') +  b'\x05' + b'\x00'*6 #fora de ordem
    header = b'\x02' + len(payload).to_bytes(1, 'big') + len(payloads).to_bytes(1, 'big') +  i.to_bytes(1, 'big') + b'\x00'*6
    payload = b'\x00\x00'
    EOP = b'\xAA\xBB\xCC\xDD'
    package = header
    package += payload
    package += EOP
    return  package

def main():
    

    #handshake = x00
    #handshake acknowledge = x01
    #conteudo = x02
    #recebido = x03
    #final = x04
    #erro = x05
    print("Iniciou o main")
    #declaramos um objeto do tipo enlace com o nome "com". Essa é a camada inferior à aplicação. Observe que um parametro
    #para declarar esse objeto é o nome da porta.
    com1 = enlace(serialName)
    

    # Ativa comunicacao. Inicia os threads e a comunicação seiral 
    com1.enable()
    #Se chegamos até aqui, a comunicação foi aberta com sucesso. Faça um print para informar.
    print(f"{len([0])}")
        
    txSize = com1.tx.getStatus()
    
    start_time = time.process_time()
    ouve_handshake = handshake(com1, start_time)
    print("fim do handshake")
    mensagem = [b'\x00']*1000
    if ouve_handshake:
        print("payloads")
        payloads = divide_pacotes(mensagem)
        for i in range(len(payloads)):
            datagrama = monta_datagrama(payloads[i], payloads, i)
            com1.sendData(np.asarray(datagrama))
            start_time = time.process_time()
            esperando = b'\x03' + len(payloads[i]).to_bytes(1, 'big') + len(payloads).to_bytes(1, 'big') + i.to_bytes(1, 'big') + b'\x00'*6 + b'\xFF'*4
            teve_resposta = espera_resposta(com1, start_time, 14, esperando)
            if not teve_resposta:
                print("ERRO, COMUNICACAO ENCERRADA PREMATURAMENTE")
                com1.disable()
                break
    print("Comunicação encerrada")
    com1.disable()
    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
