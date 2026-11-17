import os
from google import genai
from dotenv import load_dotenv

# O override=True garante que ele vai ler o .env atual e ignorar chaves antigas presas na memória
load_dotenv(override=True)
chave = os.getenv("GEMINI_API_KEY", "CHAVE_NAO_ENCONTRADA")

print("="*50)
print("🔍 INICIANDO DEBUGGING DA IA 🔍")
print("="*50)
print(f"Chave detectada : {chave[:5]}...{chave[-4:]}")
print(f"Tamanho da chave: {len(chave)} caracteres\n")

try:
    client = genai.Client(api_key=chave)
    print("⏳ Perguntando ao servidor do Google quais modelos existem para essa chave...\n")
    
    # Chama a função exata que o erro nos recomendou chamar
    modelos = client.models.list()
    
    print("✅ NOMES EXATOS DOS MODELOS DISPONÍVEIS NA SUA CONTA:")
    contador = 0
    for m in modelos:
        print(f" -> {m.name}")
        contador += 1
        
    if contador == 0:
        print("⚠️ Nenhum modelo foi retornado. Sua chave não tem permissões ativas.")
        
except Exception as e:
    print(f"❌ OCORREU UM ERRO AO CONECTAR:\n{e}")
print("="*50)
