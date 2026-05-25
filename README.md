# Gerador de Remessas SQL Server

Ferramenta de linha de comando que automatiza a organização e consolidação de scripts T-SQL em arquivos de remessa padronizados para entrega a clientes.

---

## O que faz

- Varre um diretório de remessa e detecta as pastas de objetos SQL presentes
- Concatena todos os arquivos `.sql` de cada pasta em um único arquivo compilado
- Insere cabeçalho `USE DATABASE / GO` no início de cada arquivo
- Envolve cada script em regiões de folding (`-- #region / -- #endregion`)
- Gera um `INSERT INTO VERSAO_SISTEMA` ao final de cada arquivo compilado (exceto `001_MENU_DIMP.sql`)
- Cria automaticamente a estrutura de saída `database/`
- Realiza backup automático da pasta `database/` antes de sobrescrever
- Salva log completo da execução em `database/logs/`

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

```
<pasta-da-remessa>/
└── database/
    ├── 01_AB_DIMP/
    │   ├── 001_TAB_PM.sql
    │   ├── 003_CARGA_PM.sql
    │   ├── 031_VW_PM.sql
    │   ├── 041_FN_PM.sql
    │   └── 051_PR_PM.sql
    ├── 02_AB_CONTROLE/
    │   └── 001_MENU_DIMP.sql
    └── logs/
        └── remessa_YYYYMMDD_HHMMSS.log
```

---

## Como executar

### Usando o executável (recomendado)

Não requer Python instalado.

1. Abra a pasta `dist/`
2. Execute `GeradorRemessas.exe` (duplo clique ou via CMD)
3. Informe o caminho da pasta da remessa quando solicitado:

```
Informe o caminho da pasta da remessa: C:\Remessas\Cliente_X\
```

4. Informe a versão no formato `VX.X.X`:

```
Informe a versao da remessa (ex: V5.0.2): V5.0.2
```

5. Aguarde o processamento. Ao final, pressione **Enter** para fechar.

---

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

## Mapeamento de pastas

| Pasta de entrada | Arquivo gerado       | Banco de dados |
|------------------|----------------------|----------------|
| Tabelas          | 001_TAB_PM.sql       | AB_DIMP        |
| Cargas           | 003_CARGA_PM.sql     | AB_DIMP        |
| Views            | 031_VW_PM.sql        | AB_DIMP        |
| Functions        | 041_FN_PM.sql        | AB_DIMP        |
| Procedures       | 051_PR_PM.sql        | AB_DIMP        |
| Controles        | 001_MENU_DIMP.sql    | AB_CONTROLE    |

---

## Requisitos técnicos

- Python 3.x
- Bibliotecas nativas: `os`, `re`, `pathlib`, `shutil`, `json`
- Pillow (apenas para recompilar o ícone)
- PyInstaller (apenas para recompilar o executável)
