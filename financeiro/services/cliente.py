from django.db.models import Q
from financeiro.models import Cliente, Transacao

class FinanceiroService:
    @staticmethod
    def processar_busca_cliente(termo_busca):
        if termo_busca.lower() == "barbearia":
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
        # Se for despesa da barbearia, o cliente_id vem como None
        cliente = Cliente.objects.get(id=cliente_id) if cliente_id else None
        
        Transacao.objects.create(
            cliente=cliente,
            valor=valor,
            descricao=descricao,
            tipo=tipo,
            status=status
        )
        