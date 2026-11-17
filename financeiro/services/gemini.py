import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

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
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        texto_limpo = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(texto_limpo)
    except Exception as e:
        return {"erro": str(e)}
    