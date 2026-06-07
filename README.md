# manifestbolo-t2-registration

Microsserviço responsável por gerenciar inscrições de usuários em eventos da plataforma ManifestoBolo.

---

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Health check da aplicação |
| `GET` | `/auth/me` | Valida o token (RS256/JWKS) e retorna o principal autenticado |
| `GET` | `/events/available` | Lista eventos com vagas disponíveis |
| `GET` | `/events/{event_id}/registrations` | Lista inscritos de um evento |
| `POST` | `/activities/registrations` | Cria uma inscrição em atividade |
| `GET` | `/activities/{activity_id}/users/{user_id}` | Busca uma inscrição de atividade por atividade e usuário |
| `POST` | `/events/{event_id}/guests` | Inscreve um convidado em um evento |
| `GET` | `/events/{event_id}/guests/{user_id}/check-in` | Valida inscrição para check-in (uso interno) |
| `POST` | `/events/confirmation/{confirmation_id}` | Confirma inscrição via código alfanumérico |

> Todos os endpoints de registro retornam `501 Not Implemented` — a estrutura de banco e contratos de API estão definidos, a lógica de negócio ainda não foi implementada.

---

## Executando com containers

O projeto roda inteiramente via **Docker Compose** — não é preciso instalar Python,
Postgres ou dependências na máquina. São dois serviços: `app` (a API, porta `8000`)
e `db` (Postgres, interno à rede do Compose). As migrations do Alembic rodam
automaticamente no start do `app`.

### Pré-requisito: o Auth Service no ar

Este serviço **valida os tokens** emitidos pelo Auth Service (projeto `0x_t1`),
então o Auth precisa estar rodando e publicando a porta `8080` no host. Na pasta
do Auth:

```bash
docker compose up -d        # sobe o Auth em http://localhost:8080
```

O `app` alcança o Auth pela porta publicada no host (`host.docker.internal:8080`),
configurada em `AUTH_SERVICE_BASE_URL` no `app/docker-compose.yml`. Por isso **não
há acoplamento à rede interna do Auth** — basta a porta `8080` estar publicada.

### Subir / parar este serviço

A partir da pasta `app/`:

```bash
docker compose up -d --build   # sobe a API (build na primeira vez) em :8000
docker compose ps              # status dos containers
docker compose logs -f app     # acompanha os logs da API
docker compose down            # para os containers (mantém os dados do Postgres)
docker compose down -v         # para e apaga os dados (zera o banco)
```

- **Swagger UI:** http://localhost:8000/docs
- **Health:** http://localhost:8000/health

---

## Integração com o Auth Service

O Auth assina JWTs em **RS256** e publica a chave pública via **JWKS**
(`GET {AUTH}/.well-known/jwks.json`). Este serviço valida os tokens **localmente**,
com a chave pública — sem segredo compartilhado e sem chamar o Auth a cada request.

- Implementação: [`src/domain/auth/security.py`](./app/src/domain/auth/security.py)
  — busca e cacheia o JWKS, valida assinatura `RS256` + `exp` e expõe os claims
  como um `Principal`.
- A dependency `get_current_principal` protege rotas; `require_scopes("...")`
  exige scopes específicos.
- Configuração: `AUTH_SERVICE_BASE_URL` (em `.env` / `docker-compose.yml`).

### Testando com um token

1. Obtenha um token no Auth (usuário admin de dev):

   ```bash
   TOKEN=$(curl -s -X POST http://localhost:8080/auth/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin@local.dev&password=Admin@123" \
     | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
   ```

2. Chame a rota protegida `GET /auth/me`:

   ```bash
   # sem token -> 403
   curl -i http://localhost:8000/auth/me

   # com token -> 200 + claims do token
   curl -s -H "Authorization: Bearer $TOKEN" http://localhost:8000/auth/me
   ```

   Resposta esperada (200):

   ```json
   {
     "sub": "8f2abf15-909a-4cee-b06d-fedf9be94c65",
     "scopes": ["participant", "manager", "admin"],
     "principal_type": "user",
     "email": "admin@local.dev"
   }
   ```

> Para proteger outras rotas, adicione `Depends(get_current_principal)` (ou
> `Depends(require_scopes("participant"))`) na assinatura do endpoint.

---

## Modelagem Conceitual

### Entidades

**`Registration`** — entidade central do serviço. Representa a inscrição de um usuário em um evento.

| Atributo | Tipo | Notas |
|---|---|---|
| `event_id` | UUID | PK composta — referência ao evento externo |
| `user_id` | UUID | PK composta — referência ao usuário externo |
| `status` | ENUM(`REGISTERED`, `CONFIRMED`) | Status atual da inscrição |
| `created_at` | TIMESTAMP WITH TZ | Preenchido automaticamente |
| `updated_at` | TIMESTAMP WITH TZ | Nullable — preenchido automaticamente |

**`ConfirmationToken`** — token temporário usado para confirmar a inscrição via código alfanumérico.

| Atributo | Tipo | Notas |
|---|---|---|
| `confirmation_id` | UUID | PK |
| `user_id` | UUID | Referência ao usuário (sem FK — integridade via aplicação) |
| `event_id` | UUID | Referência ao evento (sem FK — integridade via aplicação) |
| `codigo` | VARCHAR(8) | Alfanumérico, 6–8 caracteres, gerado pelo backend |
| `created_at` | TIMESTAMP WITH TZ | Automático |
| `updated_at` | TIMESTAMP WITH TZ | Nullable — preenchido quando a confirmação é realizada |
| `expires_at` | TIMESTAMP WITH TZ | Controla a validade do token |

