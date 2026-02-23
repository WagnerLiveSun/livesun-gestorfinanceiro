#!/bin/bash
# Script de inicialização do LiveSun Financeiro em Linux/Mac

echo ""
echo "========================================"
echo " LiveSun Financeiro - Inicializador"
echo "========================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Criando ambiente virtual..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Instalando dependências..."
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo ""
echo "Iniciando aplicação..."
echo ""
python run.py
