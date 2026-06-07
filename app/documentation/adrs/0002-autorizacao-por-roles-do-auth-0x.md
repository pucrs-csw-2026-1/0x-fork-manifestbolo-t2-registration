# 0002. Autorização por Roles do Auth 0x

**Data:** 2026-06-07

## Status

Aceito

## Contexto

O serviço `manifestbolo-t2-registration` precisa proteger rotas que leem ou alteram inscrições. A autenticação já era delegada ao Auth Service do grupo `0x_t1`, por meio do `AuthClient`, que valida o Bearer token chamando `/users/me` e retorna os dados do usuário autenticado.

O Auth Service `0x_t1` não expõe uma tabela dinâmica de permissões. Ele usa o campo `access_level` do usuário como um enum com três papéis: `PARTICIPANT`, `MANAGER` e `ADMIN`. Esses papéis são convertidos em scopes no JWT pelo próprio auth-service, mas o contrato consumido pelo ManifestBolo via `/users/me` é o `access_level` retornado no corpo da resposta.

As rotas do ManifestBolo têm necessidades diferentes de autorização:

1. Usuários participantes devem conseguir operar apenas sobre a própria inscrição.
2. Usuários gerentes devem conseguir consultar listagens de inscrições e validar check-in operacional.
3. Usuários administradores devem conseguir executar todas as operações protegidas, inclusive para outros usuários.

Alternativas consideradas:

1. **Validar apenas se existe Bearer token**: simples, mas permite que qualquer participante liste inscrições ou consulte check-in de terceiros.
2. **Duplicar validação de roles em cada endpoint**: funciona, mas espalha regras de autorização pelo controller e aumenta risco de inconsistência.
3. **Centralizar regras em dependências e helpers de auth** _(decisão adotada)_: mantém as regras alinhadas ao contrato do Auth `0x_t1` e deixa os controllers declararem a intenção de autorização.

## Decisão

Adotamos uma camada de autorização baseada no `access_level` retornado pelo Auth Service `0x_t1`, implementada em `src/domain/auth/dependencies.py`.

A dependência `get_current_user` permanece responsável por autenticar o request: ela extrai o Bearer token, chama o Auth Service via `AuthClient.validate_token()` e retorna o `UserResponse` autenticado. Sobre esse retorno, foram adicionados helpers de autorização por role:

- `Role`: enum local com os valores `PARTICIPANT`, `MANAGER` e `ADMIN`, espelhando o contrato do Auth `0x_t1`.
- `require_roles(...)`: factory de dependência FastAPI para aceitar apenas usuários com uma das roles informadas.
- `require_manager_or_admin`: dependência para rotas operacionais de listagem e check-in.
- `ensure_self_or_admin(...)`: regra para mutações de inscrição; o próprio usuário pode operar sobre si e `ADMIN` pode operar sobre qualquer usuário.
- `ensure_self_or_manager_or_admin(...)`: regra para consultas pontuais; o próprio usuário pode consultar a própria inscrição e `MANAGER`/`ADMIN` podem consultar qualquer usuário.
- `is_admin(...)` e `is_manager_or_admin(...)`: helpers explícitos para decisões no controller.

As regras adotadas são:

- `PARTICIPANT`: só mexe na própria inscrição.
- `MANAGER`: consulta/lista inscrições e check-in operacional.
- `ADMIN`: tudo.

O controller de registration usa essas dependências e helpers para proteger as rotas sensíveis:

- Listagens de inscrições de evento e atividade exigem `MANAGER` ou `ADMIN`.
- Validação de check-in exige `MANAGER` ou `ADMIN`.
- Criação e cancelamento de inscrição permitem o próprio usuário ou `ADMIN`.
- Consulta pontual de inscrição em atividade permite o próprio usuário, `MANAGER` ou `ADMIN`.

Essa decisão segue o Auth Service `0x_t1` como fonte do contrato de identidade e papel. O ManifestBolo não cria uma tabela própria de roles ou permissions; ele apenas interpreta o `access_level` validado pelo auth-service.

## Consequências

- **Positivo:** As regras de autorização ficam centralizadas em `src/domain/auth/dependencies.py`, reduzindo duplicação nos controllers.
- **Positivo:** O ManifestBolo passa a seguir explicitamente o modelo de roles do Auth `0x_t1`, sem criar um RBAC paralelo.
- **Positivo:** Participantes deixam de acessar rotas operacionais de listagem e check-in, reduzindo exposição de inscrições de terceiros.
- **Positivo:** `ADMIN` pode executar operações administrativas sobre inscrições de qualquer usuário, preservando a regra “admin pode tudo”.
- **Positivo:** Testes conseguem substituir o `AuthClient` por fake ou usar o Auth Service real em testes de integração, mantendo a regra exercitável.
- **Negativo:** O ManifestBolo fica acoplado aos valores textuais de `access_level` definidos pelo Auth `0x_t1`; mudanças nesses nomes exigem ajuste coordenado.
- **Negativo:** Como o Auth `0x_t1` não possui catálogo dinâmico de permissões por role, permissões finas como `registration:read` ou `checkin:validate` exigiriam evolução do contrato entre os serviços.
