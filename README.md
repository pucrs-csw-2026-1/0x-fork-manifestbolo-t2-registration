# manifestbolo-t2-registration

Microsserviço responsável por gerenciar inscrições de usuários em eventos da plataforma ManifestoBolo.

---

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/health` | Health check da aplicação |
| `GET` | `/events/available` | Lista eventos com vagas disponíveis |
| `GET` | `/events/{event_id}/registrations` | Lista inscritos de um evento |
| `POST` | `/events/{event_id}/guests` | Inscreve um convidado em um evento |
| `DELETE` | `/events/{event_id}/guests/{user_id}` | Cancela a inscrição de um convidado |
| `GET` | `/events/{event_id}/guests/{user_id}/check-in` | Valida inscrição para check-in (uso interno) |
| `POST` | `/events/confirmation/{confirmation_id}` | Confirma inscrição via código alfanumérico |

> Todos os endpoints de registro retornam `501 Not Implemented` — a estrutura de banco e contratos de API estão definidos, a lógica de negócio ainda não foi implementada.

---

## Modelagem Conceitual

### Entidades

**`Registration`** — entidade central do serviço. Representa a inscrição de um usuário em um evento.

| Atributo | Tipo | Notas |
|---|---|---|
| `event_id` | UUID | PK composta — referência ao evento externo |
| `user_id` | UUID | PK composta — referência ao usuário externo |
| `registration_timestamp` | TIMESTAMP WITH TZ | Preenchido automaticamente |
| `confirmation_timestamp` | TIMESTAMP WITH TZ | Nullable — preenchido ao confirmar |

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

### Entidades Externas

`User` e `Event` são gerenciados por outros microsserviços e consumidos via HTTP. Este serviço não possui tabelas para eles — os contratos estão em `src/domain/auth/schemas.py` e `src/domain/events/schemas.py`.

### Diagrama de Sequência — Inscrição de Convidado

```mermaid
sequenceDiagram
    actor Cliente
    participant Controller as RegistrationController
    participant Service as RegistrationService
    participant AuthClient
    participant EventsClient
    participant Repo as RegistrationRepository
    participant DB as PostgreSQL
    participant AuthSvc as auth-service
    participant EventsSvc as events-service

    Cliente->>Controller: POST /events/{event_id}/guests<br/>{userId}

    Controller->>Service: register(event_id, user_id)

    %% Validação do usuário
    Service->>AuthClient: get_user_by_id(user_id)
    AuthClient->>AuthSvc: GET /users/{user_id}
    alt Usuário não encontrado
        AuthSvc-->>AuthClient: 404 Not Found
        AuthClient-->>Service: None
        Service-->>Controller: raise HTTPException 404
        Controller-->>Cliente: 404 User not found
    else Usuário encontrado
        AuthSvc-->>AuthClient: 200 UserResponse
        AuthClient-->>Service: UserResponse
    end

    %% Validação do evento e capacidade
    Service->>EventsClient: get_event_by_id(event_id)
    EventsClient->>EventsSvc: GET /events/{event_id}
    alt Evento não encontrado
        EventsSvc-->>EventsClient: 404 Not Found
        EventsClient-->>Service: None
        Service-->>Controller: raise HTTPException 404
        Controller-->>Cliente: 404 Event not found
    else Evento encontrado
        EventsSvc-->>EventsClient: 200 EventResponse
        EventsClient-->>Service: EventResponse (maxCapacity)
    end

    %% Verificação de vagas
    Service->>Repo: count_by_event(event_id)
    Repo->>DB: SELECT COUNT(*) FROM registrations<br/>WHERE event_id = ?
    DB-->>Repo: registeredCount
    Repo-->>Service: registeredCount

    alt Sem vagas (registeredCount >= maxCapacity)
        Service-->>Controller: raise HTTPException 409
        Controller-->>Cliente: 409 Event is full
    end

    %% Verificação de inscrição duplicada
    Service->>Repo: get_by_event_and_user(event_id, user_id)
    Repo->>DB: SELECT * FROM registrations<br/>WHERE event_id = ? AND user_id = ?
    DB-->>Repo: Registration | None
    Repo-->>Service: Registration | None

    alt Já inscrito
        Service-->>Controller: raise HTTPException 409
        Controller-->>Cliente: 409 User already registered
    end

    %% Criação da inscrição
    Service->>Repo: create(event_id, user_id)
    Repo->>DB: INSERT INTO registrations<br/>(event_id, user_id, registration_timestamp)
    alt IntegrityError (race condition)
        DB-->>Repo: IntegrityError
        Repo-->>Service: raise IntegrityError
        Service-->>Controller: raise HTTPException 409
        Controller-->>Cliente: 409 User already registered
    else Sucesso
        DB-->>Repo: Registration
        Repo-->>Service: Registration
        Service-->>Controller: Registration
        Controller-->>Cliente: 201 GuestRegistrationResponse
    end
```

### Diagrama ERD

```mermaid
erDiagram
    REGISTRATIONS {
        uuid event_id PK
        uuid user_id PK
        timestamptz registration_timestamp
        timestamptz confirmation_timestamp
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
- **Cancelamento**: DELETE físico — não há `cancelled_at` ou campo `status` em `Registration`.
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
