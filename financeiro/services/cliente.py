from django.db.models import Q, Sum
from financeiro.models import Cliente, Transacao

class FinanceiroService:
    @staticmethod
    def processar_busca_cliente(termo_busca):
        # BLINDAGEM: Se a IA não achar nenhum cliente (None) ou usar um termo geral
        if not termo_busca or str(termo_busca).lower() in ["barbearia", "despesa", "loja", "geral"]:
            return {"status": "despesa"}
            
        clientes = Cliente.objects.filter(
            Q(nome__icontains=termo_busca) | Q(apelidos__icontains=termo_busca)
        )
        quantidade = clientes.count()

        if quantidade == 1:
            return {"status": "unico", "cliente": clientes.first()}
        elif quantidade > 1:
            lista = [{"id": c.id, "nome": c.nome} for c in clientes]
            return {"status": "multiplos", "opcoes": lista}
        else:
            return {"status": "novo", "termo": termo_busca}

    @staticmethod
    def registrar_transacao(cliente_id, valor, descricao, tipo, status):
        """Cria o registro financeiro real no banco de dados."""
        cliente = Cliente.objects.get(id=cliente_id) if cliente_id else None
        
        Transacao.objects.create(
            cliente=cliente,
            valor=valor,
            descricao=descricao,
            tipo=tipo,
            status=status
        )

    @staticmethod
    def consultar_divida(cliente_id):
        """Soma todos os valores pendentes (fiado) de um cliente."""
        cliente = Cliente.objects.get(id=cliente_id)
        transacoes_pendentes = Transacao.objects.filter(cliente=cliente, status='pendente')
        total = transacoes_pendentes.aggregate(Sum('valor'))['valor__sum']
        return float(total) if total else 0.0

    @staticmethod
    def cadastrar_cliente(nome):
        """Cadastra um novo cliente rapidamente salvando o nome e o apelido."""
        return Cliente.objects.create(nome=nome, apelidos=nome)
    