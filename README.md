# Best Books Downloader 📚

Sistema automatizado de web scraping do site [best-books.dev](https://www.best-books.dev/) com download automático de livros via Libgen. Implementado com arquitetura orientada a objetos e testes automatizados.

## 🎯 Funcionalidades

- **Web Scraping Completo**: Extrai automaticamente TODAS as listas de livros do site
- **Extração de Dados**: Obtém título e autor com parsing HTML robusto e encoding UTF-8
- **Suporte Unicode**: Trata corretamente caracteres especiais (ç, é, ñ, etc.)
- **Busca Automática**: Integração com Libgen via `libgen-api-enhanced`
- **Download Automático**: Baixa todos os livros disponíveis em formato EPUB
- **Organização Inteligente**: Estrutura de pastas organizada por categoria/lista
- **Arquitetura OOP**: Implementação com classes reutilizáveis e testáveis
- **Testes Automatizados**: Suite completa de testes com pytest

## 📁 Estrutura de Pastas

```text
books/
├── best-programming-books/
│   ├── Clean Code.epub
│   ├── The Pragmatic Programmer.epub
│   └── ...
├── best-python-books/
│   ├── Python Crash Course.epub
│   ├── Fluent Python.epub
│   └── ...
└── ...
```

## 🚀 Como Usar

### Instalação de Dependências

```bash
uv sync
```

### Uso Básico

```bash
# Download completo de todas as listas e todos os livros
uv run python main.py
```

**⚠️ IMPORTANTE:** O sistema baixa automaticamente **TODAS** as listas e **TODOS** os livros do site best-books.dev. Não há opções de limitação. Certifique-se de ter:

- Conexão estável com internet
- Espaço suficiente em disco (pode ser vários GB)
- Tempo disponível (o processo pode levar horas)

## 🛠️ Estrutura do Projeto

```text
.
├── main.py                 # Ponto de entrada - executa o scraping completo
├── scripts/
│   ├── __init__.py        # Módulo Python
│   ├── scraper.py         # Classe Scraper - lógica de web scraping
│   ├── libgen.py          # Classe Libgen - busca e download via Libgen
│   └── utils.py           # Funções utilitárias (slugify, formatação)
├── tests/
│   ├── __init__.py        # Módulo de testes
│   ├── test_scraper.py    # Testes do Scraper (10 testes)
│   ├── test_libgen.py     # Testes do Libgen (15 testes)
│   └── README.md          # Documentação dos testes
├── books/                 # Livros baixados (criada automaticamente)
├── pyproject.toml         # Dependências e configuração (inclui pytest)
└── README.md              # Este arquivo
```

## 📦 Dependências

**Produção:**

- `beautifulsoup4>=4.14.2` - Parsing de HTML
- `requests>=2.32.5` - Requisições HTTP
- `libgen-api-enhanced>=1.2.1` - Interface com Libgen

**Desenvolvimento:**

- `pytest>=8.4.2` - Framework de testes
- `mypy>=1.18.2` - Type checking
- `ruff>=0.13.2` - Linter e formatter

## 🧪 Testes

O projeto inclui testes automatizados para validar o funcionamento dos módulos.

### Executar todos os testes

```bash
uv run pytest
```

### Executar testes específicos

```bash
# Apenas testes rápidos (pula downloads)
uv run pytest -m "not slow"

# Apenas testes do Libgen
uv run pytest tests/test_libgen.py -v

# Apenas testes do Scraper
uv run pytest tests/test_scraper.py -v

# Testes de rede (que fazem requisições reais)
uv run pytest -m "network" -v
```

### Mais informações

Consulte [tests/README.md](tests/README.md) para documentação completa dos testes.

## 🔄 Como Funciona

O sistema executa o seguinte fluxo automatizado:

1. **Descoberta de Listas**: Acessa o site best-books.dev e extrai todas as listas disponíveis
2. **Extração de Dados**: Para cada lista, extrai título e autor de todos os livros (UTF-8)
3. **Criação de Estrutura**: Cria uma pasta para cada lista usando slugs (ex: `best-python-books/`)
4. **Busca no Libgen**: Para cada livro, faz busca por título no Libgen
5. **Filtro Inteligente**: Filtra resultados por sobrenome do autor (tolerante a variações)
6. **Download**: Baixa o primeiro resultado filtrado em formato EPUB
7. **Organização**: Salva o arquivo na pasta correspondente à lista
8. **Relatório**: Ao final, exibe estatísticas de sucesso/falha

### 🧠 Filtro Inteligente de Autor

**Problema Anterior:** Comparação exata (`author == "Eric Evans"`) falhava com:

- ❌ "Evans, Eric" (ordem invertida)
- ❌ "Eric J. Evans" (nome do meio)
- ❌ "Evans" (apenas sobrenome)

**Solução Atual:** Busca por sobrenomes

- ✅ "Eric Evans" → busca livros contendo "evans"
- ✅ "Evans, Eric" → **encontrado!** (contém "evans")
- ✅ "Eric J. Evans" → **encontrado!** (contém "evans")
- ✅ "Kent Beck & Martin Fowler" → busca "beck" **OU** "fowler"

**Delays e Rate Limiting:**

- 2 segundos entre cada livro
- 3 segundos entre cada lista
- Isso evita sobrecarga nos servidores

## ⚠️ Observações Importantes

1. **Disponibilidade**: Nem todos os livros estão disponíveis no Libgen
2. **Formato**: Busca exclusivamente livros em formato EPUB
3. **Tempo de Execução**: Processo completo pode levar várias horas
4. **Espaço em Disco**: Pode ocupar vários GB dependendo da disponibilidade
5. **Conectividade**: Libgen pode estar bloqueado em algumas regiões (use VPN se necessário)
6. **Filtro de Autor**: Livros só são baixados se o autor corresponder exatamente

## 🔧 Arquitetura

O projeto utiliza **Programação Orientada a Objetos** com separação clara de responsabilidades:

### Classe Scraper (`scripts/scraper.py`)

Gerencia todo o processo de web scraping:

```python
from scripts.scraper import Scraper

# Uso básico
scraper = Scraper()
scraper.run()  # Executa todo o processo

# Uso customizado
scraper = Scraper(base_url="https://custom-site.com")
scraper.run()
```

**Atributos:**

- `base_url` - URL base do site a ser raspado
- `books_dir` - Pasta onde os livros serão salvos
- `total_downloaded` - Contador de downloads bem-sucedidos
- `total_failed` - Contador de falhas

**Métodos Públicos:**

- `run()` - Executa o processo completo de scraping e download

**Métodos Privados:**

- `_get_all_lists()` - Extrai todas as listas do site
- `_get_books_from_list(url)` - Extrai livros de uma lista específica
- `_download_book(book, folder)` - Baixa um livro via Libgen
- `_process_list(title, url)` - Processa uma lista completa
- `_print_summary()` - Exibe relatório final

### Classe Libgen (`scripts/libgen.py`)

Gerencia busca e download via Libgen API:

```python
from scripts.libgen import Libgen
from pathlib import Path

# Inicialização
libgen = Libgen(
    mirror="li",              # Mirror: "li", "lc", "rs"
    title="Clean Code",
    author="Robert Martin"
)

# Busca filtrada
results = libgen.search_title()  # Retorna lista de Books

# Download
if results:
    libgen.download(Path("./books"), results[0])
```

**Características:**

- **Busca inteligente**: Filtra por sobrenome do autor (tolerante a variações)
- **Fallback automático**: Se não encontrar com filtro, retorna primeiros resultados
- **Download resiliente**: Timeout de 120s com retry automático (2 tentativas)
- Sanitização automática de nomes de arquivo
- Formato exclusivo: EPUB
- **Pula arquivos existentes**: Verifica se o arquivo já existe antes de baixar
- **Tratamento de erros**: Captura timeouts 504 e erros HTTP
- Retorna `True` se baixou, `False` se pulou

**Filtro de Autor:**

```python
# Aceita variações de formato
"Martin Fowler"           → busca por "fowler"
"Fowler, Martin"          → busca por "fowler"  ✓
"Kent Beck, Martin Fowler" → busca por "beck" OU "fowler"
"Robert C. Martin"        → busca por "martin"
```

### DataClass BookInfo (`scripts/utils.py`)

Representa informações estruturadas de um livro:

```python
from scripts.utils import BookInfo

# Criar instância
book = BookInfo(
    title="Clean Code",
    author="Robert Martin"
)

# Acessar atributos
print(book.title)   # "Clean Code"
print(book.author)  # "Robert Martin"
print(book)         # "Clean Code - Robert Martin"
```

**Benefícios:**

- Type safety com type hints
- Validação automática de atributos
- Método `__str__` para representação legível
- Imutabilidade opcional via `frozen=True`

### Funções Utilitárias (`scripts/utils.py`)

```python
from scripts.utils import slugify, get_author, get_title

# Conversão para slug
slugify("Best Python Books")  # → "best-python-books"

# Formatação de autor
get_author("Kenneth Reitz & Tanya Schlusser")  # → "Kenneth Reitz, Tanya Schlusser"

# Formatação de título
get_title("  clean code  ")  # → "Clean Code"
```

## 📝 Exemplo de Log

```text
📚 Best Books Downloader
============================================================
Iniciando download completo de todas as listas...
============================================================

🔍 Buscando listas de livros...
✓ Encontradas 50 listas

============================================================
📚 Processando lista: Best Python Books
============================================================
📁 Pasta: books\best-python-books
  📖 Acessando lista: https://www.best-books.dev/list/best-python-books
  ✓ Encontrados 25 livros

  [1/25]
    🔍 Buscando: Python Crash Course - Eric Matthes
    ⬇️  Baixando...
    ✓ Download concluído!

  [2/25]
    🔍 Buscando: Automate the Boring Stuff with Python - Al Sweigart
    ⬇️  Baixando...
    ✓ Download concluído!

  [3/25]
    🔍 Buscando: Fluent Python - Luciano Ramalho
    ⏭️  Arquivo já existe, pulando download

  [4/25]
    🔍 Buscando: Deep Learning with Python - François Chollet
    ⬇️  Baixando...
    ✔ Download concluído!
...

============================================================
🎉 PROCESSO CONCLUÍDO!
============================================================
✓ Livros baixados com sucesso: 847
❌ Livros não encontrados/erro: 253
📁 Todos os livros estão na pasta: D:\Workspace\best-books\books
```

## 🐛 Troubleshooting

### Erro de Conexão com Libgen

```text
ConnectTimeout: Connection to libgen.is timed out
```

**Soluções:**

1. Verifique sua conexão com internet
2. O Libgen pode estar bloqueado - use VPN
3. Tente outro mirror modificando `scripts/libgen.py`

### Livro não encontrado

```text
⚠️  Livro não encontrado no Libgen
```

**Motivos:**

- Livro não está disponível no Libgen
- Nome do autor não corresponde exatamente
- Livro não está em formato EPUB

### Erro de Encoding no Windows

```text
UnicodeEncodeError: 'charmap' codec can't encode
```

**Solução:** Já corrigido no código com `encoding="utf-8"`

### Testes falhando

Se testes de rede falharem, execute apenas testes locais:

```bash
uv run pytest -m "not network and not slow"
```

## 📊 Estatísticas

**Cobertura de Testes:**

- 25 testes automatizados
- Cobertura de testes unitários e integração
- Testes de rede marcados separadamente

**Arquivos de Código:**

- `scraper.py`: ~159 linhas
- `libgen.py`: ~45 linhas
- `utils.py`: ~22 linhas
- Total: ~226 linhas de código (sem comentários)

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

**Antes de contribuir:**

- Execute os testes: `uv run pytest`
- Verifique o linting: `uv run ruff check .`
- Atualize a documentação se necessário

## 📄 Licença

Este projeto é apenas para fins educacionais. Respeite os direitos autorais dos livros.

## ⚖️ Disclaimer

Este projeto é apenas para fins educacionais e de pesquisa. Os usuários são responsáveis por garantir que seu uso esteja em conformidade com todas as leis aplicáveis de direitos autorais e propriedade intelectual.
