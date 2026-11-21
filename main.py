import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from app.api.error_handler import registrar_error_handlers
from app.api.routers import auditoria, auth, catalogo, pedidos
from app.infrastructure.database import Base, engine
from app.infrastructure import models  # noqa: F401

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Raízes do Nordeste API",
    description="API REST Omnichannel para gestão de pedidos, estoque local, pagamento mock e fidelidade.",
    version="1.0.0",
)

registrar_error_handlers(app)
app.include_router(auth.router)
app.include_router(catalogo.router)
app.include_router(pedidos.router)
app.include_router(auditoria.router)


@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "servico": "Raízes do Nordeste API"}