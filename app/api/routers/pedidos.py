import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, registrar_auditoria
from app.api.schemas import (
    PagamentoIn,
    PagamentoOut,
    PedidoCriarIn,
    PedidoOut,
    PedidoStatusIn,
)
from app.domain.enums import PerfilUsuario, StatusPagamento, StatusPedido
from app.domain.exceptions import (
    AcessoNegadoError,
    ConflitoNegocioError,
    EstoqueInsuficienteError,
    RecursoNaoEncontradoError,
)
from app.infrastructure.database import get_db
from app.infrastructure.models import (
    EstoqueUnidade,
    ItemPedido,
    Pagamento,
    Pedido,
    Produto,
    Unidade,
    Usuario,
)

router = APIRouter(prefix="/pedidos", tags=["Pedidos e Pagamentos"])


@router.post("", response_model=PedidoOut, status_code=status.HTTP_201_CREATED)
def criar_pedido(
    dados: PedidoCriarIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    unidade = (
        db.query(Unidade)
        .filter(Unidade.id == dados.unidade_id, Unidade.ativa.is_(True))
        .first()
    )
    if not unidade:
        raise RecursoNaoEncontradoError("Unidade não encontrada ou inativa.")

    # Agrupa quantidades caso o mesmo produto seja enviado mais de uma vez
    quantidades_por_produto: dict[int, int] = {}
    for item in dados.itens:
        quantidades_por_produto[item.produto_id] = (
            quantidades_por_produto.get(item.produto_id, 0) + item.quantidade
        )

    itens_modelo: list[ItemPedido] = []
    valor_total = 0.0
    falhas_estoque: list[dict] = []

    for produto_id, qtd_solicitada in quantidades_por_produto.items():
        produto = (
            db.query(Produto)
            .filter(Produto.id == produto_id, Produto.ativo.is_(True))
            .first()
        )
        if not produto:
            raise RecursoNaoEncontradoError(f"Produto ID {produto_id} não encontrado ou inativo.")

        estoque = (
            db.query(EstoqueUnidade)
            .filter(
                EstoqueUnidade.unidade_id == dados.unidade_id,
                EstoqueUnidade.produto_id == produto_id,
            )
            .first()
        )
        disponivel = estoque.quantidade if estoque else 0

        if disponivel < qtd_solicitada:
            falhas_estoque.append(
                {
                    "produto_id": produto_id,
                    "produto": produto.nome,
                    "disponivel": disponivel,
                    "solicitado": qtd_solicitada,
                }
            )
        else:
            estoque.quantidade -= qtd_solicitada
            valor_total += produto.preco * qtd_solicitada
            itens_modelo.append(
                ItemPedido(
                    produto_id=produto_id,
                    quantidade=qtd_solicitada,
                    preco_unitario=produto.preco,
                )
            )

    if falhas_estoque:
        db.rollback()
        raise EstoqueInsuficienteError(
            message="Estoque insuficiente na unidade selecionada.",
            details=falhas_estoque,
        )

    novo_pedido = Pedido(
        usuario_id=usuario.id,
        unidade_id=dados.unidade_id,
        canal_pedido=dados.canal_pedido,
        status=StatusPedido.AGUARDANDO_PAGAMENTO,
        valor_total=round(valor_total, 2),
        itens=itens_modelo,
    )
    db.add(novo_pedido)
    db.flush()

    registrar_auditoria(
        db=db,
        usuario_id=usuario.id,
        acao="CRIACAO_PEDIDO",
        entidade="Pedido",
        entidade_id=novo_pedido.id,
        detalhes=f"Canal: {dados.canal_pedido.value} | Unidade: {dados.unidade_id} | Total: R$ {novo_pedido.valor_total:.2f}",
    )
    db.commit()
    db.refresh(novo_pedido)
    return novo_pedido


@router.get("", response_model=list[PedidoOut])
def listar_pedidos(
    unidade_id: int | None = None,
    status_pedido: StatusPedido | None = None,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    query = db.query(Pedido)

    if usuario.perfil == PerfilUsuario.CLIENTE:
        query = query.filter(Pedido.usuario_id == usuario.id)
    else:
        if unidade_id is not None:
            query = query.filter(Pedido.unidade_id == unidade_id)

    if status_pedido is not None:
        query = query.filter(Pedido.status == status_pedido)

    return query.order_by(Pedido.id.desc()).all()


@router.get("/{pedido_id}", response_model=PedidoOut)
def obter_pedido(
    pedido_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise RecursoNaoEncontradoError("Pedido não encontrado.")

    if usuario.perfil == PerfilUsuario.CLIENTE and pedido.usuario_id != usuario.id:
        raise AcessoNegadoError("Você não tem permissão para visualizar este pedido.")

    return pedido


@router.post("/{pedido_id}/pagar", response_model=PagamentoOut, status_code=status.HTTP_201_CREATED)
def processar_pagamento(
    pedido_id: int,
    dados: PagamentoIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise RecursoNaoEncontradoError("Pedido não encontrado.")

    if usuario.perfil == PerfilUsuario.CLIENTE and pedido.usuario_id != usuario.id:
        raise AcessoNegadoError("Você não tem permissão para pagar este pedido.")

    if pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
        raise ConflitoNegocioError(
            f"Pagamento não permitido para pedido com status '{pedido.status.value}'."
        )

    cliente_pedido = db.query(Usuario).filter(Usuario.id == pedido.usuario_id).first()

    # Cada 10 pontos de fidelidade equivalem a R$ 1,00 de desconto
    desconto = 0.0
    if dados.usar_pontos_fidelidade > 0:
        if cliente_pedido.pontos_fidelidade < dados.usar_pontos_fidelidade:
            raise ConflitoNegocioError("Saldo de pontos de fidelidade insuficiente.")
        desconto = min(pedido.valor_total, round(dados.usar_pontos_fidelidade / 10.0, 2))

    valor_final = max(0.0, round(pedido.valor_total - desconto, 2))
    transacao_id = f"MOCK-{uuid.uuid4().hex[:10].upper()}"

    if dados.simular_aprovacao:
        status_pgto = StatusPagamento.APROVADO
        pedido.status = StatusPedido.PAGO

        # Credita 1 ponto a cada R$ 10 pagos (apenas se consentimento LGPD estiver ativo)
        pontos_ganhos = int(valor_final // 10) if cliente_pedido.consentimento_lgpd else 0
        cliente_pedido.pontos_fidelidade = (
            cliente_pedido.pontos_fidelidade - dados.usar_pontos_fidelidade + pontos_ganhos
        )
        acao_log = "PAGAMENTO_APROVADO"
        detalhe_log = f"Transação {transacao_id} | Pago: R$ {valor_final:.2f} | Pontos ganhos: {pontos_ganhos}"
    else:
        status_pgto = StatusPagamento.RECUSADO
        acao_log = "PAGAMENTO_RECUSADO"
        detalhe_log = f"Transação {transacao_id} recusada pelo gateway mock."

    pagamento = Pagamento(
        pedido_id=pedido.id,
        metodo=dados.metodo.upper(),
        valor=valor_final,
        status=status_pgto,
        transacao_externa_id=transacao_id,
    )
    db.add(pagamento)
    db.flush()

    registrar_auditoria(
        db=db,
        usuario_id=usuario.id,
        acao=acao_log,
        entidade="Pagamento",
        entidade_id=pagamento.id,
        detalhes=detalhe_log,
    )
    db.commit()
    db.refresh(pagamento)
    return pagamento


@router.patch("/{pedido_id}/status", response_model=PedidoOut)
def atualizar_status_pedido(
    pedido_id: int,
    dados: PedidoStatusIn,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise RecursoNaoEncontradoError("Pedido não encontrado.")

    if pedido.status in (StatusPedido.CANCELADO, StatusPedido.ENTREGUE):
        raise ConflitoNegocioError(
            f"Não é possível alterar um pedido já '{pedido.status.value}'."
        )

    # Cliente só pode cancelar pedido próprio que ainda aguarda pagamento
    if usuario.perfil == PerfilUsuario.CLIENTE:
        if pedido.usuario_id != usuario.id:
            raise AcessoNegadoError("Você não tem permissão para alterar este pedido.")
        if dados.status != StatusPedido.CANCELADO or pedido.status != StatusPedido.AGUARDANDO_PAGAMENTO:
            raise AcessoNegadoError(
                "Clientes só podem cancelar pedidos próprios que ainda estejam aguardando pagamento."
            )

    status_anterior = pedido.status
    pedido.status = dados.status

    # Estorna estoque da unidade e marca pagamentos aprovados como estornados em caso de cancelamento
    if dados.status == StatusPedido.CANCELADO:
        for item in pedido.itens:
            estoque = (
                db.query(EstoqueUnidade)
                .filter(
                    EstoqueUnidade.unidade_id == pedido.unidade_id,
                    EstoqueUnidade.produto_id == item.produto_id,
                )
                .first()
            )
            if estoque:
                estoque.quantidade += item.quantidade

        for pgto in pedido.pagamentos:
            if pgto.status == StatusPagamento.APROVADO:
                pgto.status = StatusPagamento.ESTORNADO

    registrar_auditoria(
        db=db,
        usuario_id=usuario.id,
        acao="ATUALIZACAO_STATUS_PEDIDO",
        entidade="Pedido",
        entidade_id=pedido.id,
        detalhes=f"Status: {status_anterior.value} -> {dados.status.value}",
    )
    db.commit()
    db.refresh(pedido)
    return pedido