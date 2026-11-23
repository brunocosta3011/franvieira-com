# Especificação BDD: Bootstrap do Harness Multi-Agent v2.3

## Cenário 1: Validação estrita do Schema OpenSpec (Gate H0)
Given uma change sob `openspec/changes/<change-id>`
When o script de validação de schema é executado
Then os artefatos `proposal.md`, `specs/`, `test-plan.md` e `tasks.md` são verificados com sucesso.

## Cenário 2: Ciclo de Vida TDD e Evidência RED (Gate T1)
Given um agente iniciando uma nova funcionalidade
When a etapa de testes for iniciada
Then o teste com falha (RED) deve ser registrado antes de qualquer implementação.

## Cenário 3: Proteção de Concorrência e Leases
Given múltiplos executores atuando no repositório
When um agente solicita lease de escrita exclusivo
Then qualquer solicitação concorrente de escrita deve ser rejeitada até a liberação e registro de handoff.

## Cenário 4: Bloqueio Estrito de Arquivamento (ArchiveGuard)
Given uma change finalizada
When o comando de arquivamento for acionado
Then a transição só é permitida se os gates H0, T1 e T2 estiverem 100% satisfeitos.
