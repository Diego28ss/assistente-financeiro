import json
import urllib.parse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from financeiro.services.gemini import interpretar_mensagem
from financeiro.services.cliente import FinanceiroService
from financeiro.models import Cliente, PerfilUsuario, MensagemChat

@login_required(login_url='/admin/login/')
def tela_chat(request):
    """Renderiza a interface do celular."""
    # Opcional: Carregar histórico dos últimos 30 dias para exibir na tela inicial
    # Aqui, passamos apenas para renderizar o template básico por enquanto
    return render(request, 'index.html')

def gerar_link_whatsapp(nome, valor, chave_pix):
    """Gera um link do WhatsApp com a mensagem de cobrança pronta."""
    pix_msg = f" Chave PIX: {chave_pix}" if chave_pix else ""
    texto = f"Fala {nome}, beleza? O resumo dos seus cortes aqui na barbearia deu R$ {valor:.2f}. Quando puder, dá um toque!{pix_msg}"
    texto_codificado = urllib.parse.quote(texto)
    return f"https://wa.me/?text={texto_codificado}"

def salvar_historico_chat(usuario, texto, remetente):
    """Salva a mensagem no histórico do chat."""
    MensagemChat.objects.create(
        usuario=usuario,
        texto=texto,
        remetente=remetente
    )

