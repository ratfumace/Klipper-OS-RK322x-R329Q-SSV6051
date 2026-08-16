====================================================================
PASTA COMPLETA DE RECURSOS E BACKUPS - ENDER 3 V3 SE (FORK 0xD34D)
====================================================================

Data de Criacao: 04/08/2026
Impressora: Creality Ender 3 V3 SE
Placa Principal: Creality CR4NS200320C14
Microcontrolador (MCU): STM32F401RET6 (512 KiB Flash, 96 KiB RAM)
Sistema Host: TV Box Debian ARMv7
Repositorio Klipper Utilizado: https://github.com/0xD34D/klipper_ender3_v3_se
Commit do Fork: 4efbf462f902518cbac8cff3169e73535408651f

--------------------------------------------------------------------
1. CONTEUDO DA PASTA /firmware_mcu_gravado/
--------------------------------------------------------------------
- klipper-ender3v3se-c14-f401-0xd34d.bin: Binario compilado do Klipper gravado na flash da impressora.
  * Tamanho: 40736 bytes
  * SHA-256: 27aa75c690b547a95a375d5f57cff31c851063e1ab4e5b24956b97afa9f59339
  * Endereco Base de Execucao: 0x08000000
  * Frequencia da CPU: 84 MHz (Clock de referencia externo 8 MHz)
  * Comunicacao: USART1 (TX: PA9, RX: PA10), Baud Rate: 250000
- klipper-ender3v3se-c14-f401-0xd34d.elf: Arquivo ELF com tabela de simbolos para depuracao.
- klipper-ender3v3se-c14-f401-0xd34d.config: Arquivo de configuracao de compilacao (.config).

--------------------------------------------------------------------
2. CONTEUDO DA PASTA /configuracao_klipper/
--------------------------------------------------------------------
- printer.cfg: Arquivo de configuracao principal do Klipper.
- prtouch.cfg: Configuracao dos chips de sensor de peso HX711, dirzctl e prtouch.
- macro.cfg: Todas as macros personalizadas e otimizadas (PREHEAT_ABS, SECAR_ABS5, etc.).
- mainsail.cfg: Configuracoes de interface do Mainsail/Fluidd.
- prtouch.py.patched: Modulo de codigo em Python contendo o patch corrigido na linha 418.

--------------------------------------------------------------------
3. CONTEUDO DA PASTA /backup_flash_fabrica/
--------------------------------------------------------------------
- flash_original_512k_c14.bin: Backup binario completo de 512 KiB da flash original da placa C14 lido diretamente via ST-Link V2 por SWD.
  * SHA-256 Validado: 733d187732f6be6ca6deb28703f912b7571ca5faa5f629160d19db1506dec21e
