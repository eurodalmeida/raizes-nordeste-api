import os
import sys
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from app.domain.enums import PerfilUsuario
from app.infrastructure.database import Base, get_db
from app.infrastructure.models import EstoqueUnidade, Produto, Unidade, Usuario
from app.infrastructure.security import gerar_hash_senha

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def preparar_banco_teste():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    agora = datetime.now(timezone.utc)
    gerente = Usuario(
        nome="Gerente Teste",
        email="gerente@teste.com",
        senha_hash=gerar_hash_senha("123456"),
        perfil=PerfilUsuario.GERENTE,
        consentimento_lgpd=True,
        data_consentimento=agora,
    )
    cliente = Usuario(
        nome="Cliente Teste",
        email="cliente@teste.com",
        senha_hash=gerar_hash_senha("123456"),
        perfil=PerfilUsuario.CLIENTE,
        consentimento_lgpd=True,
        data_consentimento=agora,
        pontos_fidelidade=0,
    )
    unidade = Unidade(
        nome="Unidade Teste",
        cidade="Recife",
        endereco="Rua Teste, 100",
    )
    produto = Produto(
        nome="Baião de Dois",
        descricao="Prato regional",
        preco=50.0,
        categoria="Pratos Principais",
    )
    db.add_all([gerente, cliente, unidade, produto])
    db.flush()

    estoque = EstoqueUnidade(
        unidade_id=unidade.id,
        produto_id=produto.id,
        quantidade=10,
    )
    db.add(estoque)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


def obter_token(email: str, senha: str = "123456") -> str:
    resposta = client.post(
        "/auth/login",
        data={"username": email, "password": senha},
    )
    assert resposta.status_code == 200
    return resposta.json()["access_token"]


def test_health_check():
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_registro_bloqueado_sem_consentimento_lgpd():
    resposta = client.post(
        "/auth/register",
        json={
            "nome": "Novo Cliente",
            "email": "novo@teste.com",
            "senha": "123456",
            "consentimento_lgpd": False,
        },
    )
    assert resposta.status_code == 409
    assert "CONFLITO_NEGOCIO" in str(resposta.json()) or "LGPD" in str(resposta.json())


def test_fluxo_pedido_baixa_estoque_pagamento_e_fidelidade():
    token = obter_token("cliente@teste.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Cria pedido com 2 unidades (2 x R$ 50,00 = R$ 100,00)
    resp_pedido = client.post(
        "/pedidos",
        headers=headers,
        json={
            "unidade_id": 1,
            "canal_pedido": "APP",
            "itens": [{"produto_id": 1, "quantidade": 2}],
        },
    )
    assert resp_pedido.status_code == 201
    pedido = resp_pedido.json()
    assert pedido["valor_total"] == 100.0
    assert pedido["status"] == "AGUARDANDO_PAGAMENTO"

    # Confirma baixa de estoque (10 -> 8)
    resp_estoque = client.get("/catalogo/unidades/1/estoque")
    assert resp_estoque.json()[0]["quantidade"] == 8

    # Processa pagamento aprovado e verifica ganho de 10 pontos (100 // 10)
    resp_pgto = client.post(
        f"/pedidos/{pedido['id']}/pagar",
        headers=headers,
        json={"metodo": "PIX", "simular_aprovacao": True, "usar_pontos_fidelidade": 0},
    )
    assert resp_pgto.status_code == 201
    assert resp_pgto.json()["status"] == "APROVADO"

    resp_me = client.get("/auth/me", headers=headers)
    assert resp_me.json()["pontos_fidelidade"] == 10


def test_pedido_com_estoque_insuficiente():
    token = obter_token("cliente@teste.com")
    headers = {"Authorization": f"Bearer {token}"}

    resposta = client.post(
        "/pedidos",
        headers=headers,
        json={
            "unidade_id": 1,
            "canal_pedido": "WEB",
            "itens": [{"produto_id": 1, "quantidade": 50}],
        },
    )
    assert resposta.status_code == 409
    assert "ESTOQUE_INSUFICIENTE" in str(resposta.json()) or "Estoque insuficiente" in str(resposta.json())


def test_cancelamento_estorna_estoque_e_auditoria_rbac():
    token_cliente = obter_token("cliente@teste.com")
    headers_cliente = {"Authorization": f"Bearer {token_cliente}"}

    # Cria pedido de 3 unidades (estoque: 10 -> 7)
    resp_pedido = client.post(
        "/pedidos",
        headers=headers_cliente,
        json={
            "unidade_id": 1,
            "canal_pedido": "TOTEM",
            "itens": [{"produto_id": 1, "quantidade": 3}],
        },
    )
    pedido_id = resp_pedido.json()["id"]

    # Cancela pedido e valida estorno (estoque: 7 -> 10)
    resp_cancel = client.patch(
        f"/pedidos/{pedido_id}/status",
        headers=headers_cliente,
        json={"status": "CANCELADO"},
    )
    assert resp_cancel.status_code == 200
    assert resp_cancel.json()["status"] == "CANCELADO"

    resp_estoque = client.get("/catalogo/unidades/1/estoque")
    assert resp_estoque.json()[0]["quantidade"] == 10

    # Cliente não pode acessar logs de auditoria (RBAC -> 403)
    resp_audit_cliente = client.get("/auditoria/logs", headers=headers_cliente)
    assert resp_audit_cliente.status_code == 403

    # Gerente acessa logs de auditoria com sucesso (200)
    token_gerente = obter_token("gerente@teste.com")
    resp_audit_gerente = client.get(
        "/auditoria/logs",
        headers={"Authorization": f"Bearer {token_gerente}"},
    )
    assert resp_audit_gerente.status_code == 200
    assert len(resp_audit_gerente.json()) >= 2
