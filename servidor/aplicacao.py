from webbrowser import get
from enlace import *
import time
import numpy as np


# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

#use uma das 3 opcoes para atribuir à variável a porta usada
#serialName = "/dev/ttyACM0"           # Ubuntu (variacao de)
#serialName = "/dev/tty.usbmodem1411" # Mac    (variacao de)
serialName = "COM3"                  # Windows(variacao de)

EOP = b'\xAA\xBB\xCC\xDD'
# número do servidor -> 1


def get_data(com1 : enlace, size):
    if com1.rx.getBufferLen() >= size:
        data, _ = com1.getData(size)
        return data


def monta_pacote(
    h0=b'\x00', h1=b'\x00', h2=b'\x00', h3=b'\x00', h4=b'\x00',
    h5=b'\x00', h6=b'\x00', h7=b'\x00', h8=b'\x00', h9=b'\x00',
):
    return h0 + h1 + h2 + h3 + h4 + h5 + h6 + h7 + h8 + h9 + EOP


def main():
    try:
        print("Iniciou o main")
        com1 = enlace(serialName)
        com1.enable()
        com1.rx.clearBuffer()

        numero_do_pacote = 0
        dados_recebidos = b''
        pacote_enviado = None
        total_de_pacotes = None
        timer1 = time.process_time()
        timer2 = time.process_time()
        manda = False
        while (time.process_time() - timer2 < 20):
            while time.process_time() - timer1 < 5:
                if manda:
                    manda = False
                    print(f'numero do pacote: {numero_do_pacote}')
                    print(f'pacote enviado: {pacote_enviado}')
                    timer1 = time.process_time()
                    if pacote_enviado is not None:
                        com1.sendData(pacote_enviado)
                    else:
                        com1.rx.clearBuffer()
                    if total_de_pacotes is not None and (numero_do_pacote == int.from_bytes(total_de_pacotes, 'big')):
                        com1.disable()
                        return f'Transmissão encerrada {dados_recebidos} {len(dados_recebidos)}'
        
                if not com1.rx.getIsEmpty():
                    print('iniciando leitura')
                    ultimo_pacote_recebido = int.to_bytes(numero_do_pacote + 1, 1, 'big')

                    # lendo head
                    head = get_data(com1, 10)
                    print(f'head {head}')
                    if (head is None):
                        print('pacote incompleto recebido')
                        break
                    h0 = head[0:1]
                    h3 = head[3:4]
                    h4 = head[4:5]
                    h5 = head[5:6]
                    if ultimo_pacote_recebido != h4:
                        # mensagem de erro pacote errado recebido
                        pacote_enviado = monta_pacote(h0=b'\x06', h6=ultimo_pacote_recebido)
                        pass

                    if h0 == b'\x11':
                        # handshake
                        id_do_arquivo = h5
                        total_de_pacotes = h3
                        if get_data(com1, 4) != EOP:
                            print('pacote incompleto recebido')
                            com1.rx.clearBuffer()
                            break
                        pacote_enviado = monta_pacote(h0=b'\x02', h3=total_de_pacotes, h5=id_do_arquivo)
                        manda = True
                        continue
                    elif h0 == b'\x03':
                        # conteúdo
                        payload_len = int.from_bytes(h5, 'big')
                        print(com1.rx.getBufferLen(), 'buffer len')
                        payload = get_data(com1, payload_len)
                        print(f'payload {payload} {payload_len}')
                        if get_data(com1, 4) != EOP:
                            # pacote incompleto recebido
                            pacote_enviado = monta_pacote(h0=b'\x06', h3=total_de_pacotes, h5=id_do_arquivo, h6=ultimo_pacote_recebido)
                            break
                        dados_recebidos += payload
                        
                        pacote_enviado = monta_pacote(h0=b'\x04', h3=total_de_pacotes, h7=ultimo_pacote_recebido)
                        timer1 = time.process_time()
                        timer2 = time.process_time()
                        numero_do_pacote += 1
                        print(f'total de pacotes / núemro do pacote')
                        print(int.from_bytes(total_de_pacotes, 'big'), numero_do_pacote)
                        manda = True
                        continue
                    elif h0 == b'\x05':
                        # timeout
                        com1.disable()
                        return 'Erro de timeout'
                    com1.rx.clearBuffer()
            else:
                print(f'numero do pacote: {numero_do_pacote}')
                print(f'pacote enviado: {pacote_enviado}')
                timer1 = time.process_time()
                if pacote_enviado is not None:
                    com1.sendData(pacote_enviado)
                if total_de_pacotes is not None and (numero_do_pacote == int.from_bytes(total_de_pacotes, 'big')):
                    com1.disable()
                    return f'Transmissão encerrada {dados_recebidos} {len(dados_recebidos)}'
        com1.disable()
        return 'Erro de timeout'





        # Encerra comunicação
        print("-------------------------")
        print("Comunicação encerrada")
        print("-------------------------")
        com1.disable()

    except Exception as e:
        com1.disable()
        print(f"{type(e).__name__} at line {e.__traceback__.tb_lineno} of {__file__}: {e}")
        return e
        

if __name__ == "__main__":
    print("-------------------------")
    print(main())
    print("-------------------------")
