# Raízes do Nordeste - API Omnichannel

API REST em Python (FastAPI) para gerenciar pedidos multicanal (App, Web, Totem e Balcão), estoque por unidade, pagamento simulado, fidelidade e auditoria da rede Raízes do Nordeste.

## Links e Artefatos do Projeto

- **Repositório Git:** [https://github.com/eurodalmeida/raizes-nordeste-api](https://github.com/eurodalmeida/raizes-nordeste-api)
- **Swagger / OpenAPI local:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Coleção Postman:** `Raizes_Nordeste_API.postman_collection.json` (na raiz deste repositório)

## Requisitos e Estrutura

- Python 3.10+, FastAPI, SQLAlchemy, Pydantic, PyJWT e Pytest.
- `app/domain`: enums de domínio (`CanalPedido`, `PerfilUsuario`, `StatusPedido`, `StatusPagamento`) e exceções de negócio.
- `app/infrastructure`: banco SQLite, modelos relacionais e segurança (hash bcrypt e JWT).
- `app/api`: schemas, tratamento padronizado de erros e rotas (`/auth`, `/catalogo`, `/pedidos`, `/auditoria`).
- `tests`: suíte automatizada com `pytest`.

## Como executar localmente

1. Copie o arquivo de variáveis de ambiente:
```powershell
copy .env.example .env
```

2. Crie e ative o ambiente virtual e instale as dependências:
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

3. Crie as tabelas e popule os dados iniciais:
```powershell
python seed.py
```

4. Inicie o servidor:
```powershell
uvicorn main:app --reload
```

Acesse `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)` para testar via Swagger ou importe `Raizes_Nordeste_API.postman_collection.json` no Postman.

## Usuários padrão (`seed.py`)

- **Gerente:** `gerente@raizes.com` | Senha: `123456`
- **Atendente:** `atendente@raizes.com` | Senha: `123456`
- **Cliente:** `cliente@raizes.com` | Senha: `123456`

## Testes Automatizados

```powershell
pytest -v
```