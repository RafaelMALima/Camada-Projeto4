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


def espera_resposta(com1, start_time, tamanho, esperando, tempo_espera):
    while time.process_time() - start_time < tempo_espera:
        if not com1.rx.getIsEmpty():
            rxBuffer , _ = com1.getData(tamanho)
            com1.rx.clearBuffer()
            print(rxBuffer)
            print(esperando)
            with open('logs/client4.txt' , 'a') as f:
                if int.from_bytes(rxBuffer[0:1], 'big') == 2:
                    f.write(f"{time.asctime(time.localtime(time.time()))}/receb/ {int.from_bytes(rxBuffer[0:1], 'big')} / {14} \n")
                else:
                    f.write(f"{time.asctime(time.localtime(time.time()))}/receb/ {int.from_bytes(rxBuffer[0:1], 'big')} / {14 + int.from_bytes(rxBuffer[5:6], 'big')} \n")
            if rxBuffer == esperando:
                print("A mensagem foi enviada com sucesso")
                return True, rxBuffer
            else:
                print("Erro de interpretacao")
                return True, rxBuffer
    return False, b'\x00'

def handshake(com1, start_time, total_packs):
    while(True):
        start_time = time.process_time()
        txBuffer = b'\x11\x00\x00' + total_packs.to_bytes(1, 'big') + b'\x00\x11\x00\x00\x00\x00\xAA\xBB\xCC\xDD'
        print(np.asarray(txBuffer))
        com1.sendData(np.asarray(txBuffer))
        with open('logs/client4.txt', 'a') as f:
            f.write(f"{time.asctime(time.localtime(time.time()))}/envia/ 1 / 14 \n")

        timer_handshake = time.process_time()
        print("Handshake enviado, esperando resposta")
        handshake_respondido, response = espera_resposta(com1, start_time, 14, b'\x02\x00\x00' +total_packs.to_bytes(1, 'big') + b'\x00\x11\x00\x00\x00\x00\xAA\xBB\xCC\xDD', 5)
        if (handshake_respondido and response == b'\x02\x00\x00' +total_packs.to_bytes(1, 'big') + b'\x00\x11\x00\x00\x00\x00\xAA\xBB\xCC\xDD'):
            print("Handshake respondido")
            return True

def divide_pacotes(mensagem):
    pacotes = []
    pacote = b''
    i = 0
    for byte in mensagem:
        if len(pacote) < 114:
            pacote += byte
        else:
            pacotes.append(pacote)
            pacote = byte
    pacotes.append(pacote)
    print(i)
    return pacotes
    
    

def monta_datagrama_conteudo(payload, payloads, i):
    header = b'\x03\x00\x00' + len(payloads).to_bytes(1, 'big') +  i.to_bytes(1, 'big') + len(payload).to_bytes(1, 'big') + b'\x00'*4
    EOP = b'\xAA\xBB\xCC\xDD'
    package = header
    package += payload
    package += EOP
    return  package

def main():
    

    print("Iniciou o main")
    #declaramos um objeto do tipo enlace com o nome "com". Essa é a camada inferior à aplicação. Observe que um parametro
    #para declarar esse objeto é o nome da porta.
    com1 = enlace(serialName)
    

    # Ativa comunicacao. Inicia os threads e a comunicação seiral 
    com1.enable()
    com1.rx.clearBuffer()
    mensagem = [b'\x00']*1000
    payloads = divide_pacotes(mensagem)
        
    txSize = com1.tx.getStatus()
    
    start_time = time.process_time()
    houve_handshake = handshake(com1, start_time, len(payloads))
    print("fim do handshake")
    cont = 1
    if houve_handshake:
        while cont < len(payloads)+1:
            datagrama = monta_datagrama_conteudo(payloads[cont - 1], payloads, cont)
            print(f"datagrama:{datagrama}")
            com1.sendData(np.asarray(datagrama))
            with open('logs/client4.txt', 'a') as f:
                f.write(f"{time.asctime(time.localtime(time.time()))}/envia/ {int.from_bytes(datagrama[0:1], 'big')} / {14 + int.from_bytes(datagrama[5:6], 'big')} / {cont} / {len(payloads)}\n")

            timer1 = time.process_time()
            timer2 = time.process_time()
            esperando = b'\x04\x00\x00'+len(payloads).to_bytes(1,'big') + b'\x00\x00\x00' + cont.to_bytes(1,'big') + b'\x00'*2 +  b'\xAA\xBB\xCC\xDD'
            sends = 1
            while time.process_time() - timer2 < 20:
                recebeu_resposta, resposta = espera_resposta(com1, timer1, 14, esperando, 5)
                if recebeu_resposta:
                    cont += 1
                    break
                if time.process_time() - timer1 > 5:
                    timer1 = time.process_time()
            if recebeu_resposta:
                if resposta[:1] == b'\x06':
                    cont = int.from_bytes(resposta[6:7], 'big')
                if resposta[:1] == b'\x04':
                    pass
                if resposta[:1] == b'\x05':
                    print('ERRO 5 DO SERVIDOR, ENCERRANDO COMUNICACAO')
                    com1.disable()
                    quit()
            elif resposta[:1] == b'\x00':
                header_fim = b'\x05' + b'\x00'*9
                mensagem_encerramento = header_fim + b'\xAA\xBB\xCC\xDD'
                com1.sendData(mensagem_encerramento)
                print("TIMEOUT CRITICO, ENCERRANDO COMUNICACAO")
                with open('logs/client4.txt', 'a') as f:
                    f.write(f"{time.asctime(time.localtime(time.time()))}/envia/ {int.from_bytes(mensagem_encerramento[0:1], 'big')} / 14 \n")
                com1.disable()
                quit()
                
                    
                
    print("Comunicação encerrada")
    com1.disable()
    #so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()