@csrf_exempt
@login_required(login_url='/admin/login/')
def processar_mensagem(request):
    """Recebe a mensagem do HTML, processa na IA e no banco de dados."""
    if request.method == 'POST':
        try:
            dados = json.loads(request.body)
            usuario_atual = request.user
            
            perfil, _ = PerfilUsuario.objects.get_or_create(usuario=usuario_atual)
            chave_pix_usuario = perfil.chave_pix
            
            # 1. A MEMÓRIA DO TIRA-TEIMA
            if "cliente_id_confirmado" in dados:
                c_id = dados["cliente_id_confirmado"]
                d_ia = dados["dados_ia"]
                acao_memoria = d_ia.get("acao")
                nome = Cliente.objects.get(id=c_id, usuario=usuario_atual).nome

                if acao_memoria == "consultar":
                    total = FinanceiroService.consultar_divida(c_id, usuario=usuario_atual)
                    if total > 0:
                        msg = f"📊 O cliente {nome} te deve R$ {total:.2f} de fiado."
                        link = gerar_link_whatsapp(nome, total, chave_pix_usuario)
                        salvar_historico_chat(usuario_atual, msg, 'ia')
                        return JsonResponse({"tipo": "sucesso", "resposta": msg, "whatsapp_link": link})
                    else:
                        msg = f"✅ O cliente {nome} não tem dívidas pendentes! Tudo zerado."
                        salvar_historico_chat(usuario_atual, msg, 'ia')
                        return JsonResponse({"tipo": "sucesso", "resposta": msg})
                else: 
                    FinanceiroService.registrar_transacao(
                        c_id, d_ia.get("valor", 0), d_ia.get("descricao", ""),
                        d_ia.get("tipo", "entrada"), d_ia.get("status", "pago"),
                        usuario=usuario_atual
                    )
                    msg = f"✅ Fechou! Registrado R$ {d_ia.get('valor')} para {nome}."
                    salvar_historico_chat(usuario_atual, msg, 'ia')
                    return JsonResponse({"tipo": "sucesso", "resposta": msg})

            # 2. A MEMÓRIA DO NOVO CADASTRO FLUIDO
            if "confirmar_cadastro" in dados:
                d_ia = dados["dados_ia"]
                nome_novo = d_ia.get("cliente")
                
                novo_cliente = FinanceiroService.cadastrar_cliente(nome_novo, usuario=usuario_atual)
                FinanceiroService.registrar_transacao(
                    novo_cliente.id, d_ia.get("valor", 0), d_ia.get("descricao", ""),
                    d_ia.get("tipo", "entrada"), d_ia.get("status", "pago"),
                    usuario=usuario_atual
                )
                msg = f"👤 Cliente '{nome_novo}' cadastrado com sucesso!<br>✅ Lançamento de R$ {d_ia.get('valor')} registrado."
                salvar_historico_chat(usuario_atual, msg, 'ia')
                return JsonResponse({
                    "tipo": "sucesso", 
                    "resposta": msg
                })

            # 3. FLUXO NORMAL: Interpretando a mensagem com o Gemini
            mensagem = dados.get('mensagem', '')
            if not mensagem:
                return JsonResponse({"erro": "Mensagem vazia"})

            salvar_historico_chat(usuario_atual, mensagem, 'usuario')
            
            dados_ia = interpretar_mensagem(mensagem)
            
            if "erro" in dados_ia:
                msg_erro = f"Erro na IA: {dados_ia['erro']}"
                salvar_historico_chat(usuario_atual, msg_erro, 'ia')
                return JsonResponse({"tipo": "erro", "resposta": msg_erro})

            acao = dados_ia.get("acao")
            
            # 3.1 FLUXO: Atualização de PIX
            if acao == "atualizar_pix":
                nova_chave = dados_ia.get("chave_pix", "")
                if nova_chave:
                    perfil.chave_pix = nova_chave
                    perfil.save()
                    msg = f"✅ Chave PIX atualizada para: {nova_chave}"
                else:
                    msg = "Não entendi a chave PIX, pode repetir?"
                salvar_historico_chat(usuario_atual, msg, 'ia')
                return JsonResponse({"tipo": "sucesso", "resposta": msg})
                
            # 3.2 FLUXO: Relatórios
            if acao == "relatorio_faturamento":
                periodo = dados_ia.get("periodo", "dia") # dia, semana, mes, etc. (Implementação do cálculo será no Service no próximo passo)
                msg = f"📊 Buscando o relatório de faturamento para: {periodo}... (Cálculo na Fase 3)"
                salvar_historico_chat(usuario_atual, msg, 'ia')
                return JsonResponse({"tipo": "sucesso", "resposta": msg})


            cliente_nome = dados_ia.get("cliente")
            valor = dados_ia.get("valor", 0.0)
            descricao = dados_ia.get("descricao", "")
            tipo = dados_ia.get("tipo", "entrada")
            status = dados_ia.get("status", "pago")

            resultado_busca = FinanceiroService.processar_busca_cliente(cliente_nome, usuario=usuario_atual)

            if resultado_busca["status"] == "unico":
                cliente_id = resultado_busca["cliente"].id
                nome_encontrado = resultado_busca["cliente"].nome
                
                if acao == "consultar":
                    total = FinanceiroService.consultar_divida(cliente_id, usuario=usuario_atual)
                    if total > 0:
                        resposta = f"📊 O cliente {nome_encontrado} te deve R$ {total:.2f} de fiado."
                        link = gerar_link_whatsapp(nome_encontrado, total, chave_pix_usuario)
                        salvar_historico_chat(usuario_atual, resposta, 'ia')
                        return JsonResponse({"tipo": "sucesso", "resposta": resposta, "whatsapp_link": link})
                    else:
                        resposta = f"✅ O cliente {nome_encontrado} não tem dívidas pendentes! Tudo zerado."
                        salvar_historico_chat(usuario_atual, resposta, 'ia')
                        return JsonResponse({"tipo": "sucesso", "resposta": resposta})
                else:
                    FinanceiroService.registrar_transacao(cliente_id, valor, descricao, tipo, status, usuario=usuario_atual)
                    resposta = f"✅ Registrado: R$ {valor:.2f} para {nome_encontrado} ({status.upper()})"
                    salvar_historico_chat(usuario_atual, resposta, 'ia')
                    return JsonResponse({"tipo": "sucesso", "resposta": resposta})

            elif resultado_busca["status"] == "multiplos":
                resposta = f"Encontrei mais de um '{cliente_nome}'. Qual deles é?"
                salvar_historico_chat(usuario_atual, resposta, 'ia')
                return JsonResponse({
                    "tipo": "tira_teima",
                    "opcoes": resultado_busca["opcoes"],
                    "resposta": resposta,
                    "dados_ia": dados_ia
                })

            elif resultado_busca["status"] == "novo":
                if acao == "consultar":
                    resposta = f"O cliente '{cliente_nome}' não está cadastrado, então não tem dívida."
                    salvar_historico_chat(usuario_atual, resposta, 'ia')
                    return JsonResponse({"tipo": "sucesso", "resposta": resposta})
                else:
                    resposta = f"Não encontrei '{cliente_nome}'. Quer que eu cadastre como cliente novo e já lance o valor?"
                    salvar_historico_chat(usuario_atual, resposta, 'ia')
                    return JsonResponse({
                        "tipo": "novo_cliente",
                        "resposta": resposta,
                        "dados_ia": dados_ia
                    })

            elif resultado_busca["status"] == "despesa":
                if acao == "consultar":
                    resposta = "O relatório de despesas será liberado na próxima versão!"
                    salvar_historico_chat(usuario_atual, resposta, 'ia')
                    return JsonResponse({"tipo": "info", "resposta": resposta})
                else:
                    FinanceiroService.registrar_transacao(None, valor, descricao, tipo, status, usuario=usuario_atual)
                    resposta = f"💸 Despesa Registrada: R$ {valor:.2f} ({descricao})"
                    salvar_historico_chat(usuario_atual, resposta, 'ia')
                    return JsonResponse({"tipo": "sucesso", "resposta": resposta})
                    
        except Exception as e:
            msg_erro = str(e)
            # Idealmente logar o erro num logger
            return JsonResponse({"tipo": "erro", "resposta": msg_erro})
            
    return JsonResponse({"tipo": "erro", "resposta": "Método não permitido"})
