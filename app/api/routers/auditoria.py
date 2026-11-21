from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.dependencies import exigir_perfis
from app.api.schemas import LogAuditoriaOut
from app.domain.enums import PerfilUsuario
from app.infrastructure.database import get_db
from app.infrastructure.models import LogAuditoria, Usuario

router = APIRouter(prefix="/auditoria", tags=["Auditoria e Governança"])


@router.get("/logs", response_model=list[LogAuditoriaOut])
def listar_logs_auditoria(
    limite: int = 50,
    db: Session = Depends(get_db),
    gerente: Usuario = Depends(exigir_perfis(PerfilUsuario.GERENTE)),
):
    return (
        db.query(LogAuditoria)
        .order_by(LogAuditoria.id.desc())
        .limit(limite)
        .all()
    )