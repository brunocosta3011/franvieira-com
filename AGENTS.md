# Diretrizes de Governança para Agentes Autônomos (AGENTS.md)
## Ecossistema Digital Fran Vieira — Harness Multi-Agent v2.3

Bem-vindo ao repositório `franvieira.com`.
**Todos os agentes autônomos, modelos de linguagem e desenvolvedores devem seguir estritamente o fluxo Harness v2.3.**

---

### 1. Fluxo Obrigatório de Desenvolvimento
Nenhuma implementação ou modificação substancial de código deve ser feita diretamente no repositório sem seguir o ciclo canônico de governança:

1. **Criação da Change OpenSpec (`openspec/changes/<change-id>/`):**
   - `proposal.md`: Contexto, problema, escopo, fora de escopo, riscos e critérios de aceite.
   - `specs/`: Cenários BDD estruturados (`Given/When/Then` ou `Dado/Quando/Então`).
   - `test-plan.md`: Mapeamento requisito -> teste e evidência de teste RED inicial.
   - `tasks.md`: Lista sequencial de tarefas atômicas (cada uma com estimativa <= 2 horas).
   - `design.md`: Obrigatório para alterações de contrato ou decisões arquiteturais.

2. **Validação do Schema OpenSpec (Gate H0):**
   - Execute:
     ```bash
     python3 scripts/validar_change_openspec.py <change-id>
     ```
   - O schema deve estar 100% válido antes de avançar.

3. **Ciclo TDD Estrito (RED antes de GREEN):**
   - Transicione o estado para `RED_REQUIRED`.
   - Crie o teste automatizado que falha comprovando a ausência da funcionalidade/correção.
   - Registre a evidência de falha no `test-plan.md` e transicione para `RED_RECORDED`.
   - Apenas agora avance para `IMPLEMENTING`.
   - Escreva o código produtivo até que todos os testes passem (`GREEN`).
   - Refatore conforme necessário (`REFACTORED`).

4. **Verificação e Quality Gates (V1, R1, T2):**
   - Execute a suite de testes:
     ```bash
     python3 -m unittest discover -s tests -p 'test_*.py'
     ```
   - Gere o bundle de resultados:
     ```bash
     python3 scripts/harness_ctl.py gates <change-id>
     ```

5. **Arquivamento Seguro (ArchiveGuard):**
   - Use o CLI para transicionar e arquivar:
     ```bash
     python3 scripts/harness_ctl.py archive <change-id>
     ```
   - O `ArchiveGuard` impedirá o arquivamento se faltar teste RED ou se algum teste estiver quebrado.

---

### 2. Leases de Concorrência
Para evitar concorrência destrutiva entre agentes trabalhando simultaneamente:
- Adquira lease de escrita antes de alterar arquivos:
  ```bash
  python3 scripts/harness_ctl.py lease acquire <change-id> --agent <nome_do_agente> --write
  ```

---

### 3. Habilidades Disponíveis
Consulte `.agents/skills/harness-workflow/SKILL.md` para instruções detalhadas sobre cada etapa operacional.
