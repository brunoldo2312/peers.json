"""
verificar_github.py — BRN Ferramenta de Rede
Versão: 1.2 | Data: 29/09/2026
- Verifica status do peers.json
- Atualiza timestamp e altura (apenas com token configurado)
- Token carregado de forma segura
"""

import json
import time
import requests
import os
from base64 import b64encode

# ============================================================
# 🔧 CONFIGURAÇÕES
# ============================================================

USUARIO = "brunoldo2312"
REPOSITORIO = "peers.json"
ARQUIVO = "peers.json"
SEU_ENDERECO = "177.82.132.98:6001"
SEU_NODE_ID = "c6b06a40"
MAX_TOLERANCIA = 120  # 2 minutos

# Carrega token de forma segura (não fica no código)
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Tenta ler do arquivo .env se não estiver na variável de ambiente
if not GITHUB_TOKEN:
    try:
        with open(".env", "r", encoding="utf-8") as f:
            for linha in f:
                if linha.startswith("GITHUB_TOKEN="):
                    GITHUB_TOKEN = linha.strip().split("=", 1)[1]
                    break
    except FileNotFoundError:
        pass

# ============================================================
# 🔍 VERIFICAR STATUS
# ============================================================

def verificar_atualizacao():
    print("=" * 60)
    print("🔍 VERIFICAÇÃO — peers.json no GitHub")
    print("=" * 60 + "\n")
    
    PEERS_URL = f"https://raw.githubusercontent.com/{USUARIO}/{REPOSITORIO}/main/{ARQUIVO}"
    
    try:
        print("📡 Baixando arquivo do GitHub...")
        resp = requests.get(PEERS_URL, timeout=15)
        resp.raise_for_status()
        peers = resp.json()
        
        print(f"✅ Arquivo baixado — {len(peers)} nó(s) encontrado(s)\n")
        
        if SEU_ENDERECO not in peers:
            print(f"⚠️  {SEU_ENDERECO} não encontrado na lista")
            print(f"   Nós disponíveis: {list(peers.keys())}")
            return False
        
        dados = peers[SEU_ENDERECO]
        ts_github = dados.get("ts", 0)
        altura = dados.get("h", "?")
        node_id = dados.get("id", "???????")
        
        ts_atual = int(time.time())
        diferenca = ts_atual - ts_github
        
        print("📊 DADOS DO SEU NÓ:")
        print(f"   📍 Endereço:   {SEU_ENDERECO}")
        print(f"   🆔 Node ID:    {node_id}")
        print(f"   📦 Altura:     {altura}")
        print(f"   ⏱️  TS GitHub:  {ts_github}")
        print(f"   ⏱️  TS Atual:   {ts_atual}")
        print(f"   ⏱️  Diferença:  {diferenca} segundos ({diferenca/60:.1f} minutos)\n")
        
        if diferenca < MAX_TOLERANCIA:
            print("✅ ✅ ✅ ATUALIZADO! Tudo funcionando.")
            return True
        elif diferenca < 3600:
            print("⚠️  ATENÇÃO: Desatualizado")
            print(f"   Última atualização: {diferenca/60:.1f} minutos atrás")
            return False
        else:
            print("❌ DESATUALIZADO!")
            print(f"   Última atualização: {diferenca/3600:.1f} horas atrás")
            return False
    
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Sem conexão com a internet")
        return False
    except requests.exceptions.HTTPError as e:
        print(f"❌ ERRO HTTP: {e}")
        if resp.status_code == 404:
            print(f"   Arquivo não encontrado em: {PEERS_URL}")
        return False
    except json.JSONDecodeError:
        print("❌ ERRO: O arquivo não contém um JSON válido")
        return False
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {e}")
        return False

# ============================================================
# 🚀 ATUALIZAR NO GITHUB
# ============================================================

