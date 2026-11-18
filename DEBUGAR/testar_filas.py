import os
from google import genai
from dotenv import load_dotenv

# Força a leitura do .env na raiz do projeto
caminho_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
load_dotenv(caminho_env)

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Lista de modelos rápidos que o seu Raio-X detectou anteriormente
modelos_para_testar = [
    'gemini-3.8-flash',
    'gemini-3.5-flash',
    'gemini-3.5-flash-lite',
    'gemini-2.5-flash-lite'
]

print("="*50)
print("🔍 INICIANDO RADAR DE TRÁFEGO DO GOOGLE 🔍")
print("="*50)

for modelo in modelos_para_testar:
    print(f"⏳ Batendo na porta do modelo: {modelo}...")
    try:
        response = client.models.generate_content(
            model=modelo,
            contents="Responda apenas 'OK' se estiver funcionando."
        )
        print(f"✅ PISTA LIVRE! O modelo respondeu: {response.text.strip()}\n")
    except Exception as e:
        mensagem_erro = str(e)
        if "503" in mensagem_erro:
            print("❌ FILA CHEIA (Erro 503 - Unavailable)\n")
        elif "404" in mensagem_erro:
            print("❌ NEGADO (Erro 404 - Not Found / Sem acesso)\n")
        else:
            print(f"❌ ERRO DESCONHECIDO: {mensagem_erro[:80]}...\n")

print("="*50)
