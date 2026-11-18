import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

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
        # PISTA LIVRE: Usando o modelo Lite para evitar filas e ter resposta instantânea
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt
        )
        texto_limpo = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(texto_limpo)
    except Exception as e:
        return {"erro": str(e)}
    