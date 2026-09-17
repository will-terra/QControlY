# QControlY

QControlY é um aplicativo desktop multiplataforma (Windows, macOS, Linux) para gerenciar fones de ouvido da linha QCY (H3, H3 Pro e H3S) via Bluetooth Low Energy (BLE).

O projeto é estruturado em camadas bem definidas e utiliza `bleak` para a comunicação Bluetooth e `PySide6` para a interface gráfica.

## Requisitos

- Python 3.10 ou superior.
- Adaptador Bluetooth compatível com Bluetooth Low Energy (BLE).

## Como Instalar

Recomenda-se o uso de um ambiente virtual para gerenciar as dependências isoladamente.

1. Navegue até o diretório do projeto:
   ```bash
   cd QControlY
   ```

2. Crie e ative um ambiente virtual (opcional, mas recomendado):
   ```bash
   python -m venv .venv
   
   # Linux/macOS
   source .venv/bin/activate  
   
   # Windows
   .venv\Scripts\activate
   ```

3. Instale o projeto e as dependências básicas:
   ```bash
   pip install -e .
   ```
   
   *Nota: Caso deseje contribuir para o projeto ou rodar testes, instale com as dependências de desenvolvimento:*
   ```bash
   pip install -e ".[dev]"
   ```

## Como Iniciar

Após a instalação, o executável do projeto ficará disponível no seu terminal. Para iniciar o aplicativo, basta rodar:

```bash
qcy-h3
```

*Nota: O aplicativo inicia uma interface gráfica, incluindo um ícone na bandeja do sistema (system tray) para fácil acesso.*

## Executando os Testes

O projeto utiliza a biblioteca `pytest` para testes (rodando independentemente da conexão com o fone). Com as dependências de desenvolvimento instaladas, execute:

```bash
pytest
```

## Estrutura do Código

- `src/qcontroly/core/`: Lógica principal e codec de protocolo (modelos, comandos e codificação de quadros). Independente de I/O e UI.
- `src/qcontroly/ble/`: Integração Bluetooth GATT utilizando a biblioteca `bleak` (cliente de conexão e escaneamento).
- `src/qcontroly/ui/`: Interface com o usuário (PySide6), incluindo `main_window`, integração de System Tray e controle de threads (workers) para chamadas assíncronas BLE.
