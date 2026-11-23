# Raízes do Nordeste - API Omnichannel

API REST em FastAPI para gerenciar pedidos multicanal (App, Web, Totem e Balcão), estoque por unidade, pagamento simulado e pontos de fidelidade da rede Raízes do Nordeste.

## Estrutura das pastas

- `app/domain`: enums de status/perfis e exceções de regra de negócio.
- `app/infrastructure`: conexão com SQLite, modelos do SQLAlchemy e autenticação JWT.
- `app/api`: schemas do Pydantic, tratamento de erros e rotas (`/auth`, `/catalogo`, `/pedidos`, `/auditoria`).
- `tests`: testes automatizados com `pytest`.

## Como rodar o projeto

1. Ative o ambiente virtual e instale as dependências:
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Popule o banco inicial com dados de teste:
```powershell
python seed.py
```

3. Suba o servidor:
```powershell
uvicorn main:app --reload
```

Depois é só abrir `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)` no navegador.

## Logins de teste (`seed.py`)

- Gerente: `gerente@raizes.com` (senha: `123456`)
- Atendente: `atendente@raizes.com` (senha: `123456`)
- Cliente: `cliente@raizes.com` (senha: `123456`)

## Testes

```powershell
pytest -v
```