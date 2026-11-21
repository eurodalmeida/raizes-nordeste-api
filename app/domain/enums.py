from enum import Enum

class PerfilUsuario(str, Enum):
    CLIENTE = 'CLIENTE'
    ATENDENTE = 'ATENDENTE'
    GERENTE = 'GERENTE'

class CanalPedido(str, Enum):
    APP = 'APP'
    WEB = 'WEB'
    TOTEM = 'TOTEM'
    BALCAO = 'BALCAO'

class StatusPedido(str, Enum):
    AGUARDANDO_PAGAMENTO = 'AGUARDANDO_PAGAMENTO'
    PAGO = 'PAGO'
    EM_PREPARO = 'EM_PREPARO'
    PRONTO = 'PRONTO'
    ENTREGUE = 'ENTREGUE'
    CANCELADO = 'CANCELADO'

class StatusPagamento(str, Enum):
    PENDENTE = 'PENDENTE'
    APROVADO = 'APROVADO'
    RECUSADO = 'RECUSADO'
    ESTORNADO = 'ESTORNADO'