def atualizar_no_github(altura_atual=0):
    print("\n" + "=" * 60)
    print("🚀 ENVIANDO ATUALIZAÇÃO PARA O GITHUB")
    print("=" * 60 + "\n")
    
    if not GITHUB_TOKEN:
        print("❌ Token não configurado!")
        print("   Para atualizar, crie um arquivo .env com:")
        print("   GITHUB_TOKEN=seu-token-aqui")
        print("   Ou defina a variável de ambiente GITHUB_TOKEN")
        return False
    
    agora = int(time.time())
    url = f"https://api.github.com/repos/{USUARIO}/{REPOSITORIO}/contents/{ARQUIVO}"
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    try:
        print("📡 Lendo versão atual...")
        resp = requests.get(url, headers=headers)
        
        if resp.status_code == 200:
            dados_arquivo = resp.json()
            conteudo_atual = json.loads(__import__("base64").b64decode(dados_arquivo["content"]))
            sha_atual = dados_arquivo["sha"]
            print(f"✅ Lido — {len(conteudo_atual)} nó(s) preservado(s)")
        elif resp.status_code == 404:
            print("⚠️ Arquivo não existe — criando novo")
            conteudo_atual = {}
            sha_atual = None
        else:
            print(f"❌ Erro: {resp.status_code}")
            print(f"   {resp.text}")
            return False
        
        # Atualiza apenas os dados do seu nó — os outros não são alterados
        conteudo_atual[SEU_ENDERECO] = {
            "h": altura_atual,
            "id": SEU_NODE_ID,
            "ts": agora
        }
        
        print(f"📤 Atualizando: {SEU_ENDERECO}")
        print(f"   → ts={agora}, h={altura_atual}, id={SEU_NODE_ID}")
        
        novo_conteudo = b64encode(json.dumps(conteudo_atual, indent=2, ensure_ascii=False).encode()).decode()
        payload = {
            "message": f"Atualização automática: ts={agora}, h={altura_atual}",
            "content": novo_conteudo,
            "sha": sha_atual
        }
        
        print("📡 Enviando para GitHub...")
        resp = requests.put(url, headers=headers, json=payload)
        
        if resp.status_code in (200, 201):
            print("\n✅ ✅ ✅ SUCESSO!")
            print(f"🔗 Ver em: https://github.com/{USUARIO}/{REPOSITORIO}/blob/main/{ARQUIVO}")
            return True
        else:
            print(f"❌ Erro: {resp.status_code}")
            print(f"   {resp.text}")
            return False
    
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

# ============================================================
# ▶️ MENU PRINCIPAL
# ============================================================

if __name__ == "__main__":
    print("\n🔧 BRN — Ferramenta de Gerenciamento de Rede")
    print("=" * 60 + "\n")
    
    if not GITHUB_TOKEN:
        print("ℹ️  MODO DE LEITURA — Token não configurado")
        print("   Você pode VERIFICAR, mas não ATUALIZAR")
        print("   Para atualizar, configure o arquivo .env\n")
    
    print("Escolha uma opção:")
    print("   1️⃣  Verificar status atual")
    if GITHUB_TOKEN:
        print("   2️⃣  Atualizar agora")
        print("   3️⃣  Verificar + Atualizar")
    
    escolha = input("\nDigite a opção desejada: ").strip()
    
    if escolha == "1":
        verificar_atualizacao()
    elif escolha == "2" and GITHUB_TOKEN:
        altura = input("Digite a altura da blockchain (número do bloco): ").strip()
        altura = int(altura) if altura.isdigit() else 0
        atualizar_no_github(altura)
    elif escolha == "3" and GITHUB_TOKEN:
        verificar_atualizacao()
        print()
        altura = input("Digite a altura da blockchain: ").strip()
        altura = int(altura) if altura.isdigit() else 0
        atualizar_no_github(altura)
    else:
        if escolha in ["2", "3"] and not GITHUB_TOKEN:
            print("❌ Opção indisponível — token não configurado")
        else:
            print("❌ Opção inválida")
    
    print("\n" + "=" * 60)
    input("Pressione Enter para sair...")