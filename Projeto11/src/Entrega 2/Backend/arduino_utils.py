"""
Módulo de Gerenciamento e Detecção Automática de Portas Serial do Arduino (TenniSync)
Detecta dinamicamente a porta COM onde o Arduino está conectado (incluindo clones com chip CH340, FTDI, CP210x ou oficiais).
"""

import os
import sys
import time

try:
    from logger import log_info, log_warn, log_error, log_debug
except ImportError:
    try:
        from Backend.logger import log_info, log_warn, log_error, log_debug
    except ImportError:
        def log_info(tag, msg, extra=None): print(f"[INFO][{tag}] {msg}")
        def log_warn(tag, msg, extra=None): print(f"[WARN][{tag}] {msg}")
        def log_error(tag, msg, extra=None): print(f"[ERROR][{tag}] {msg}")
        def log_debug(tag, msg, extra=None): pass

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    serial = None
    HAS_SERIAL = False

# VIDs conhecidos de placas microcontroladoras compatíveis com Arduino
KNOWN_ARDUINO_VIDS = {
    0x2341,  # Arduino SA (Uno, Mega, Leonardo, Nano, etc.)
    0x2A03,  # Arduino.org
    0x1A86,  # QinHeng Electronics (CH340 / CH341 - clones Arduino Uno muito comuns)
    0x0403,  # FTDI (FT232R)
    0x10C4,  # Silicon Labs (CP210x)
    0x067B,  # Prolific (PL2303)
    0x1B4F,  # SparkFun
    0x2E8A,  # Raspberry Pi (Pico)
    0x303A,  # Espressif (ESP32)
}

# Palavras-chave que indicam dispositivos válidos
VALID_KEYWORDS = [
    "arduino",
    "ch340",
    "ch341",
    "ftdi",
    "cp210",
    "usb-serial",
    "usb serial",
    "wch"
]

# Termos que devem ser categoricamente ignorados (ex: portas Bluetooth causam travamento)
BLACKLIST_TERMS = [
    "bluetooth",
    "bth",
    "link bluetooth"
]

def list_candidate_ports():
    """
    Lista portas seriais candidatas filtrando conexões Bluetooth e portas inválidas.
    Retorna lista de tuplas: (port_device, score, description)
    onde maior score indica maior probabilidade de ser o Arduino.
    """
    if not HAS_SERIAL:
        return []

    candidates = []
    try:
        ports = serial.tools.list_ports.comports()
    except Exception as e:
        log_warn("ARDUINO", f"Falha ao enumerar portas COM: {e}")
        return []

    for p in ports:
        desc_lower = (p.description or "").lower()
        hwid_lower = (p.hwid or "").lower()
        mfg_lower = (p.manufacturer or "").lower()

        # Ignora portas bluetooth
        if any(term in desc_lower or term in hwid_lower or term in mfg_lower for term in BLACKLIST_TERMS):
            continue

        score = 0
        # Checa VID conhecido
        if p.vid in KNOWN_ARDUINO_VIDS:
            score += 10

        # Checa palavras-chave na descrição ou HWID
        for kw in VALID_KEYWORDS:
            if kw in desc_lower or kw in hwid_lower or kw in mfg_lower:
                score += 5

        # Se for porta USB genérica, pontua levemente
        if "usb" in hwid_lower or "usb" in desc_lower:
            score += 2

        candidates.append((p.device, score, p.description or p.device))

    # Ordena pelo maior score primeiro
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates

def find_arduino_port(preferred_port=None):
    """
    Detecta automaticamente em qual porta COM o Arduino está conectado.
    Se preferred_port for informado (e não for 'auto' ou None), testa primeiro ela.
    """
    if not HAS_SERIAL:
        return None

    # 1. Se uma porta foi explicitada pelo usuário, testa se ela existe e abre
    if preferred_port and str(preferred_port).strip().upper() != "AUTO":
        port_name = str(preferred_port).upper().strip()
        try:
            test_ser = serial.Serial(port_name, 9600, timeout=0.2)
            test_ser.close()
            log_info("ARDUINO", f"Porta serial solicitada '{port_name}' confirmada e pronta.")
            return port_name
        except Exception:
            log_warn("ARDUINO", f"Porta solicitada '{port_name}' indisponível. Iniciando autodetecção dinâmica...")

    # 2. Busca entre as portas candidatas
    candidates = list_candidate_ports()
    if not candidates:
        log_warn("ARDUINO", "Nenhuma porta serial USB identificada no sistema.")
        return None

    # Testa abrir as portas candidatas ordenadas por relevância
    for port_device, score, desc in candidates:
        try:
            test_ser = serial.Serial(port_device, 9600, timeout=0.2)
            test_ser.close()
            log_info("ARDUINO", f"Arduino detectado com sucesso na porta {port_device} ({desc})!")
            return port_device
        except Exception as e:
            log_debug("ARDUINO", f"Não foi possível abrir porta candidata {port_device}: {e}")

    return None

def connect_arduino(preferred_port=None, baudrate=9600):
    """
    Tenta estabelecer conexão serial com o Arduino na porta detectada.
    Retorna uma tupla (serial_object, port_name) ou (None, None).
    """
    if not HAS_SERIAL:
        return None, None

    port = find_arduino_port(preferred_port)
    if not port:
        return None, None

    try:
        ser = serial.Serial(port, baudrate, timeout=0)
        time.sleep(0.05)
        # Envia reset de LEDs inicial ('R')
        try:
            ser.write(b'R')
        except Exception:
            pass
        return ser, port
    except Exception as e:
        log_error("ARDUINO", f"Erro ao conectar na porta detectada {port}: {e}")
        return None, None
