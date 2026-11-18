import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def interpretar_mensagem(mensagem_usuario):
    prompt = f"""
    Você é um assistente financeiro de uma barbearia. Extraia os dados da mensagem do usuário para o formato JSON.
    
    Regras de extração:
    - acao: Pode ser "registrar", "consultar", "atualizar_pix", ou "relatorio_faturamento".
    - cliente: Nome do cliente (se houver).
    - valor: Número float (se houver valor monetário, extraia).
    - tipo: "entrada" (para pagamentos/serviços) ou "saida" (para gastos/despesas). Padrão é "entrada".
    - status: "pago" ou "pendente". Padrão é "pago".
    - descricao: O que foi feito/comprado.
    - chave_pix: Se o usuário quiser mudar a chave PIX, extraia a nova chave aqui.
    - periodo: Se o usuário pedir relatório (ex: "hoje", "essa semana", "este mes"), extraia o período aqui ("dia", "semana", "mes", etc).
    
    Exemplos:
    1. "Muda minha chave pix para celular 11999999999" -> {{"acao": "atualizar_pix", "chave_pix": "11999999999"}}
    2. "O João ficou me devendo 50 pelo corte" -> {{"acao": "registrar", "cliente": "João", "valor": 50.0, "tipo": "entrada", "status": "pendente", "descricao": "Corte"}}
    3. "Quanto entrou hoje?" -> {{"acao": "relatorio_faturamento", "periodo": "dia"}}
    
    Mensagem: "{mensagem_usuario}"
    Retorne APENAS o JSON, sem markdown e sem formatação adicional.
    """
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt
        )
        texto_limpo = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(texto_limpo)
    except Exception as e:
        return {"erro": str(e)}
    