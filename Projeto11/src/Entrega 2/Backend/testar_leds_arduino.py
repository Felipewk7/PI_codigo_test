"""
Script de Teste Interativo dos 12 LEDs do Painel IoT Arduino (TenniSync)
Permite ao usuário escolher exatamente qual LED acender individualmente para identificar
e validar cada articulação e pino da placa.
"""

import sys
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from arduino_utils import connect_arduino

# Mapeamento oficial dos 12 LEDs anatômicos
LEDS = [
    (1,  'A', 2,  'Ombro Direito'),
    (2,  'B', 3,  'Ombro Esquerdo'),
    (3,  'C', 4,  'Cotovelo Direito'),
    (4,  'D', 5,  'Cotovelo Esquerdo'),
    (5,  'E', 6,  'Punho Direito'),
    (6,  'F', 7,  'Punho Esquerdo'),
    (7,  'G', 8,  'Quadril Direito'),
    (8,  'H', 9,  'Quadril Esquerdo'),
    (9,  'I', 10, 'Joelho Direito'),
    (10, 'J', 11, 'Joelho Esquerdo'),
    (11, 'K', 12, 'Tornozelo Direito'),
    (12, 'L', 13, 'Tornozelo Esquerdo'),
]

MAPA_NUMERO = {num: (cmd, pino, nome) for num, cmd, pino, nome in LEDS}

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def imprimir_menu(porta, status_atual=""):
    print("=" * 68)
    print("      TENNISSYNC - TESTE INTERATIVO DOS 12 LEDs (ARDUINO)")
    print("=" * 68)
    print(f" Status: Conectado na porta [{porta}]")
    if status_atual:
        print(f" Estado: {status_atual}")
    print("-" * 68)
    print(" ESCOLHA O LED QUE DESEJA ACENDER:")
    print(" -------------------------------------------------------------------")
    for num, cmd, pino, nome in LEDS:
        print(f"  [{num:2d}] {nome:<20} -> Pino {pino:2d} no Arduino (Byte '{cmd}')")
    print("-" * 68)
    print(" COMANDOS ESPECIAIS:")
    print("  [T]  Testar TODOS em sequência (Passo a passo automático)")
    print("  [A]  Acender TODOS os 12 juntos")
    print("  [R]  Apagar TODOS os LEDs")
    print("  [S]  Sair do programa")
    print("=" * 68)

def main():
    limpar_tela()
    print("=" * 68)
    print("      TENNISSYNC - TESTE INTERATIVO DOS 12 LEDs (ARDUINO)")
    print("=" * 68)
    print("\nProcurando conexão com o Arduino...")

    ser = None
    port = None

    while ser is None:
        ser, port = connect_arduino("auto")
        if ser is None:
            print("\n[AVISO] Nenhum Arduino detectado nas portas USB.")
            resp = input("Conecte o cabo USB do Arduino e aperte ENTER para tentar de novo (ou 'S' para sair): ").strip().upper()
            if resp == 'S':
                print("Encerrando.")
                return
            print("Tentando reconectar...")
            time.sleep(1)

    # Inicia com tudo apagado
    try:
        ser.write(b'R')
    except Exception:
        pass

    status = "Pronto. Digite o número do LED desejado."

    while True:
        limpar_tela()
        imprimir_menu(port, status)

        try:
            escolha = input("\nDigite o número (1 a 12) ou comando [T/A/R/S] e aperte ENTER: ").strip().upper()
        except (KeyboardInterrupt, EOFError):
            break

        if not escolha:
            continue

        if escolha in ['S', 'SAIR', '0', 'Q']:
            print("\nApagando LEDs e encerrando teste...")
            try:
                ser.write(b'R')
                ser.close()
            except Exception:
                pass
            print("Até logo!")
            break

        elif escolha == 'R':
            try:
                ser.write(b'R')
                status = "Todos os LEDs foram APAGADOS."
            except Exception as e:
                status = f"Erro ao enviar comando: {e}"

        elif escolha == 'A':
            try:
                payload = bytearray([ord('R')] + [ord(cmd) for _, cmd, _, _ in LEDS])
                ser.write(payload)
                status = "TODOS os 12 LEDs foram ACESOS simultaneamente!"
            except Exception as e:
                status = f"Erro ao enviar comando: {e}"

        elif escolha == 'T':
            limpar_tela()
            print("=" * 68)
            print("   INICIANDO TESTE SEQUENCIAL AUTOMÁTICO DE CADA UM DOS 12 LEDs")
            print("=" * 68)
            try:
                ser.write(b'R')
                time.sleep(0.3)
                for num, cmd, pino, nome in LEDS:
                    print(f"  -> Acendendo [{num:2d}] {nome:<18} (Pino {pino:2d} | Byte '{cmd}')...")
                    ser.write(b'R')
                    ser.write(cmd.encode('ascii'))
                    time.sleep(0.8)
                ser.write(b'R')
                status = "Teste sequencial automático concluído com sucesso!"
            except Exception as e:
                status = f"Erro durante o teste sequencial: {e}"

        elif escolha.isdigit():
            num = int(escolha)
            if num in MAPA_NUMERO:
                cmd, pino, nome = MAPA_NUMERO[num]
                try:
                    # Apaga anterior e acende exclusivamente o LED escolhido
                    payload = bytearray([ord('R'), ord(cmd)])
                    ser.write(payload)
                    status = f"ACESO -> [{num}] {nome} (Pino {pino} no Arduino | Byte '{cmd}')"
                except Exception as e:
                    status = f"Erro ao comunicar com Arduino: {e}"
            else:
                status = f"Opção inválida ({num}). Digite um número de 1 a 12."
        else:
            status = f"Comando '{escolha}' não reconhecido. Digite de 1 a 12, T, A, R ou S."

if __name__ == "__main__":
    main()
