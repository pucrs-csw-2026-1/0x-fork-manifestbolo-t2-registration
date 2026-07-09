# 0002. Publicação de Eventos de Domínio via SNS

**Data:** 2026-07-05

## Status

Aceito

## Contexto

Outros serviços da plataforma (em particular o serviço de Metrics) precisam ser notificados quando uma inscrição é confirmada ou cancelada neste serviço. A comunicação deve ser assíncrona e desacoplada — o `registration` não deve depender da disponibilidade do consumidor para responder às requisições HTTP que originam esses eventos.

Foi decidido usar SNS (via uma Ministack/LocalStack compartilhada com o restante da plataforma) para publicar eventos leves de domínio: `RegistrationConfirmed` e `RegistrationCancelled`. `CheckInPerformed` ficou fora de escopo porque hoje não existe nenhuma escrita de estado associada a check-in neste serviço — o endpoint `GET /events/{event_id}/guests/{user_id}/check-in` é só uma consulta de validação.

Havia três decisões de design a resolver:

1. **Onde encaixar o publisher na arquitetura existente.** O ADR-0001 já estabeleceu o padrão de isolar cada integração externa em `src/domain/<nome>/` com `client.py`/`schemas.py`. Optamos por seguir o mesmo padrão para o SNS, ainda que a integração não seja HTTP: `src/domain/notifications/` com `publisher.py` e `schemas.py`.
2. **Como injetar o publisher no `RegistrationService`.** `EventsClient`/`AuthClient` são passados como parâmetro dos métodos que precisam deles (`register`, `register_activity`), porque `confirm` e `cancel_registration` nunca precisaram de um client externo antes. Como a publicação de eventos é um efeito colateral do próprio service (não uma dependência de validação de uma chamada específica), o `SnsEventPublisher` é injetado no `__init__` do `RegistrationService`, como estado do objeto, resolvido via `Depends` na fábrica `get_registration_service`. O parâmetro é opcional (`= None`) para não quebrar os testes existentes que instanciam `RegistrationService(repository)` diretamente sem publisher.
3. **`resource_ref` sem um id único de inscrição.** `Registration` tem chave primária composta (`event_id`, `user_id`), sem UUID próprio. Optamos por serializar o par como `f"{event_id}:{user_id}"` — determinístico, parseável e suficiente para o consumidor localizar o recurso via os endpoints existentes deste serviço.

## Decisão

```
src/domain/
└── notifications/
    ├── schemas.py     ← DomainEvent, DomainEventType (contrato do evento)
    └── publisher.py   ← SnsEventPublisher + get_sns_event_publisher
```

- O contrato do evento publicado é fixo e leve: `event_id` (id do Evento pai, não da inscrição), `event_type`, `source` (nome do tópico), `occurred_at` (ISO 8601 UTC) e `resource_ref` (a PK composta serializada).
- `SnsEventPublisher.publish(event)` nunca propaga exceção. Tenta publicar até 3 vezes no total (1 tentativa inicial + 2 retries, com 200ms/400ms de backoff); se todas falharem, loga um erro estruturado (`event_type`, `event_id`, `resource_ref`, motivo) e retorna normalmente — a resposta HTTP da operação que disparou o evento nunca é afetada por falha de publicação (best-effort, não outbox transacional).
- O ARN do tópico SNS é resolvido em runtime via `sns_client.create_topic(Name=settings.SNS_REGISTRATION_TOPIC_NAME)` (operação idempotente do SNS — retorna o ARN existente se o tópico já tiver sido criado, por exemplo pelo Terraform de outro serviço da plataforma). Este serviço não cria `aws_sns_topic` via Terraform próprio. O ARN é cacheado na instância do publisher após a primeira resolução.
- O disparo acontece sempre depois do commit da transição de estado (`repository.update_status(...)`), nunca antes, e nunca de forma bloqueante dentro da mesma transação de banco.
- `RegistrationService.cancel_registration` só publica `RegistrationCancelled` quando o status realmente muda para `CANCELLED` — chamadas repetidas em uma inscrição já cancelada continuam idempotentes e não republicam o evento.

## Consequências

- **Positivo:** o padrão de isolamento já validado pelo ADR-0001 é reaproveitado sem modificações — quem já entende a estrutura de `auth/`/`events/` reconhece `notifications/` de imediato.
- **Positivo:** testes do `RegistrationService` continuam funcionando sem publisher (parâmetro opcional), e os testes de publicação usam `moto` para mockar o SNS de ponta a ponta via `TestClient`.
- **Positivo:** a resolução de ARN via `create_topic` idempotente evita duplicar a definição do tópico em múltiplos módulos Terraform de serviços diferentes.
- **Negativo:** o publisher é resolvido a cada request (sem singleton entre requests), então `create_topic` é chamado ocasionalmente mais de uma vez entre requests diferentes — aceitável porque a operação é idempotente e barata, mas pode ser revisitado com um singleton por processo se isso se mostrar um problema de performance.
- **Negativo:** `resource_ref` como string composta (`event_id:user_id`) exige que o consumidor (Metrics) saiba parsear esse formato — não é um UUID opaco único. Isso deve ser validado com quem mantém o consumidor antes de considerar o fluxo de ponta a ponta como concluído.
