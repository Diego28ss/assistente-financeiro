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
        