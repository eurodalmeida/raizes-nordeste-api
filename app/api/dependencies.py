from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.domain.enums import PerfilUsuario
from app.domain.exceptions import AcessoNegadoError, NaoAutenticadoError
from app.infrastructure.database import get_db
from app.infrastructure.models import LogAuditoria, Usuario
from app.infrastructure.security import decodificar_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Usuario:
    payload = decodificar_token(token)
    user_id = payload.get("sub")
    if not user_id:
        raise NaoAutenticadoError("Token inválido.")

    usuario = db.query(Usuario).filter(Usuario.id == int(user_id)).first()
    if not usuario:
        raise NaoAutenticadoError("Usuário não encontrado.")

    return usuario


def exigir_perfis(*perfis_permitidos: PerfilUsuario):
    def verificar_perfil(usuario: Usuario = Depends(get_current_user)) -> Usuario:
        if usuario.perfil not in perfis_permitidos:
            raise AcessoNegadoError(
                f"Acesso restrito aos perfis: {[p.value for p in perfis_permitidos]}."
            )
        return usuario

    return verificar_perfil


def registrar_auditoria(
    db: Session,
    usuario_id: int | None,
    acao: str,
    entidade: str,
    entidade_id: int | None = None,
    detalhes: str | None = None,
) -> None:
    log = LogAuditoria(
        usuario_id=usuario_id,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhes=detalhes,
    )
    db.add(log)