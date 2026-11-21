from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.domain.enums import (
    CanalPedido,
    PerfilUsuario,
    StatusPagamento,
    StatusPedido,
)


class UsuarioRegistroIn(BaseModel):
    nome: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(..., min_length=6, max_length=72)
    consentimento_lgpd: bool


class UsuarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    perfil: PerfilUsuario
    consentimento_lgpd: bool
    pontos_fidelidade: int
    criado_em: datetime


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UnidadeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cidade: str
    endereco: str
    ativa: bool


class ProdutoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None
    preco: float
    categoria: str
    ativo: bool


class EstoqueItemOut(BaseModel):
    produto_id: int
    produto_nome: str
    preco: float
    categoria: str
    quantidade: int


class EstoqueAtualizarIn(BaseModel):
    quantidade: int = Field(..., ge=0)


class ItemPedidoIn(BaseModel):
    produto_id: int
    quantidade: int = Field(..., gt=0)


class PedidoCriarIn(BaseModel):
    unidade_id: int
    canal_pedido: CanalPedido
    itens: list[ItemPedidoIn] = Field(..., min_length=1)


class ItemPedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    produto_id: int
    quantidade: int
    preco_unitario: float


class PagamentoIn(BaseModel):
    metodo: str = Field(..., examples=["PIX", "CARTAO_CREDITO", "DINHEIRO"])
    simular_aprovacao: bool = True
    usar_pontos_fidelidade: int = Field(default=0, ge=0)


class PagamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pedido_id: int
    metodo: str
    valor: float
    status: StatusPagamento
    transacao_externa_id: str | None
    criado_em: datetime


class PedidoStatusIn(BaseModel):
    status: StatusPedido


class PedidoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int
    unidade_id: int
    canal_pedido: CanalPedido
    status: StatusPedido
    valor_total: float
    criado_em: datetime
    itens: list[ItemPedidoOut]
    pagamentos: list[PagamentoOut] = []


class LogAuditoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    usuario_id: int | None
    acao: str
    entidade: str
    entidade_id: int | None
    detalhes: str | None
    criado_em: datetime