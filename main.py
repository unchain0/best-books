"""
Best Books Downloader - Script principal
Web scraping do site best-books.dev com download automático via Libgen

Executa o download completo de TODAS as listas e TODOS os livros do site.
Features:
- Downloads paralelos (padrão: 3 simultâneos)
- Progress bars com Rich
- Logging detalhado em arquivo
- Estatísticas completas ao final
"""

from scripts.scraper import run_scraper


if __name__ == "__main__":
    run_scraper()
