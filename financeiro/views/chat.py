import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from financeiro.services.gemini import interpretar_mensagem
from financeiro.services.cliente import FinanceiroService
from financeiro.models import Cliente

def tela_chat(request):
    """Renderiza a interface do celular."""
    return render(request, 'index.html')

@csrf_exempt
def processar_mensagem(request):
    """Recebe a mensagem do HTML, processa na IA e no banco de dados."""
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            
            # 1. A MEMÓRIA: Se o JS mandar a confirmação do Tira-Teima, salva direto!
            if "cliente_id_confirmado" in dados:
                c_id = dados["cliente_id_confirmado"]
                d_ia = dados["dados_ia"]
                FinanceiroService.registrar_transacao(
                    c_id, d_ia.get("valor", 0), d_ia.get("descricao", ""),
                    d_ia.get("tipo", "entrada"), d_ia.get("status", "pago")
                )
                nome = Cliente.objects.get(id=c_id).nome
                return JsonResponse({
                    "tipo": "sucesso",
                    "resposta": f"✅ Fechou! Registrado R$ {d_ia.get('valor')} para {nome}."
                })

            # 2. FLUXO NORMAL: Interpretando a mensagem com o Gemini
            mensagem = dados.get('mensagem', '')
            if not mensagem:
                return JsonResponse({"erro": "Mensagem vazia"})

            dados_ia = interpretar_mensagem(mensagem)
            
            if "erro" in dados_ia:
                return JsonResponse({"tipo": "erro", "resposta": f"Erro na IA: {dados_ia['erro']}"})

            acao = dados_ia.get("acao")
            cliente_nome = dados_ia.get("cliente")
            valor = dados_ia.get("valor", 0.0)
            descricao = dados_ia.get("descricao", "")
            tipo = dados_ia.get("tipo", "entrada")
            status = dados_ia.get("status", "pago")

            if acao == "registrar":
                resultado_busca = FinanceiroService.processar_busca_cliente(cliente_nome)
                
                if resultado_busca["status"] == "unico":
                    cliente_id = resultado_busca["cliente"].id
                    FinanceiroService.registrar_transacao(cliente_id, valor, descricao, tipo, status)
                    return JsonResponse({
                        "tipo": "sucesso",
                        "resposta": f"✅ Registrado: R$ {valor:.2f} para {resultado_busca['cliente'].nome} ({status.upper()})"
                    })
                
                elif resultado_busca["status"] == "multiplos":
                    return JsonResponse({
                        "tipo": "tira_teima",
                        "opcoes": resultado_busca["opcoes"],
                        "resposta": f"Encontrei mais de um '{cliente_nome}'. Qual deles é?",
                        "dados_ia": dados_ia # Enviando os dados para a memória do celular!
                    })
                    
                elif resultado_busca["status"] == "novo":
                    return JsonResponse({
                        "tipo": "novo_cliente",
                        "resposta": f"Não encontrei '{cliente_nome}'. Quer que eu cadastre como cliente novo?"
                    })
                
                elif resultado_busca["status"] == "despesa":
                    FinanceiroService.registrar_transacao(None, valor, descricao, tipo, status)
                    return JsonResponse({
                        "tipo": "sucesso",
                        "resposta": f"💸 Despesa Registrada: R$ {valor:.2f} ({descricao})"
                    })

            return JsonResponse({"tipo": "info", "resposta": "Função de relatório em desenvolvimento!"})
            
        except Exception as e:
            return JsonResponse({"tipo": "erro", "resposta": str(e)})
            
    return JsonResponse({"tipo": "erro", "resposta": "Método não permitido"})
