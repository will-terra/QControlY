"""Identificadores GATT dos fones QCY H3 / H3 Pro / H3S.

Valores confirmados via captura btsnoop_hci.log (Wireshark, filtro btatt).
"""

# Serviço proprietário (anúncio BLE)
QCY_SERVICE = "0000a002-0000-1000-8000-00805f9b34fb"

# Características do serviço a002
QCY_WRITE = "00000001-0000-1000-8000-00805f9b34fb"    # app → fone (Command)
QCY_NOTIFY = "00000002-0000-1000-8000-00805f9b34fb"   # fone → app (Notification)

# Aliases semânticos (todas usam a mesma characteristic no H3S)
QCY_EQUALIZER = QCY_WRITE
QCY_BATTERY = QCY_WRITE

# Serviço Generic Access (0x1800)
GATT_DEVICE_NAME = "00002a00-0000-1000-8000-00805f9b34fb"

# Substrings de nome para identificar fones da série H3
NAME_MATCH = ("H3",)
