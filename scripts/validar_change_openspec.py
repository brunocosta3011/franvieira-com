#!/usr/bin/env python3
"""
CLI de Validação OpenSpec para Harness v2.3
Valida conformidade com schema platform-sdd-tdd.
Uso:
    python3 scripts/validar_change_openspec.py <change_id_ou_caminho>
    python3 scripts/validar_change_openspec.py --all
"""
import argparse
from pathlib import Path
import sys

# Adiciona a raiz do projeto ao sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from harness.core.validator import validate_change


def main() -> int:
    parser = argparse.ArgumentParser(description="Valida conformidade de changes OpenSpec SDD/TDD.")
    parser.add_argument("change", nargs="?", help="ID da change ou caminho do diretório")
    parser.add_argument("--all", action="store_true", help="Valida todas as changes em openspec/changes/")
    args = parser.parse_args()

    if args.all:
        changes_dir = root_dir / "openspec" / "changes"
        if not changes_dir.exists():
            print(f"Diretório de changes não encontrado: {changes_dir}")
            return 1

        all_valid = True
        subdirs = [d for d in changes_dir.iterdir() if d.is_dir()]
        if not subdirs:
            print("Nenhuma change ativa encontrada em openspec/changes/.")
            return 0

        for d in sorted(subdirs):
            res = validate_change(d, project_root=root_dir)
            print(res.summary)
            if not res.is_valid:
                all_valid = False

        return 0 if all_valid else 1

    if not args.change:
        parser.print_help()
        return 1

    res = validate_change(args.change, project_root=root_dir)
    print(res.summary)
    return 0 if res.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
