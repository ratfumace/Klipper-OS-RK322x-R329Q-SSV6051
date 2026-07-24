# Klipper OS RK322x — R329Q V8.0 / SSV6051

Sistema Linux preparado para transformar uma TV Box **R329Q V8.0**, baseada
nos processadores **Rockchip RK3228/RK3229**, em um controlador dedicado para
impressora 3D com Klipper.

> Este projeto é específico para a placa R329Q V8.0 com Wi-Fi SSV6051 2.4 GHz.
> Não grave a imagem em outra placa sem confirmar a compatibilidade do
> processador, armazenamento, DTB e módulo Wi-Fi.

## O que está incluído

- Linux ARMHF baseado em Debian 11/Armbian.
- Klipper e Moonraker instalados como serviços systemd.
- Mainsail como interface web principal.
- Fluidd instalado como alternativa selecionável pelo menu.
- Wi-Fi SSV6051 2.4 GHz e Ethernet.
- Detecção de controladoras por `/dev/ttyUSB*` e `/dev/ttyACM*`.
- Acesso SSH.
- Menu `config` para rede, interface web, MCU, serviços e senha.
- Tela inicial do terminal mostrando IP Ethernet e IP Wi-Fi.
- Terminal com destaque vermelho; a interface web mantém o tema original.
- Correção do reinício físico da TV Box por watchdog.

## Hardware alvo

| Componente | Especificação |
|---|---|
| Placa | R329Q V8.0 |
| Processador | Rockchip RK3228/RK3229 |
| Arquitetura | ARMHF |
| Wi-Fi | SSV6051 2.4 GHz |
| Kernel | 4.4.194-rk322x |
| Armazenamento | NAND/eMMC da TV Box |

## Downloads

As imagens não ficam dentro do histórico Git porque são arquivos muito
grandes. Baixe a versão desejada na seção **Releases** do GitHub.

### Multitool com Klipper OS — recomendado

Use esta opção para instalar o sistema na memória interna da TV Box. O
Multitool já contém a imagem compactada do Klipper OS.

Arquivo de distribuição:

`multitool_com_klipper_os_R329Q.rar`

### Imagem direta do Klipper OS

Use para gravar o sistema diretamente em um cartão ou para adicionar a imagem
manualmente à pasta `images` de um Multitool.

Arquivo:

`klipper_os_rk322x_R329Q_SSV6051.img.gz`

### Multitool vazio

Contém o Multitool sem nenhuma imagem dentro da pasta `images`. É útil para
adicionar outro sistema compatível posteriormente.

Arquivo de origem:

`multitool_sem_klipper_os_R329Q.img`

## Instalação na NAND

### Requisitos

- TV Box desligada e com placa R329Q V8.0.
- Cartão microSD de pelo menos 8 GB.
- Leitor de cartão.
- Programa capaz de gravar imagens brutas em cartões.
- Cabo Ethernet recomendado para a primeira inicialização.

### Passo a passo

1. Baixe o **Multitool com Klipper OS** na página de Releases.
2. Extraia o arquivo até obter
   `multitool_com_klipper_os_R329Q.img`.
3. Grave esse `.img` no cartão microSD. Não copie o arquivo para o cartão:
   use a opção de gravar/restaurar imagem do programa escolhido.
4. Com a TV Box desligada, coloque o cartão e inicialize pelo Multitool.
5. No menu do Multitool, selecione a função de gravar uma imagem na memória
   interna.
6. Escolha `klipper_os_rk322x_R329Q_SSV6051.img.gz`, que já está na pasta
   `images`.
7. Confirme a gravação e aguarde a conclusão sem desligar a TV Box.
8. Desligue o aparelho, retire o cartão e ligue novamente.
9. Aguarde a primeira inicialização. Conecte o cabo Ethernet para localizar o
   IP com facilidade.

> A gravação na NAND apaga o sistema anterior da TV Box. Faça backup antes se
> precisar preservar o conteúdo original.

## Primeiro acesso

Credenciais iniciais:

```text
Usuário: klipper
Senha:   123456
Root:    123456
```

Acesse por SSH:

```bash
ssh klipper@IP_DA_TV_BOX
```

Abra o menu de configuração:

```bash
config
```

No menu você pode configurar Wi-Fi, trocar as senhas de `klipper` e `root`,
selecionar Mainsail ou Fluidd, verificar serviços e selecionar a porta da MCU.

Troque a senha inicial depois do primeiro acesso.

## Interface web

Com o IP mostrado na tela inicial:

```text
Mainsail/Fluidd: http://IP_DA_TV_BOX
Moonraker API:   http://IP_DA_TV_BOX:7125
```

O Nginx é mantido porque publica Mainsail/Fluidd na porta 80. A interface web
usa o tema original; a personalização vermelha existe somente no terminal.

## Configuração da impressora

1. Conecte a placa da impressora à TV Box por USB.
2. Execute `config`.
3. Abra a opção de seleção da MCU e escolha a porta serial detectada.
4. Edite `printer.cfg` com a pinagem correta da sua impressora.
5. Reinicie o serviço Klipper pelo próprio menu.
6. Abra o Mainsail pelo navegador e confirme a comunicação com a MCU.

Cada modelo de impressora necessita de um `printer.cfg` próprio. Não inicie
movimentos ou aquecimento antes de validar pinos, termistores, limites de
temperatura, sentido dos motores e fins de curso.

## Wi-Fi SSV6051

A imagem usa:

```text
overlays=wlan-ssv6051 cpu-stability
```

O overlay `wlan-alt-wiring` não deve ser ativado nesta placa. Na R329Q V8.0
testada ele impedia a enumeração correta do módulo SDIO depois da instalação
na NAND.

## Reinício

O sistema possui um overlay e um gancho de desligamento para o watchdog
Rockchip. Assim, `sudo reboot` reinicia fisicamente a placa sem exigir que o
usuário desligue e ligue a fonte manualmente.

## Estado da versão

- Instalação na NAND: validada.
- Wi-Fi SSV6051: detectado e capaz de localizar redes.
- Ethernet e DHCP: validados.
- `sudo reboot`: validado em reinicializações consecutivas.
- Klipper, Moonraker, Mainsail, Fluidd e Nginx: ativos.
- Acesso SSH: validado.
- Senha inicial de `klipper` e `root`: validada.

O teste final com movimentos, aquecedores e sensores depende da impressora e
do arquivo `printer.cfg` utilizado.
