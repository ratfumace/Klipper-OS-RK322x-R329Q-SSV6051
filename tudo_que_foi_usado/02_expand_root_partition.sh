#!/bin/bash
# Script para expandir a partição de 4GB para 8GB (capacidade real) na TV Box com chip RK NAND.
# AVISO: Operação de risco no armazenamento raiz. Apenas execute caso o disco não esteja particionado para 8GB.

echo "Instalando ferramenta gdisk..."
apt-get update && apt-get install -y gdisk

echo "Movendo backup GPT para o final do disco..."
sgdisk -e /dev/rknand0

echo "Recriando particao 1 com tamanho total a partir do setor 32768..."
sgdisk -d 1 -n 1:32768:0 /dev/rknand0

echo "Tentando atualizar a tabela no kernel..."
partprobe /dev/rknand0 || true

echo "Expandindo filesystem..."
resize2fs /dev/rknand0p1

echo "Concluido! O tamanho novo deve ser de 7.3GB:"
df -h /
