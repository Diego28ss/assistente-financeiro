from django.db import models

class Cliente(models.Model):
    nome = models.CharField(max_length=150)
    # O campo apelidos é crucial para a IA encontrar nomes como "Gilo" ou "João da Padaria"
    apelidos = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        help_text="Separe por vírgula. Ex: Gilo, João da Padaria, Diego do Corsa"
    )
    telefone = models.CharField(max_length=20, blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome

class Transacao(models.Model):
    TIPO_CHOICES = [
        ('entrada', 'Entrada (Corte/Serviço)'),
        ('saida', 'Saída (Despesa/Produto)'),
    ]
    
    STATUS_CHOICES = [
        ('pago', 'Pago'),
        ('pendente', 'Pendente (Fiado)'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='transacoes')
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    descricao = models.CharField(max_length=255, help_text="Ex: Corte de cabelo e barba")
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES, default='entrada')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pago')
    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        nome_cliente = self.cliente.nome if self.cliente else "Despesa"
        return f"{nome_cliente} - R$ {self.valor} ({self.get_status_display()})"
    