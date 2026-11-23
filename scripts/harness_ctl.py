#!/usr/bin/env python3
"""
CLI de Controle e Governança do Harness v2.3
Permite consultar status, transicionar estados, verificar histórico e rodar gates.
"""
import argparse
import json
from pathlib import Path
import sys

# Adiciona a raiz do projeto ao sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from harness.core.state_machine import HarnessStateMachine, HarnessState, InvalidStateTransitionError
from harness.core.gates import GateRunner, ArchiveGuard, ArchiveBlockedError
from harness.core.lease import WorkspaceLeaseManager, LeaseType, LeaseAcquisitionError


def cmd_status(args: argparse.Namespace) -> int:
    sm = HarnessStateMachine(args.change_id, project_root=root_dir)
    print(f"Change ID: {args.change_id}")
    print(f"Estado Atual: {sm.get_state().value}")
    print(f"Criado em: {sm.created_at}")
    print(f"Atualizado em: {sm.updated_at}")
    if sm.metadata:
        print(f"Metadados: {json.dumps(sm.metadata, indent=2, ensure_ascii=False)}")
    return 0


def cmd_transition(args: argparse.Namespace) -> int:
    sm = HarnessStateMachine(args.change_id, project_root=root_dir)
    try:
        new_state = sm.transition(
            target_state=args.to_state,
            actor=args.actor,
            reason=args.reason,
        )
        print(f"Sucesso: Change '{args.change_id}' transicionou para '{new_state.value}'.")
        return 0
    except InvalidStateTransitionError as e:
        print(f"Erro de Transição: {e}", file=sys.stderr)
        return 1


def cmd_history(args: argparse.Namespace) -> int:
    sm = HarnessStateMachine(args.change_id, project_root=root_dir)
    history = sm.get_history()
    if not history:
        print(f"Nenhum evento registrado para '{args.change_id}'.")
        return 0

    print(f"Histórico de Eventos para '{args.change_id}' ({len(history)} eventos):")
    for ev in history:
        from_st = ev.get("from_state") or "None"
        to_st = ev.get("to_state")
        ts = ev.get("timestamp")
        actor = ev.get("actor")
        reason = ev.get("reason")
        print(f"  [{ts}] {from_st} -> {to_st} | Ator: {actor} | Motivo: {reason}")
    return 0


def cmd_gates(args: argparse.Namespace) -> int:
    runner = GateRunner(project_root=root_dir)
    bundle = runner.evaluate_gates(args.change_id)
    status_str = "APROVADO (GREEN)" if bundle.overall_passed else "REPROVADO (RED)"
    print(f"ResultBundle: {bundle.bundle_id}")
    print(f"Status Geral: {status_str}")
    print(f"SHA-256: {bundle.sha256}")
    print("\nResultados por Gate:")
    for r in bundle.results:
        symbol = "✓" if r.passed else "✗"
        print(f"  [{symbol}] {r.gate.value}: {r.message}")
    return 0 if bundle.overall_passed else 1


def cmd_archive(args: argparse.Namespace) -> int:
    guard = ArchiveGuard(project_root=root_dir)
    try:
        bundle = guard.assert_ready_to_archive(args.change_id)
        sm = HarnessStateMachine(args.change_id, project_root=root_dir)
        if sm.get_state() != HarnessState.READY_TO_ARCHIVE:
            sm.transition(HarnessState.READY_TO_ARCHIVE, actor="harness_ctl", reason="Pre-archive transition")
        sm.transition(HarnessState.ARCHIVED, actor="harness_ctl", reason=f"Archived with ResultBundle {bundle.bundle_id}")

        # Mover diretório de change para archive se aplicável
        src = root_dir / "openspec" / "changes" / args.change_id
        dst_dir = root_dir / "openspec" / "archive"
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / args.change_id
        if src.exists() and not dst.exists():
            import shutil
            shutil.move(str(src), str(dst))
            print(f"Diretório movido: {src.relative_to(root_dir)} -> {dst.relative_to(root_dir)}")

        print(f"Change '{args.change_id}' arquivada com sucesso com governança estrita!")
        return 0
    except ArchiveBlockedError as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1


def cmd_lease(args: argparse.Namespace) -> int:
    lm = WorkspaceLeaseManager(project_root=root_dir)
    if args.action == "acquire":
        try:
            ltype = LeaseType.WRITE if args.write else LeaseType.READ
            record = lm.acquire(args.change_id, agent_id=args.agent, lease_type=ltype)
            print(f"Lease adquirido com sucesso: {record.lease_id} ({record.lease_type.value}) por {record.agent_id}")
            return 0
        except LeaseAcquisitionError as e:
            print(f"Falha de Lease: {e}", file=sys.stderr)
            return 1
    elif args.action == "history":
        history = lm.get_handoff_history(args.change_id)
        print(f"Histórico de Handoffs para '{args.change_id}' ({len(history)} registros):")
        for h in history:
            print(f"  [{h.get('timestamp')}] {h.get('from_agent')} -> {h.get('to_agent')} | Lease: {h.get('lease_id')}")
        return 0
    else:
        print(f"Ação de lease '{args.action}' desconhecida.")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Harness Control CLI v2.3")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # status
    p_status = subparsers.add_parser("status", help="Consulta o estado de uma change")
    p_status.add_argument("change_id", help="ID da change")
    p_status.set_defaults(func=cmd_status)

    # transition
    p_trans = subparsers.add_parser("transition", help="Transiciona uma change para novo estado")
    p_trans.add_argument("change_id", help="ID da change")
    p_trans.add_argument("to_state", help="Estado destino")
    p_trans.add_argument("--actor", default="agent", help="Identificador do agente/ator")
    p_trans.add_argument("--reason", default="Manual transition via CLI", help="Motivo da transição")
    p_trans.set_defaults(func=cmd_transition)

    # history
    p_hist = subparsers.add_parser("history", help="Exibe o histórico de eventos de uma change")
    p_hist.add_argument("change_id", help="ID da change")
    p_hist.set_defaults(func=cmd_history)

    # gates
    p_gates = subparsers.add_parser("gates", help="Executa e avalia os Quality Gates")
    p_gates.add_argument("change_id", help="ID da change")
    p_gates.set_defaults(func=cmd_gates)

    # archive
    p_arch = subparsers.add_parser("archive", help="Arquiva uma change aplicando ArchiveGuard")
    p_arch.add_argument("change_id", help="ID da change")
    p_arch.set_defaults(func=cmd_archive)

    # lease
    p_lease = subparsers.add_parser("lease", help="Gerencia leases de workspace")
    p_lease.add_argument("action", choices=["acquire", "history"], help="Ação de lease")
    p_lease.add_argument("change_id", help="ID da change")
    p_lease.add_argument("--agent", default="cli_agent", help="Identificador do agente")
    p_lease.add_argument("--write", action="store_true", default=True, help="Adquirir lease exclusivo de escrita")
    p_lease.set_defaults(func=cmd_lease)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
