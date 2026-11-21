import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from app.api.error_handler import registrar_error_handlers

app = FastAPI(
    title="Raízes do Nordeste API",
    description="API REST Omnichannel para gestão de pedidos, estoque local, pagamento mock e fidelidade.",
    version="1.0.0",
)

registrar_error_handlers(app)


@app.get("/health", tags=["Sistema"])
def health_check():
    return {"status": "ok", "servico": "Raízes do Nordeste API"}