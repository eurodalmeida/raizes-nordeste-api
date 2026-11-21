from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, registrar_auditoria
from app.api.schemas import TokenOut, UsuarioOut, UsuarioRegistroIn
from app.domain.enums import PerfilUsuario
from app.domain.exceptions import ConflitoNegocioError, NaoAutenticadoError
from app.infrastructure.database import get_db
from app.infrastructure.models import Usuario
from app.infrastructure.security import (
    criar_token_acesso,
    gerar_hash_senha,
    verificar_senha,
)

router = APIRouter(prefix="/auth", tags=["Autenticação"])


@router.post("/register", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registrar_cliente(dados: UsuarioRegistroIn, db: Session = Depends(get_db)):
    if not dados.consentimento_lgpd:
        raise ConflitoNegocioError(
            "É obrigatório aceitar o termo de consentimento LGPD para concluir o cadastro."
        )

    existente = db.query(Usuario).filter(Usuario.email == dados.email).first()
    if existente:
        raise ConflitoNegocioError("Já existe um usuário cadastrado com este e-mail.")

    novo_usuario = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=gerar_hash_senha(dados.senha),
        perfil=PerfilUsuario.CLIENTE,
        consentimento_lgpd=True,
        data_consentimento=datetime.now(timezone.utc),
    )
    db.add(novo_usuario)
    db.flush()

    registrar_auditoria(
        db=db,
        usuario_id=novo_usuario.id,
        acao="CADASTRO_CLIENTE",
        entidade="Usuario",
        entidade_id=novo_usuario.id,
        detalhes="Cadastro realizado com consentimento LGPD ativo.",
    )
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


@router.post("/login", response_model=TokenOut)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    usuario = db.query(Usuario).filter(Usuario.email == form_data.username).first()
    if not usuario or not verificar_senha(form_data.password, usuario.senha_hash):
        raise NaoAutenticadoError("E-mail ou senha inválidos.")

    token = criar_token_acesso(
        {"sub": str(usuario.id), "perfil": usuario.perfil.value}
    )
    return TokenOut(access_token=token)


@router.get("/me", response_model=UsuarioOut)
def perfil_atual(usuario: Usuario = Depends(get_current_user)):
    return usuario