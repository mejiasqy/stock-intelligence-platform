"""Verifica se o ambiente local atende aos pré-requisitos do projeto."""

import io
import subprocess
import sys
from dataclasses import dataclass

# Garante UTF-8 no terminal Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


@dataclass
class Check:
    name: str
    ok: bool
    detail: str


def run(cmd: list[str]) -> tuple[bool, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode == 0, (result.stdout + result.stderr).strip()
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        return False, str(e)


def check_python() -> Check:
    major, minor = sys.version_info.major, sys.version_info.minor
    ok = (major, minor) >= (3, 12)
    return Check("Python >= 3.12", ok, f"encontrado: {major}.{minor}")


def check_uv() -> Check:
    ok, out = run(["uv", "--version"])
    return Check("uv (gerenciador Python)", ok, out.split("\n")[0] if ok else "não encontrado")


def check_node() -> Check:
    ok, out = run(["node", "--version"])
    if ok:
        version = out.strip().lstrip("v")
        major = int(version.split(".")[0])
        ok = major >= 18
        detail = f"encontrado: v{version}"
    else:
        detail = "não encontrado"
    return Check("Node.js >= 18", ok, detail)


def check_docker() -> Check:
    ok, out = run(["docker", "--version"])
    return Check("Docker", ok, out.split("\n")[0] if ok else "não encontrado")


def check_docker_compose() -> Check:
    ok, out = run(["docker", "compose", "version"])
    return Check("Docker Compose", ok, out.split("\n")[0] if ok else "não encontrado")


def check_git() -> Check:
    ok, out = run(["git", "--version"])
    return Check("git", ok, out.split("\n")[0] if ok else "não encontrado")


def main() -> int:
    checks = [
        check_python(),
        check_uv(),
        check_node(),
        check_docker(),
        check_docker_compose(),
        check_git(),
    ]

    all_ok = True
    print("\nVerificação de ambiente — Stock Intelligence Platform\n")
    print(f"{'Verificação':<35} {'Status':<8} Detalhe")
    print("-" * 70)

    for c in checks:
        status = "OK" if c.ok else "FALHOU"
        mark = "✓" if c.ok else "✗"
        print(f"{mark} {c.name:<33} {status:<8} {c.detail}")
        if not c.ok:
            all_ok = False

    print()
    if all_ok:
        print("Ambiente OK — todos os pré-requisitos atendidos.")
        return 0
    else:
        print("Ambiente incompleto — corrija os itens marcados com ✗.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
