# Plataforma de Gestão Operacional de Aeroporto — Backend

API REST do Projeto Integrador (aeroporto de Cape Town). FastAPI + SQLAlchemy + Alembic + MySQL.

O frontend que consome esta API está em [`entrega-front`](../entrega-front).

## Modelo de dados

8 tabelas, criadas do zero e normalizadas:

| Tabela | Papel |
|---|---|
| `terminais` | Terminal nacional / internacional |
| `vagas` | Posições de estacionamento (gate ou remota), pertencem a um terminal |
| `aeronaves` | Prefixo, modelo, companhia e **capacidade** (define os assentos do voo) |
| `voos` | Origem, destino, horários, status e vínculo com aeronave e terminal |
| `alocacoes_vaga` | **Tabela intermediária voo ↔ vaga** — qual voo ocupa qual posição, e por quê |
| `passageiros` | Cadastro de passageiros |
| `reservas` | **Tabela intermediária passageiro ↔ voo** (N:M) — carrega assento e estado operacional |
| `bagagens` | Mala despachada, apontando para **uma única reserva** (um dono, um voo) |

Relações exigidas pelo enunciado:

- **Um voo tem vários passageiros** → `voos` 1:N `reservas`
- **Um passageiro pode estar em vários voos** → N:M resolvido pela tabela intermediária `reservas`
- **Um passageiro despacha várias malas, mas uma mala tem um só dono** → `reservas` 1:N `bagagens`

A **ocupação do voo é derivada**, nunca armazenada:
`ocupados = COUNT(reservas com status CONFIRMADA | CHECK_IN_FEITO | EMBARCADA)`.

## Regras de negócio

**Status do voo (máquina de estados)**

```
NO_HORARIO → ATRASADO | EMBARQUE | CANCELADO
ATRASADO   → EMBARQUE | CANCELADO
EMBARQUE   → FINALIZADO | CANCELADO
FINALIZADO, CANCELADO → estados terminais
```

Transição inválida devolve **409**. Ao finalizar, quem estava com check-in feito vira `EMBARCADA` e a
vaga é liberada. Ao cancelar, as reservas ativas caem em cascata e a vaga volta a ficar `LIVRE`.

**Reservas** — só em voo que aceita reserva, com assento disponível e sem duplicidade.
Check-in exige reserva `CONFIRMADA`; no-show só depois que o voo entra em embarque.
**Realocação** exige `NO_SHOW` (ou voo cancelado) e um voo destino com o **mesmo destino**, partida
futura e lugar livre — a reserva antiga vira `REALOCADA` e **as bagagens acompanham o passageiro**.

**Vagas** — a vaga precisa estar livre, sem sobreposição de período, e **no mesmo terminal do voo**.

**Bagagens** — `DESPACHADA → EM_TRIAGEM → CARREGADA → ENTREGUE`, com `EXTRAVIADA` acessível a partir
de qualquer estado não-final.

## Arquitetura

```
src/
  models/        SQLAlchemy (persistência)
  entities/      schemas Pydantic (contratos de entrada/saída)
  repositories/  acesso a dados
  use_cases/     regras de negócio
  routes/        APIRouters (/api/...)
  middlewares/   CORS e tratamento global de erros
  utils/         enums, exceções e geração de assentos
  main.py        create_app()
  seed.py        dados de demonstração
```

Erros de domínio (`src/utils/exceptions.py`) viram JSON `{"detail": ..., "codigo": ...}`:
**404** não encontrado · **422** regra de negócio · **409** conflito de estado.

## Como rodar

1. Configure o `.env` (use o `.env.example` como base):

```bash
cp .env.example .env
```

2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Crie o banco e aplique as migrations:

```bash
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS entrega;"
```

```bash
python -m alembic upgrade head
```

4. Popule com o cenário de demonstração:

```bash
python -m src.seed
```

5. Suba a API:

```bash
uvicorn src.main:app --reload
```

Documentação interativa (Swagger) em **http://localhost:8000/docs**.

## Principais endpoints

| Recurso | Endpoints |
|---|---|
| Dashboard | `GET /api/dashboard/resumo` |
| Terminais | CRUD em `/api/terminais` + `GET /{id}/vagas` |
| Vagas | CRUD em `/api/vagas` (filtros `terminal_id`, `status`, `tipo`) |
| Aeronaves | CRUD em `/api/aeronaves` + `GET /{id}/voos` |
| Voos | CRUD em `/api/voos` (filtros `status`, `terminal_id`, `origem`, `destino`, `data`, `sentido`, `busca`)<br>`PATCH /{id}/status` · `GET /{id}/passageiros` · `GET /{id}/ocupacao` · `GET /{id}/bagagens`<br>`POST /{id}/alocacoes` · `PATCH /{id}/alocacoes/{alocacao_id}/liberar` |
| Passageiros | CRUD em `/api/passageiros` + `GET /{id}/reservas` + `GET /{id}/bagagens` |
| Reservas | `GET`/`POST` em `/api/reservas` · `PATCH /{id}/check-in` · `PATCH /{id}/no-show`<br>`POST /{id}/realocar` · `DELETE /{id}` (cancela) |
| Bagagens | `GET`/`POST` em `/api/bagagens` · `PATCH /{id}/status` · `GET /rastreio/{etiqueta}` |
