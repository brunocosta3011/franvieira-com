# Proposta: Bootstrap do Harness Multi-Agent v2.3 com Governança SDD/TDD

## Contexto
O ecossistema digital Fran Vieira necessita de governança estrita para colaboração confiável de agentes de inteligência artificial autônomos (Antigravity IDE, Claude Code CLI, etc.) e desenvolvedores humanos, garantindo qualidade inegociável de código e aderência a contratos.

## Problema
Sem uma esteira estruturada em código, agentes podem cometer regressões silenciosas, concorrer em arquivos simultaneamente, escrever código sem testes prévios ou fora do escopo aprovado.

## Escopo
- Configuração do schema canônico OpenSpec `platform-sdd-tdd`.
- Implementação do Core Engine do Harness v2.3 (`validator`, `state_machine`, `context_pack`, `execution_pack`, `lease`, `gates`, `registry`).
- Implementação dos Agent Adapters (`fake`, `interactive`, `claude_cli`).
- Disponibilização dos scripts CLI `scripts/validar_change_openspec.py` e `scripts/harness_ctl.py`.
- Formalização da Skill portável e documento de governança `AGENTS.md`.
- Cobertura de 100% por suite de testes automatizados TDD.

## Fora de Escopo
- Refatoração dos estilos visuais ou código legado existente do site neste bootstrap.
- Alteração da infraestrutura externa de DNS ou hospedagem.

## Riscos
- Sobrecarga de comandos caso o fluxo não seja documentado de forma clara e simples (mitigado pela criação de CLI unificado e da skill portável).

## Critérios de Aceite
- Todos os 4 artefatos OpenSpec presentes e válidos pelo validador do schema.
- Suite de testes automatizados rodando e atingindo 100% GREEN.
- ArchiveGuard validando H0, T1 e T2 antes de autorizar arquivamento.
