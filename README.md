# Gerador de Remessas SQL Server

Ferramenta de linha de comando que automatiza a organização e consolidação de scripts T-SQL em arquivos de remessa padronizados para entrega a clientes.

---

## O que faz

- Varre um diretório de remessa e detecta as pastas de objetos SQL presentes
- Concatena todos os arquivos `.sql` de cada pasta em um único arquivo compilado
- Insere cabeçalho `USE DATABASE / GO` no início de cada arquivo gerado
- Envolve cada script em regiões de folding (`-- #region / -- #endregion`)
- Gera um `INSERT INTO VERSAO_SISTEMA` ao final de cada arquivo compilado (exceto `Controles`)
- Cria automaticamente a estrutura de saída `database/` dentro da pasta informada
- Realiza backup automático da pasta `database/` antes de sobrescrever
- Salva log completo da execução em `database/logs/`

---

## O que foi alterado (v2)

### Parâmetros dinâmicos por sistema

Anteriormente o script era fixo para o sistema **DIMP** (`AB_DIMP`, sigla `PM`). Agora qualquer sistema pode ser utilizado informando dois novos parâmetros durante a execução:

| Parâmetro         | Descrição                                    | Exemplo       |
|-------------------|----------------------------------------------|---------------|
| **Banco de dados** | Nome do banco principal do sistema           | `AB_DIMP`     |
| **Sigla do sistema** | Identificador curto usado nos arquivos gerados | `DIMP`    |

### Impacto dos novos parâmetros

**Pasta de saída principal** — gerada dinamicamente com base no banco informado:
```
01_<BANCO_DE_DADOS>/scripts/
```
Exemplo: banco `AB_CUST` → pasta `01_AB_CUST/scripts/`

**Nome dos arquivos gerados** — usa a sigla informada:
```
001_TAB_<SIGLA>.sql
003_CARGA_<SIGLA>.sql
031_VW_<SIGLA>.sql
041_FN_<SIGLA>.sql
051_PR_<SIGLA>.sql
001_MENU_<SIGLA>.sql   ← pasta Controles
```

**Footer de versionamento** — `CODSISTEMA` agora reflete a sigla informada:
```sql
INSERT INTO VERSAO_SISTEMA (CODSISTEMA, VERSAO, NOMESCRIPT, CODUSUARIO, DATATU)
VALUES ('<SIGLA>', '<VERSAO>', '<ARQUIVO>', HOST_NAME(), GETDATE())
```

### `AB_CONTROLE` permanece fixo

A pasta `Controles` sempre usa o banco `AB_CONTROLE` e a pasta de saída `02_AB_CONTROLE`, independente do sistema informado. Apenas o nome do arquivo gerado muda conforme a sigla.

---

## Entradas solicitadas durante a execução

O script solicita quatro informações em sequência:

```
Informe o caminho da pasta da remessa: C:\Remessas\V5.0.2\
Informe a versao da remessa (ex: V5.0.2): V5.0.2
Informe o nome do banco de dados (ex: AB_DIMP): AB_DIMP
Informe a sigla do sistema (ex: PM): DIMP
```

---

## Estrutura de entrada esperada

```
<pasta-da-remessa>/
├── Tabelas/        → um ou mais arquivos .sql
├── Cargas/
├── Views/
├── Functions/
├── Procedures/
└── Controles/
```

Nem todas as pastas precisam estar presentes — o sistema processa apenas as que encontrar.

---

## Estrutura de saída gerada

Exemplo com banco `AB_DIMP` e sigla `DIMP`:

```
<pasta-da-remessa>/
└── database/
    ├── 01_AB_DIMP/
    │   └── scripts/
    │       ├── 001_TAB_DIMP.sql
    │       ├── 003_CARGA_DIMP.sql
    │       ├── 031_VW_DIMP.sql
    │       ├── 041_FN_DIMP.sql
    │       └── 051_PR_DIMP.sql
    ├── 02_AB_CONTROLE/
    │   └── scripts/
    │       └── 001_MENU_DIMP.sql
    └── logs/
        └── remessa_YYYYMMDD_HHMMSS.log
```

Exemplo com banco `AB_CUST` e sigla `CUST`:

```
<pasta-da-remessa>/
└── database/
    ├── 01_AB_CUST/
    │   └── scripts/
    │       ├── 001_TAB_CUST.sql
    │       ├── 003_CARGA_CUST.sql
    │       └── ...
    ├── 02_AB_CONTROLE/
    │   └── scripts/
    │       └── 001_MENU_CUST.sql
    └── logs/
```

---

## Mapeamento de pastas

| Pasta de entrada | Arquivo gerado          | Banco de dados     | Pasta de saída         |
|------------------|-------------------------|--------------------|------------------------|
| Tabelas          | `001_TAB_<SIGLA>.sql`   | Informado pelo usuário | `01_<BANCO>/scripts` |
| Cargas           | `003_CARGA_<SIGLA>.sql` | Informado pelo usuário | `01_<BANCO>/scripts` |
| Views            | `031_VW_<SIGLA>.sql`    | Informado pelo usuário | `01_<BANCO>/scripts` |
| Functions        | `041_FN_<SIGLA>.sql`    | Informado pelo usuário | `01_<BANCO>/scripts` |
| Procedures       | `051_PR_<SIGLA>.sql`    | Informado pelo usuário | `01_<BANCO>/scripts` |
| Controles        | `001_MENU_<SIGLA>.sql`  | `AB_CONTROLE` (fixo)  | `02_AB_CONTROLE/scripts` |

---

## Como executar

### Usando o executável (recomendado)

Não requer Python instalado.

1. Abra a pasta `dist/`
2. Execute `GeradorRemessas.exe` (duplo clique ou via CMD)
3. Responda às perguntas exibidas no terminal

### Usando o script Python diretamente

**Requisito:** Python 3.x

```bash
python gerador_remessas.py
```

---

## Como recompilar o executável

**Requisito:** Python 3.x com PyInstaller instalado.

```bash
pip install pyinstaller pillow
python gerar_icone.py
python -m PyInstaller --onefile --console --name "GeradorRemessas" --icon "GeradorRemessas.ico" gerador_remessas.py
```

O executável será gerado em `dist/GeradorRemessas.exe`.

---

## Requisitos técnicos

- Python 3.x
- Bibliotecas nativas: `os`, `re`, `pathlib`, `shutil`, `json`
- Pillow (apenas para recompilar o ícone)
- PyInstaller (apenas para recompilar o executável)
