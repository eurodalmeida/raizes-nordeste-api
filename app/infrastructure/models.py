from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SqlEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.domain.enums import (
    CanalPedido,
    PerfilUsuario,
    StatusPagamento,
    StatusPedido,
)
from app.infrastructure.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(SqlEnum(PerfilUsuario), default=PerfilUsuario.CLIENTE, nullable=False)

    # Conformidade LGPD e Fidelidade
    consentimento_lgpd = Column(Boolean, default=False, nullable=False)
    finalidade_lgpd = Column(String(255), default="Programa de fidelidade e histórico de pedidos", nullable=True)
    data_consentimento = Column(DateTime, nullable=True)
    pontos_fidelidade = Column(Integer, default=0, nullable=False)

    criado_em = Column(DateTime, default=utcnow, nullable=False)

    pedidos = relationship("Pedido", back_populates="usuario")


class Unidade(Base):
    __tablename__ = "unidades"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    cidade = Column(String(100), nullable=False)
    endereco = Column(String(255), nullable=False)
    ativa = Column(Boolean, default=True, nullable=False)

    estoques = relationship("EstoqueUnidade", back_populates="unidade")
    pedidos = relationship("Pedido", back_populates="unidade")


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(120), nullable=False)
    descricao = Column(Text, nullable=True)
    preco = Column(Float, nullable=False)
    categoria = Column(String(60), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

    estoques = relationship("EstoqueUnidade", back_populates="produto")


class EstoqueUnidade(Base):
    __tablename__ = "estoque_unidades"
    __table_args__ = (
        UniqueConstraint("unidade_id", "produto_id", name="uq_unidade_produto"),
    )

    id = Column(Integer, primary_key=True, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, default=0, nullable=False)

    unidade = relationship("Unidade", back_populates="estoques")
    produto = relationship("Produto", back_populates="estoques")


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    unidade_id = Column(Integer, ForeignKey("unidades.id"), nullable=False)
    canal_pedido = Column(SqlEnum(CanalPedido), nullable=False)
    status = Column(SqlEnum(StatusPedido), default=StatusPedido.AGUARDANDO_PAGAMENTO, nullable=False)
    valor_total = Column(Float, default=0.0, nullable=False)
    criado_em = Column(DateTime, default=utcnow, nullable=False)

    usuario = relationship("Usuario", back_populates="pedidos")
    unidade = relationship("Unidade", back_populates="pedidos")
    itens = relationship("ItemPedido", back_populates="pedido", cascade="all, delete-orphan")
    pagamentos = relationship("Pagamento", back_populates="pedido")


class ItemPedido(Base):
    __tablename__ = "itens_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)

    pedido = relationship("Pedido", back_populates="itens")
    produto = relationship("Produto")


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    metodo = Column(String(40), nullable=False)
    valor = Column(Float, nullable=False)
    status = Column(SqlEnum(StatusPagamento), default=StatusPagamento.PENDENTE, nullable=False)
    transacao_externa_id = Column(String(100), nullable=True)
    criado_em = Column(DateTime, default=utcnow, nullable=False)

    pedido = relationship("Pedido", back_populates="pagamentos")


class LogAuditoria(Base):
    __tablename__ = "logs_auditoria"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=True)
    acao = Column(String(80), nullable=False)
    entidade = Column(String(60), nullable=False)
    entidade_id = Column(Integer, nullable=True)
    detalhes = Column(Text, nullable=True)
    criado_em = Column(DateTime, default=utcnow, nullable=False)