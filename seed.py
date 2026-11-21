import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.domain.enums import PerfilUsuario
from app.infrastructure.database import Base, SessionLocal, engine
from app.infrastructure.models import EstoqueUnidade, Produto, Unidade, Usuario
from app.infrastructure.security import gerar_hash_senha


def popular_banco():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Usuario).first():
            print("Banco já possui dados cadastrados. Nenhuma alteração feita.")
            return

        agora = datetime.now(timezone.utc)

        # 1. Usuários iniciais (senha padrão: 123456)
        usuarios = [
            Usuario(
                nome="Gerente Geral",
                email="gerente@raizes.com",
                senha_hash=gerar_hash_senha("123456"),
                perfil=PerfilUsuario.GERENTE,
                consentimento_lgpd=True,
                data_consentimento=agora,
            ),
            Usuario(
                nome="Atendente Balcão",
                email="atendente@raizes.com",
                senha_hash=gerar_hash_senha("123456"),
                perfil=PerfilUsuario.ATENDENTE,
                consentimento_lgpd=True,
                data_consentimento=agora,
            ),
            Usuario(
                nome="Cliente Teste",
                email="cliente@raizes.com",
                senha_hash=gerar_hash_senha("123456"),
                perfil=PerfilUsuario.CLIENTE,
                consentimento_lgpd=True,
                data_consentimento=agora,
                pontos_fidelidade=50,
            ),
        ]
        db.add_all(usuarios)
        db.flush()

        # 2. Unidades
        unidade_recife = Unidade(
            nome="Raízes Recife - Boa Viagem",
            cidade="Recife",
            endereco="Av. Boa Viagem, 1200",
        )
        unidade_fortaleza = Unidade(
            nome="Raízes Fortaleza - Meireles",
            cidade="Fortaleza",
            endereco="Av. Beira Mar, 850",
        )
        db.add_all([unidade_recife, unidade_fortaleza])
        db.flush()

        # 3. Produtos do cardápio
        produtos = [
            Produto(
                nome="Baião de Dois Completo",
                descricao="Arroz, feijão verde, queijo coalho, carne de sol e nata.",
                preco=42.90,
                categoria="Pratos Principais",
            ),
            Produto(
                nome="Carne de Sol na Nata",
                descricao="Acompanha macaxeira frita e arroz de leite.",
                preco=54.00,
                categoria="Pratos Principais",
            ),
            Produto(
                nome="Cartola Nordestina",
                descricao="Banana frita, queijo coalho assado, açúcar e canela.",
                preco=18.50,
                categoria="Sobremesas",
            ),
            Produto(
                nome="Suco de Cajá 500ml",
                descricao="Polpa natural da fruta.",
                preco=11.00,
                categoria="Bebidas",
            ),
        ]
        db.add_all(produtos)
        db.flush()

        # 4. Estoque inicial por unidade
        estoques = []
        for unidade in [unidade_recife, unidade_fortaleza]:
            for produto in produtos:
                estoques.append(
                    EstoqueUnidade(
                        unidade_id=unidade.id,
                        produto_id=produto.id,
                        quantidade=20,
                    )
                )
        db.add_all(estoques)
        db.commit()
        print("Banco populado com sucesso! Usuários, unidades, produtos e estoque criados.")

    except Exception as e:
        db.rollback()
        print(f"Erro ao popular banco: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    popular_banco()