from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect
from financeiro.views import tela_chat, processar_mensagem

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Se acessar a raiz pura (http://127.0.0.1:8000/), o Django "empurra" para o Assistente
    path('', lambda request: redirect('assistente')),
    
    # 2. A sua nova URL personalizada (http://127.0.0.1:8000/Assistente/)
    path('Assistente/', tela_chat, name='assistente'),
    
    # 3. A API invisível que conversa com o Gemini e o Banco de Dados
    path('api/mensagem/', processar_mensagem, name='processar_mensagem'),
]