**`HealthLog`** — log de execução do health check (entidade de infraestrutura).

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | UUID | PK |
| `checked_at` | TIMESTAMP WITH TZ | Automático |
| `status` | VARCHAR(32) | Ex: `"ok"` |

**`ActivityRegistration`** — tabela de atividades por usuário e seção.

| Atributo | Tipo | Notas |
|---|---|---|
| `activity_id` | UUID | PK composta — referência à atividade externa |
| `user_id` | UUID | PK composta — referência ao usuário externo |
| `updated_at` | TIMESTAMP WITH TZ | Atualizado automaticamente |
| `created_at` | TIMESTAMP WITH TZ | Criado automaticamente |

### Entidades Externas

`User` e `Event` são gerenciados por outros microsserviços e consumidos via HTTP. Este serviço não possui tabelas para eles — os contratos estão em `src/domain/auth/schemas.py` e `src/domain/events/schemas.py`.

### Diagrama ERD

```mermaid
erDiagram
    REGISTRATIONS {
        uuid event_id PK
        uuid user_id PK
        enum status "REGISTERED|CONFIRMED"
        timestamptz created_at
        timestamptz updated_at
    }

    CONFIRMATION_TOKENS {
        uuid confirmation_id PK
        uuid user_id FK
        uuid event_id FK
        varchar_8 codigo
        timestamptz created_at
        timestamptz updated_at
        timestamptz expires_at
    }

    HEALTH_LOG {
        uuid id PK
        timestamptz checked_at
        varchar_32 status
    }

    ACTIVITY_REGISTRATIONS {
        uuid activity_id PK
        uuid user_id PK
        timestamptz updated_at
        timestamptz created_at
    }

    USER["USER (externo — auth-service)"] {
        uuid id PK
    }

    EVENT["EVENT (externo — events-service)"] {
        uuid id PK
    }

    USER ||--o{ REGISTRATIONS : "inscreve-se em"
    EVENT ||--o{ REGISTRATIONS : "recebe inscrições de"
    REGISTRATIONS ||--o| CONFIRMATION_TOKENS : "confirmada por"
```

### Relacionamentos

```
[auth-service]          [events-service]
     │                        │
  AuthClient             EventsClient
     │                        │
     └────────┬───────────────┘
              │ (injeção de dependência)
              ▼
      RegistrationService
              │
     ┌────────┴────────┐
     ▼                 ▼
Registration ──1:1──► ConfirmationToken
(event_id PK,        (confirmation_id PK,
 user_id PK)          user_id + event_id idx)
```

| Relacionamento | Cardinalidade | Regra |
|---|---|---|
| User → Registration | 1:N | Um usuário pode se inscrever em vários eventos |
| Event → Registration | 1:N | Um evento pode ter vários inscritos |
| (user_id, event_id) → Registration | UNIQUE | Impede inscrição duplicada |
| Registration → ConfirmationToken | 1:1 lógico | Um token por par `(user_id, event_id)`, indexado — sem FK declarada |

### Regras de Integridade

- **Inscrição duplicada**: bloqueada no `RegistrationService` via HTTP 409 antes do INSERT, com fallback em `IntegrityError`.
- **Token expirado**: controlado por `expires_at`; validação ocorre na camada de serviço.
- **Confirmação**: preenche `updated_at` em `ConfirmationToken` e `confirmation_timestamp` em `Registration`.
- **Integridade referencial** com `User` e `Event`: garantida pela aplicação, não por FK no banco.

---

## Arquitetura

Este serviço segue a decisão registrada em [ADR-0001](./app/documentation/adrs/0001-separacao-clients-http-por-microsservico-externo.md): cada microsserviço externo tem um domínio isolado com `client.py` e `schemas.py` dedicados.

```
src/domain/
├── auth/
│   ├── client.py      ← chamadas HTTP ao auth-service
│   └── schemas.py     ← modelos das respostas do auth-service
├── events/
│   ├── client.py      ← chamadas HTTP ao events-service
│   └── schemas.py     ← modelos das respostas do events-service
├── health/
│   ├── controller.py
│   ├── model.py
│   ├── repository.py
│   ├── schemas.py
│   └── service.py
└── registration/
    ├── controller.py
    ├── model.py
    ├── repository.py
    ├── schemas.py
    └── service.py     ← orquestra AuthClient e EventsClient via injeção
```

---

## Lint e Formatação (Ruff)

O projeto usa [Ruff](https://docs.astral.sh/ruff/) para lint e formatação. A configuração está em [`app/pyproject.toml`](./app/pyproject.toml) (regras `E`, `F`, `I`, `N`, `UP`, `B`, `SIM` com `force-sort-within-sections = true` para o isort).

**Antes de qualquer `git push`**, rode os dois comandos a partir da pasta `app/`:

```bash
ruff check . --fix    # aplica lint + ordena imports (regra I001)
ruff format .         # formata o código (aspas, espaços, quebras de linha)
```

Para apenas validar (sem alterar arquivos), como faz o CI:

```bash
ruff check .
ruff format --check .
```

A pipeline do GitHub Actions roda `ruff check app/ --output-format=github` e falha o build se houver qualquer erro — então é mais rápido corrigir localmente antes de pushar.
