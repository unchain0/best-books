"""
Best Books Downloader - Script principal
Web scraping do site best-books.dev com download automático via Libgen

Executa o download completo de TODAS as listas e TODOS os livros do site.
"""
from scripts.scraper import run_scraper


if __name__ == "__main__":
    print("📚 Best Books Downloader")
    print("=" * 60)
    print("Iniciando download completo de todas as listas...")
    print("=" * 60)
    print()
    
    run_scraper()
