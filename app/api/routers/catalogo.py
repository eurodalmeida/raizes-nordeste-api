from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import exigir_perfis, registrar_auditoria
from app.api.schemas import (
    EstoqueAtualizarIn,
    EstoqueItemOut,
    ProdutoOut,
    UnidadeOut,
)
from app.domain.enums import PerfilUsuario
from app.domain.exceptions import RecursoNaoEncontradoError
from app.infrastructure.database import get_db
from app.infrastructure.models import EstoqueUnidade, Produto, Unidade, Usuario

router = APIRouter(prefix="/catalogo", tags=["Catálogo e Estoque"])


@router.get("/unidades", response_model=list[UnidadeOut])
def listar_unidades(db: Session = Depends(get_db)):
    return db.query(Unidade).filter(Unidade.ativa.is_(True)).all()


@router.get("/produtos", response_model=list[ProdutoOut])
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(Produto).filter(Produto.ativo.is_(True)).all()


@router.get("/unidades/{unidade_id}/estoque", response_model=list[EstoqueItemOut])
def consultar_estoque_unidade(unidade_id: int, db: Session = Depends(get_db)):
    unidade = db.query(Unidade).filter(Unidade.id == unidade_id).first()
    if not unidade:
        raise RecursoNaoEncontradoError("Unidade não encontrada.")

    registros = (
        db.query(EstoqueUnidade, Produto)
        .join(Produto, EstoqueUnidade.produto_id == Produto.id)
        .filter(EstoqueUnidade.unidade_id == unidade_id, Produto.ativo.is_(True))
        .all()
    )

    return [
        EstoqueItemOut(
            produto_id=produto.id,
            produto_nome=produto.nome,
            preco=produto.preco,
            categoria=produto.categoria,
            quantidade=estoque.quantidade,
        )
        for estoque, produto in registros
    ]


@router.put(
    "/unidades/{unidade_id}/estoque/{produto_id}",
    response_model=EstoqueItemOut,
)
def atualizar_estoque_unidade(
    unidade_id: int,
    produto_id: int,
    dados: EstoqueAtualizarIn,
    db: Session = Depends(get_db),
    operador: Usuario = Depends(
        exigir_perfis(PerfilUsuario.GERENTE, PerfilUsuario.ATENDENTE)
    ),
):
    estoque = (
        db.query(EstoqueUnidade)
        .filter(
            EstoqueUnidade.unidade_id == unidade_id,
            EstoqueUnidade.produto_id == produto_id,
        )
        .first()
    )
    if not estoque:
        raise RecursoNaoEncontradoError("Registro de estoque não encontrado para esta unidade/produto.")

    quantidade_anterior = estoque.quantidade
    estoque.quantidade = dados.quantidade

    registrar_auditoria(
        db=db,
        usuario_id=operador.id,
        acao="ATUALIZACAO_ESTOQUE",
        entidade="EstoqueUnidade",
        entidade_id=estoque.id,
        detalhes=f"Unidade {unidade_id}, Produto {produto_id}: {quantidade_anterior} -> {dados.quantidade}",
    )
    db.commit()
    db.refresh(estoque)

    return EstoqueItemOut(
        produto_id=estoque.produto.id,
        produto_nome=estoque.produto.nome,
        preco=estoque.produto.preco,
        categoria=estoque.produto.categoria,
        quantidade=estoque.quantidade,
    )