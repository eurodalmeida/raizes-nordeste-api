from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.domain.enums import PerfilUsuario


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