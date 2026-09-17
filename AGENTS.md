# QControlY — contexto do projeto

App desktop multiplataforma (Win/macOS/Linux) para gerenciar fones QCY H3, H3 Pro e H3S via BLE.

## Stack
- Python 3.10+, bleak (BLE), PySide6 (UI), pytest
- Arquitetura em camadas: core (puro, sem I/O) / ble (adaptador bleak) / ui (Qt)

## Estrutura
- `src/qcyh3/core/protocol.py` — codec de quadros (SOP/LEN/CMD/PAYLOAD/EOF)
- `src/qcyh3/core/commands.py` — tabela de opcodes (confirmados via btsnoop_hci.log)
- `src/qcyh3/core/model.py` — modelos de domínio (AncMode, EqPreset, DeviceState, DeviceInfo)
- `src/qcyh3/ble/uuids.py` — UUIDs GATT (confirmados via btsnoop_hci.log)
- `src/qcyh3/ble/client.py` — conexão GATT, write, notify
- `src/qcyh3/ble/scanner.py` — descoberta de dispositivos QCY
- `src/qcyh3/ui/main_window.py` — janela principal PySide6 com system tray
- `src/qcyh3/ui/worker.py` — thread BLE com ponte Qt↔asyncio
- `tests/` — testes do codec, rodam sem fone

## Comandos
- Instalar: `pip install -e ".[dev]"`
- Testes: `pytest`
- Rodar app: `qcy-h3`

## Regras
- `core/` nunca importa bleak/PySide6 — mantenha puro e testável.
- Mudanças de protocolo nunca tocam `ui/`; mudanças de UI nunca tocam `core/protocol.py`.
- Todo comando/opcode confirmado deve vir com comentário citando a fonte (captura btsnoop).
- Antes de concluir qualquer tarefa: `pytest` deve passar.

## Engenharia reversa (contexto)
O protocolo é BLE GATT proprietário: app oficial → characteristic write (comandos),
fone → notify (respostas). Para descobrir opcodes não mapeados:
capturar com HCI snoop no Android e abrir no Wireshark (filtro btatt).
