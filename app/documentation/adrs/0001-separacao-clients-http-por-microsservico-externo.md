# 0001. Separação de Clientes HTTP em Domínios Independentes por Microsserviço Externo

**Data:** 2026-05-14

## Status

Aceito

## Contexto

O serviço `manifestbolo-t2-registration` é um microsserviço responsável por gerenciar inscrições de usuários em eventos. Para cumprir suas responsabilidades, ele precisa se comunicar com dois outros microsserviços da plataforma:

- **Auth Service**: para validar tokens e obter dados do usuário autenticado.
- **Events Service**: para listar eventos cadastrados, consultar capacidade máxima e verificar datas de encerramento.

A abordagem mais simples seria colocar todas as chamadas HTTP diretamente no `RegistrationService`, dentro do domínio `registration`. Porém, isso criaria um acoplamento implícito entre a lógica de negócio de inscrições e os detalhes de implementação de cada integração externa, tornando o código difícil de manter, testar e evoluir.

Alternativas consideradas:

1. **Concentrar tudo no `RegistrationService`**: simples de implementar inicialmente, mas viola o Princípio da Responsabilidade Única (SRP) e dificulta testes unitários, pois exige mocks de múltiplos sistemas em um único lugar.
2. **Usar um módulo genérico `http_clients.py`**: elimina algum acoplamento, mas agrupa clientes não relacionados e não reflete a linguagem do domínio.
3. **Criar um domínio isolado por microsserviço externo** _(decisão adotada)_: cada integração externa tem seu próprio módulo dentro de `src/domain/`, com `client.py` e `schemas.py` dedicados.

## Decisão

Adotamos a criação de domínios isolados para cada microsserviço externo com o qual este serviço se comunica:

```
src/domain/
├── auth/
│   ├── client.py    ← chamadas HTTP ao auth-service
│   └── schemas.py   ← modelos das respostas do auth-service
├── events/
│   ├── client.py    ← chamadas HTTP ao events-service
│   └── schemas.py   ← modelos das respostas do events-service
└── registration/
    ├── controller.py
    ├── service.py   ← orquestra: usa AuthClient e EventsClient via injeção
    ├── repository.py
    └── schemas.py
```

Cada `client.py` encapsula toda a lógica de comunicação HTTP com o serviço externo correspondente (URL base, headers, tratamento de erros HTTP) e expõe uma interface limpa orientada ao domínio. Os `schemas.py` modelam apenas as respostas que chegam daquele serviço, desacoplando o modelo interno do contrato externo.

A injeção de dependência do FastAPI (`Depends`) é usada para fornecer as instâncias dos clients ao `RegistrationService`, permitindo que em testes os clients sejam substituídos por mocks sem alterar o código de produção.

## Consequências

- **Positivo:** Cada integração externa tem um único ponto de mudança. Se o `events-service` alterar um endpoint ou campo de resposta, só o `events/client.py` e `events/schemas.py` precisam ser atualizados.
- **Positivo:** O `RegistrationService` expressa a lógica de negócio em termos de domínio (`events_client.get_all_events()`), e não em detalhes de HTTP.
- **Positivo:** Testes unitários do `RegistrationService` podem mockar `AuthClient` e `EventsClient` independentemente, sem precisar simular requisições HTTP.
- **Positivo:** A estrutura de pastas torna explícita, para qualquer desenvolvedor novo, quais serviços externos este microsserviço consome.
- **Negativo:** Adiciona arquivos e pastas mesmo para integrações simples com poucos endpoints — pode parecer excessivo para integrações muito pequenas.
- **Negativo:** Requer disciplina para manter os `schemas.py` de cada client sincronizados com os contratos reais dos serviços externos (recomenda-se utilizar o `openapi.json` exportado por cada serviço como fonte de verdade).
