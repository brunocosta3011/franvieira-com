---
name: harness-workflow
description: Guia canônico do Harness Multi-Agent v2.3 com governança estrita OpenSpec SDD/TDD no ecossistema Fran Vieira.
---

# Harness Multi-Agent v2.3 - Fluxo de Governança Estrita OpenSpec SDD/TDD

Este guia define as regras universais de operação para qualquer agente autônomo, assistente de IA (Antigravity IDE, Claude Code CLI, etc.) ou desenvolvedor atuando neste repositório.

---

## 1. Princípios Invioláveis

1. **SDD Primeiro (Specification-Driven Development):** Nenhuma linha de código deve ser escrita sem uma change OpenSpec estruturada em `openspec/changes/<change-id>/` contendo os 4 artefatos canônicos:
   - `proposal.md`
   - `specs/` (BDD Given/When/Then)
   - `test-plan.md`
   - `tasks.md` (tarefas atômicas <= 2h)
2. **TDD Estrito (RED antes de GREEN):** É expressamente proibido implementar funcionalidade ou correção sem antes criar um teste automatizado e registrar sua execução com falha (estado **RED**).
3. **Bloqueio de Arquivamento (ArchiveGuard):** Uma change nunca pode ser transicionada para `ARCHIVED` sem passar nos gates **H0** (schema válido), **T1** (evidência de teste RED comprovada) e **T2** (100% dos testes passando em GREEN).
4. **Isolamento de Concorrência (Leases):** Modificações em disco exigem aquisição de lease exclusivo de escrita (`WRITE`).

---

## 2. Ciclo de Vida Canônico de Estados

```
[DRAFT]
   │
   ▼
[SPEC_PLANNED] ──> [SPEC_APPROVED]
                        │
                        ▼
                 [RED_REQUIRED]
                        │
                        ▼
                 [RED_RECORDED]
                        │
                        ▼
                 [IMPLEMENTING] ──> [GREEN]
                                      │
                                      ▼
                                [REFACTORED]
                                      │
                                      ▼
                                 [VERIFIED]
                                      │
                                      ▼
                                 [REVIEWED]
                                      │
                                      ▼
                             [READY_TO_ARCHIVE]
                                      │
                                      ▼
                                 [ARCHIVED]
```

---

## 3. Comandos Úteis

### Validação do Schema OpenSpec
```bash
python3 scripts/validar_change_openspec.py <change_id>
# ou validar todas
python3 scripts/validar_change_openspec.py --all
```

### Controle de Estados e Gates
```bash
# Consultar estado atual
python3 scripts/harness_ctl.py status <change_id>

# Transicionar de estado
python3 scripts/harness_ctl.py transition <change_id> <TARGET_STATE> --actor "agente" --reason "motivo"

# Consultar histórico de eventos
python3 scripts/harness_ctl.py history <change_id>

# Avaliar Quality Gates (H0, T1, T2, V1, R1)
python3 scripts/harness_ctl.py gates <change_id>

# Arquivar change após conclusão (aplica ArchiveGuard automaticamente)
python3 scripts/harness_ctl.py archive <change_id>
```

### Executar Testes Automatizados
```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```
