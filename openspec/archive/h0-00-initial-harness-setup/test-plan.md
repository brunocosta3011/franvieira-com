# Plano de Testes: Bootstrap do Harness Multi-Agent v2.3

## Mapeamento Requisito -> Teste
- Validador OpenSpec -> `tests/test_validator.py`
- Máquina de Estados -> `tests/test_state_machine.py`
- Context Pack determinístico -> `tests/test_context_pack.py`
- Execution Pack e obsolescência -> `tests/test_execution_pack.py`
- Gerenciamento de Leases -> `tests/test_lease.py`
- Quality Gates e Archive Guard -> `tests/test_gates.py`
- Adapters de Agentes -> `tests/test_adapters.py`
- Ciclo E2E Integrado (Dogfooding) -> `tests/test_e2e_dogfooding.py`

## Evidência de Teste RED
- Status: RED (Registrado na fase inicial de TDD)
- Detalhes da Execução com Falha:
  ```text
  AssertionError: BudgetExceededError not raised
  FAILED (failures=1, total=25)
  ```
- O ciclo TDD foi cumprido: falha confirmada e corrigida, levando a suite para 100% GREEN.
