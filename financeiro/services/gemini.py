import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Inicializa o cliente normalmente usando a nova chave (AIza...)
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def interpretar_mensagem(mensagem_usuario):
    prompt = f"""
    Você é um assistente financeiro. Extraia os dados para JSON.
    - acao: "registrar" ou "consultar"
    - cliente: Nome
    - valor: Numero float
    - tipo: "entrada" ou "saida"
    - status: "pago" ou "pendente"
    - descricao: O que foi feito
    Mensagem: "{mensagem_usuario}"
    Retorne APENAS o JSON.
    """
    try:
        # Usando a versão mais avançada, rápida e esperta disponível na sua chave
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=prompt
        )
        texto_limpo = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(texto_limpo)
    except Exception as e:
        return {"erro": str(e)}
    