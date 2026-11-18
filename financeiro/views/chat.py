import json
import urllib.parse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from financeiro.services.gemini import interpretar_mensagem
from financeiro.services.cliente import FinanceiroService
from financeiro.models import Cliente

def tela_chat(request):
    """Renderiza a interface do celular."""
    return render(request, 'index.html')

def gerar_link_whatsapp(nome, valor):
    """Gera um link do WhatsApp com a mensagem de cobrança pronta."""
    texto = f"Fala {nome}, beleza? O resumo dos seus cortes aqui na barbearia deu R$ {valor:.2f}. Quando puder, dá um toque! Chave PIX: [SUA CHAVE AQUI]"
    texto_codificado = urllib.parse.quote(texto)
    return f"https://wa.me/?text={texto_codificado}"

@csrf_exempt
def processar_mensagem(request):
    """Recebe a mensagem do HTML, processa na IA e no banco de dados."""
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            
            # 1. A MEMÓRIA DO TIRA-TEIMA
            if "cliente_id_confirmado" in dados:
                c_id = dados["cliente_id_confirmado"]
                d_ia = dados["dados_ia"]
                acao_memoria = d_ia.get("acao")
                nome = Cliente.objects.get(id=c_id).nome

                if acao_memoria == "consultar":
                    total = FinanceiroService.consultar_divida(c_id)
                    if total > 0:
                        msg = f"📊 O cliente {nome} te deve R$ {total:.2f} de fiado."
                        link = gerar_link_whatsapp(nome, total)
                        return JsonResponse({"tipo": "sucesso", "resposta": msg, "whatsapp_link": link})
                    else:
                        msg = f"✅ O cliente {nome} não tem dívidas pendentes! Tudo zerado."
                        return JsonResponse({"tipo": "sucesso", "resposta": msg})
                else: 
                    FinanceiroService.registrar_transacao(
                        c_id, d_ia.get("valor", 0), d_ia.get("descricao", ""),
                        d_ia.get("tipo", "entrada"), d_ia.get("status", "pago")
                    )
                    return JsonResponse({"tipo": "sucesso", "resposta": f"✅ Fechou! Registrado R$ {d_ia.get('valor')} para {nome}."})

            # 2. A MEMÓRIA DO NOVO CADASTRO FLUIDO
            if "confirmar_cadastro" in dados:
                d_ia = dados["dados_ia"]
                nome_novo = d_ia.get("cliente")
                
                novo_cliente = FinanceiroService.cadastrar_cliente(nome_novo)
                FinanceiroService.registrar_transacao(
                    novo_cliente.id, d_ia.get("valor", 0), d_ia.get("descricao", ""),
                    d_ia.get("tipo", "entrada"), d_ia.get("status", "pago")
                )
                return JsonResponse({
                    "tipo": "sucesso", 
                    "resposta": f"👤 Cliente '{nome_novo}' cadastrado com sucesso!<br>✅ Lançamento de R$ {d_ia.get('valor')} registrado."
                })

            # 3. FLUXO NORMAL: Interpretando a mensagem com o Gemini
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

            resultado_busca = FinanceiroService.processar_busca_cliente(cliente_nome)

            if resultado_busca["status"] == "unico":
                cliente_id = resultado_busca["cliente"].id
                nome_encontrado = resultado_busca["cliente"].nome
                
                if acao == "consultar":
                    total = FinanceiroService.consultar_divida(cliente_id)
                    if total > 0:
                        resposta = f"📊 O cliente {nome_encontrado} te deve R$ {total:.2f} de fiado."
                        link = gerar_link_whatsapp(nome_encontrado, total)
                        return JsonResponse({"tipo": "sucesso", "resposta": resposta, "whatsapp_link": link})
                    else:
                        resposta = f"✅ O cliente {nome_encontrado} não tem dívidas pendentes! Tudo zerado."
                        return JsonResponse({"tipo": "sucesso", "resposta": resposta})
                else:
                    FinanceiroService.registrar_transacao(cliente_id, valor, descricao, tipo, status)
                    return JsonResponse({"tipo": "sucesso", "resposta": f"✅ Registrado: R$ {valor:.2f} para {nome_encontrado} ({status.upper()})"})

            elif resultado_busca["status"] == "multiplos":
                return JsonResponse({
                    "tipo": "tira_teima",
                    "opcoes": resultado_busca["opcoes"],
                    "resposta": f"Encontrei mais de um '{cliente_nome}'. Qual deles é?",
                    "dados_ia": dados_ia
                })

            elif resultado_busca["status"] == "novo":
                if acao == "consultar":
                    return JsonResponse({"tipo": "sucesso", "resposta": f"O cliente '{cliente_nome}' não está cadastrado, então não tem dívida."})
                else:
                    return JsonResponse({
                        "tipo": "novo_cliente",
                        "resposta": f"Não encontrei '{cliente_nome}'. Quer que eu cadastre como cliente novo e já lance o valor?",
                        "dados_ia": dados_ia
                    })

            elif resultado_busca["status"] == "despesa":
                if acao == "consultar":
                    return JsonResponse({"tipo": "info", "resposta": "O relatório de despesas será liberado na próxima versão!"})
                else:
                    FinanceiroService.registrar_transacao(None, valor, descricao, tipo, status)
                    return JsonResponse({"tipo": "sucesso", "resposta": f"💸 Despesa Registrada: R$ {valor:.2f} ({descricao})"})
                    
        except Exception as e:
            return JsonResponse({"tipo": "erro", "resposta": str(e)})
            
    return JsonResponse({"tipo": "erro", "resposta": "Método não permitido"})
