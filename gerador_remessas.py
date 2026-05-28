from pathlib import Path
from datetime import datetime
from typing import Optional
import os
import re
import shutil
import json


# ─────────────────────────────────────────────────────────────────
# Configuração de mapeamento das pastas
# ─────────────────────────────────────────────────────────────────

FOLDER_MAPPING = {
    "Tabelas": {
        "output_file": "001_TAB_",
    },
    "Cargas": {
        "output_file": "003_CARGA_",
    },
    "Views": {
        "output_file": "031_VW_",
    },
    "Functions": {
        "output_file": "041_FN_",
    },
    "Procedures": {
        "output_file": "051_PR_",
    },
    "Controles": {
        "output_file": "001_MENU_",
        "database":    "AB_CONTROLE",
    },
}

CONFIG_FILE = "config.json"

# ─────────────────────────────────────────────────────────────────
# Logger
# ─────────────────────────────────────────────────────────────────

class Logger:
    def __init__(self):
        self.entries = []
        self.log_path = None

    def _record(self, level: str, msg: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.entries.append(f"[{timestamp}] [{level}] {msg}")
        print(f"[{level}] {msg}")

    def ok(self, msg: str):
        self._record("OK  ", msg)

    def warn(self, msg: str):
        self._record("WARN", msg)

    def error(self, msg: str):
        self._record("ERR ", msg)

    def info(self, msg: str):
        self._record("INFO", msg)

    def save(self, output_base: Path):
        log_dir = output_base / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_path = log_dir / f"remessa_{timestamp}.log"
        self.log_path.write_text("\n".join(self.entries), encoding="utf-8")
        print(f"\n[INFO] Log salvo em: {self.log_path}")


# ─────────────────────────────────────────────────────────────────
# Configuração externa
# ─────────────────────────────────────────────────────────────────

def load_config() -> dict:
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        try:
            with config_path.open(encoding="utf-8") as f:
                data = json.load(f)
                print(f"[INFO] Configuracao carregada de {CONFIG_FILE}")
                return data
        except Exception as e:
            print(f"[WARN] Falha ao ler {CONFIG_FILE}: {e}. Usando configuracao padrao.")
    return {}


# ─────────────────────────────────────────────────────────────────
# Utilitários de saída
# ─────────────────────────────────────────────────────────────────

def print_progress(current: int, total: int, label: str = ""):
    bar_len = 28
    filled = int(bar_len * current / total) if total > 0 else bar_len
    bar = "█" * filled + "░" * (bar_len - filled)
    pct = int(100 * current / total) if total > 0 else 100
    print(f"\r  [{bar}] {pct:3d}%  {label:<35}", end="", flush=True)
    if current >= total:
        print()


def print_banner():
    print()
    print("=" * 60)
    print("   Gerador de Remessas SQL Server")
    print("=" * 60)
    print()


def print_summary(generated: list, logger: "Logger"):
    print()
    print("=" * 60)
    if not generated:
        print("  Nenhum arquivo foi gerado.")
        print("=" * 60)
        return

    print("  Processamento concluido com sucesso!")
    print()
    print("  Arquivos gerados:")
    for item in generated:
        relative = item["file"]
        print(f"    - {relative}")
    print("=" * 60)
    if logger.log_path:
        print(f"\n  Log completo: {logger.log_path}")
    print()


# ─────────────────────────────────────────────────────────────────
# Construtores de conteúdo SQL
# ─────────────────────────────────────────────────────────────────

def build_file_header(database: str) -> str:
    line = "-- " + "=" * 57
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return (
        f"{line}\n"
        f"-- Gerado automaticamente em {ts}\n"
        f"-- Banco de dados: {database}\n"
        f"{line}\n\n"
        f"USE {database}\nGO\n\n"
    )


def build_file_footer(output_filename: str, versao: str, sistema_sigla: str) -> str:
    dash = "-" * 104
    return (
        f"{dash}\n"
        f"INSERT INTO VERSAO_SISTEMA (CODSISTEMA, VERSAO, NOMESCRIPT, CODUSUARIO, DATATU)\n"
        f"VALUES ('{sistema_sigla}', '{versao}','{output_filename}', HOST_NAME(), GETDATE())\n"
        f"GO\n"
        f"{dash}\n"
    )


def build_script_block(filename: str, content: str) -> str:
    sep = "-- " + "=" * 45
    return (
        f"{sep}\n"
        f"-- REGION: {filename}\n"
        f"{sep}\n"
        f"-- #region {filename}\n\n"
        f"{content.strip()}\n\n"
        f"GO\n\n"
        f"-- #endregion\n\n"
    )


# ─────────────────────────────────────────────────────────────────
# Leitura de arquivos
# ─────────────────────────────────────────────────────────────────

def strip_use_go(content: str) -> str:
    """Remove declarações USE <db> / GO dos arquivos individuais."""
    return re.sub(r"(?im)^\s*USE\s+\S+\r?\n\s*GO[ \t]*\r?\n?", "", content)


def read_sql_file(path: Path, logger: "Logger") -> Optional[str]:
    # Tenta múltiplos encodings para compatibilidade
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
        except PermissionError:
            logger.error(f"Sem permissao para ler: {path.name}")
            return None
        except OSError as e:
            logger.error(f"Erro ao ler {path.name}: {e}")
            return None
    logger.error(f"Nao foi possivel decodificar o arquivo: {path.name}")
    return None


# ─────────────────────────────────────────────────────────────────
# Backup
# ─────────────────────────────────────────────────────────────────

def backup_existing(output_dir: Path, logger: "Logger"):
    if not output_dir.exists():
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = output_dir.parent / f"database_backup_{timestamp}"
    try:
        shutil.copytree(output_dir, backup_path)
        logger.info(f"Backup criado em: {backup_path}")
    except Exception as e:
        logger.warn(f"Nao foi possivel criar backup: {e}")


# ─────────────────────────────────────────────────────────────────
# Processamento de pasta
# ─────────────────────────────────────────────────────────────────

def process_folder(
    folder_path: Path,
    folder_name: str,
    output_base: Path,
    logger: "Logger",
    versao: str,
    database_name: str,
    sistema_sigla: str
) -> Optional[dict]:
    sql_files = sorted(folder_path.glob("*.sql"))

    if not sql_files:
        logger.warn(f'Pasta "{folder_name}" encontrada, mas sem arquivos .sql')
        return None

    mapping      = FOLDER_MAPPING[folder_name]
    is_controle  = "database" in mapping

    if is_controle:
        out_dir_name    = "02_AB_CONTROLE"
        database        = mapping["database"]
        output_filename = f"{mapping['output_file']}{sistema_sigla}.sql"
    else:
        out_dir_name    = f"01_{database_name}"
        database        = database_name
        output_filename = f"{mapping['output_file']}{sistema_sigla}.sql"

    output_dir = output_base / out_dir_name / "scripts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / output_filename

    logger.ok(f'Pasta "{folder_name}" encontrada — {len(sql_files)} arquivo(s) .sql')

    blocks = [build_file_header(database)]
    compiled = 0

    for i, sql_path in enumerate(sql_files, start=1):
        print_progress(i, len(sql_files), sql_path.name)
        content = read_sql_file(sql_path, logger)
        if content is None:
            continue
        blocks.append(build_script_block(sql_path.name, strip_use_go(content)))
        compiled += 1

    if not is_controle:
        blocks.append(build_file_footer(output_filename, versao, sistema_sigla))

    try:
        output_file.write_text("".join(blocks), encoding="utf-8")
    except PermissionError:
        logger.error(f"Sem permissao para escrever: {output_file}")
        return None
    except OSError as e:
        logger.error(f"Erro ao escrever {output_file}: {e}")
        return None

    logger.ok(f'{compiled} arquivo(s) compilados em {output_filename}')
    return {"folder": folder_name, "file": str(output_file), "count": compiled}


# ─────────────────────────────────────────────────────────────────
# Entrada do usuário
# ─────────────────────────────────────────────────────────────────

def get_database_name() -> str:
    while True:
        raw = input("Informe o nome do banco de dados (ex: AB_DIMP): ").strip()
        if not raw:
            print("[ERR ] Nome do banco nao pode ser vazio.\n")
            continue
        if re.search(r"\s", raw):
            print("[ERR ] Nome do banco nao pode conter espacos.\n")
            continue
        return raw

def get_sistema_sigla() -> str:
    while True:
        raw = input("Informe a sigla do sistema (ex: PM): ").strip().upper()
        if not raw:
            print("[ERR ] Sigla do sistema nao pode ser vazia.\n")
            continue
        if re.search(r"\s", raw):
            print("[ERR ] Sigla do sistema nao pode conter espacos.\n")
            continue
        return raw

def get_version() -> str:
    pattern = re.compile(r"^V\d+\.\d+\.\d+$")
    while True:
        raw = input("Informe a versao da remessa (ex: V5.0.2): ").strip()
        if not raw:
            print("[ERR ] Versao nao pode ser vazia.\n")
            continue
        if not pattern.match(raw):
            print("[ERR ] Formato invalido. Use o padrao VX.X.X (ex: V5.0.2).\n")
            continue
        return raw


def get_source_path() -> Path:
    while True:
        raw = input("Informe o caminho da pasta da remessa: ").strip().strip('"')
        if not raw:
            print("[ERR ] Caminho nao pode ser vazio.\n")
            continue
        path = Path(raw)
        if not path.exists():
            print(f"[ERR ] Caminho nao encontrado: {path}\n")
            continue
        if not path.is_dir():
            print(f"[ERR ] O caminho nao e um diretorio: {path}\n")
            continue
        try:
            os.listdir(path)
        except PermissionError:
            print(f"[ERR ] Sem permissao para acessar: {path}\n")
            continue
        return path


# ─────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────

def main():
    print_banner()
    load_config()

    logger = Logger()
    source_path = get_source_path()
    versao = get_version()
    database_name = get_database_name()
    sistema_sigla = get_sistema_sigla()
    output_base = source_path / "database"

    if output_base.exists():
        backup_existing(output_base, logger)

    print()
    logger.info("Iniciando varredura de pastas...")
    print()

    generated = []
    found_any = False

    for folder_name in FOLDER_MAPPING:
        folder_path = source_path / folder_name
        if not folder_path.is_dir():
            logger.warn(f'Pasta "{folder_name}" nao encontrada')
            continue

        found_any = True
        result = process_folder(folder_path, folder_name, output_base, logger, versao, database_name, sistema_sigla)
        if result:
            generated.append(result)
        print()

    if not found_any:
        logger.error("Nenhuma pasta conhecida encontrada no diretorio informado.")
        logger.info("Pastas esperadas: " + ", ".join(FOLDER_MAPPING.keys()))

    logger.save(output_base)
    print_summary(generated, logger)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INFO] Operacao cancelada pelo usuario.")
    finally:
        input("Pressione Enter para fechar...")
