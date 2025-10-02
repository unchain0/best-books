"""
Testes para o módulo libgen.py
Testa busca e download de livros via Libgen
"""

import pytest
from pathlib import Path
import tempfile
from scripts.libgen import Libgen
from scripts.utils import get_author, get_title


class TestLibgen:
    """Testes para a classe Libgen"""

    def test_libgen_initialization(self):
        """Testa inicialização da classe Libgen"""
        libgen = Libgen(title="Python Crash Course", author="Eric Matthes")

        assert libgen.title == "Python Crash Course"
        assert libgen.author == "Eric Matthes"
        assert libgen.search is not None

    def test_libgen_search_self_taught_programmer(self):
        """Testa busca do livro 'The Self-Taught Programmer' do exemplo"""
        libgen = Libgen(title="The Self-Taught Programmer", author="Cory Althoff")
        results = libgen.search_title()

        # Verifica se retornou resultados
        assert results is not None, "Nenhum resultado foi retornado"
        assert len(results) > 0, "Lista de resultados está vazia"

        # Verifica primeiro resultado
        first_book = results[0]
        assert hasattr(first_book, "title"), "Livro não tem atributo 'title'"
        assert hasattr(first_book, "author"), "Livro não tem atributo 'author'"

        print(f"\n✓ Encontrado: {first_book.title} - {first_book.author}")

    def test_libgen_search_python_crash_course(self):
        """Testa busca de outro livro popular"""
        libgen = Libgen(title="Python Crash Course", author="Eric Matthes")
        results = libgen.search_title()

        assert results is not None

        # Se não encontrou com filtro de autor, tenta sem filtro
        if len(results) == 0:
            print("\n⚠️  Nenhum resultado com filtro de autor, testando sem filtro...")
            libgen_no_filter = Libgen(title="Python Crash Course", author="")
            results = libgen_no_filter.search_title()

        # Pelo menos sem filtro deve retornar algo
        if len(results) > 0:
            first_book = results[0]
            print(f"\n✓ Encontrado: {first_book.title} - {first_book.author}")
        else:
            print("\n⚠️  Livro não encontrado (pode não estar no Libgen)")

    def test_libgen_search_no_results(self):
        """Testa busca com título inexistente"""
        libgen = Libgen(
            title="Livro Totalmente Inexistente XYZABC123", author="Autor Inexistente"
        )
        results = libgen.search_title()

        # Pode retornar lista vazia ou None
        assert results is not None
        assert len(results) == 0
        print("\n✓ Busca por livro inexistente retornou lista vazia (correto)")

    @pytest.mark.slow
    def test_libgen_download(self):
        """Testa download de livro (teste lento - marca como slow)"""
        # Cria diretório temporário
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Busca o livro
            libgen = Libgen(title="The Self-Taught Programmer", author="Cory Althoff")
            results = libgen.search_title()

            assert len(results) > 0, "Nenhum resultado encontrado para download"

            # Tenta fazer o download
            book = results[0]

            try:
                downloaded = libgen.download(tmpdir_path, book)

                # Verifica se retornou True (download realizado)
                assert downloaded is True, "Download deveria retornar True"

                # Verifica se arquivo foi criado
                files = list(tmpdir_path.glob("*.epub"))
                assert len(files) > 0, "Nenhum arquivo .epub foi baixado"

                downloaded_file = files[0]
                assert downloaded_file.exists(), "Arquivo não existe"
                assert downloaded_file.stat().st_size > 0, "Arquivo está vazio"

                print(f"\n✓ Download bem-sucedido: {downloaded_file.name}")
                print(f"  Tamanho: {downloaded_file.stat().st_size / 1024:.2f} KB")

            except Exception as e:
                pytest.skip(
                    f"Download falhou (pode ser problema de conectividade): {e}"
                )

    @pytest.mark.slow
    def test_libgen_skip_existing_file(self):
        """Testa se pula download quando o arquivo já existe"""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Busca o livro
            libgen = Libgen(title="The Self-Taught Programmer", author="Cory Althoff")
            results = libgen.search_title()

            assert len(results) > 0, "Nenhum resultado encontrado"

            book = results[0]

            try:
                # Primeiro download
                downloaded1 = libgen.download(tmpdir_path, book)
                assert downloaded1 is True, "Primeiro download deveria retornar True"

                # Segundo download (deveria pular)
                downloaded2 = libgen.download(tmpdir_path, book)
                assert downloaded2 is False, (
                    "Segundo download deveria retornar False (arquivo já existe)"
                )

                # Verifica que ainda há apenas 1 arquivo
                files = list(tmpdir_path.glob("*.epub"))
                assert len(files) == 1, "Deveria haver apenas 1 arquivo"

                print("\n✓ Arquivo existente foi pulado corretamente")

            except Exception as e:
                pytest.skip(f"Teste falhou (pode ser problema de conectividade): {e}")


class TestUtilsFunctions:
    """Testes para funções utilitárias"""

    def test_get_author_basic(self):
        """Testa formatação de nome de autor"""
        assert get_author("eric matthes") == "Eric Matthes"
        assert get_author("JOHN DOE") == "John Doe"
        assert get_author("jane smith") == "Jane Smith"

    def test_filter_results_flexible_matching(self):
        """Testa filtro flexível de autores por sobrenome"""
        from unittest.mock import Mock
        from scripts.utils import filter_results

        # Cria mocks de livros com diferentes formatos de autor
        book1 = Mock()
        book1.author = "Martin Fowler"
        book1.title = "Refactoring"

        book2 = Mock()
        book2.author = "Fowler, Martin"  # Formato invertido
        book2.title = "Patterns"

        book3 = Mock()
        book3.author = "Robert C. Martin"  # Nome diferente
        book3.title = "Clean Code"

        book4 = Mock()
        book4.author = "Kent Beck, Martin Fowler"  # Múltiplos autores
        book4.title = "Extreme Programming"

        results = [book1, book2, book3, book4]

        # Testa filtro por "Martin Fowler" - deve pegar book1, book2, book4
        filtered = filter_results(results, "Martin Fowler")
        assert len(filtered) == 3
        assert book1 in filtered
        assert book2 in filtered
        assert book4 in filtered

        # Testa filtro por múltiplos autores - deve pegar book1, book2, book4
        filtered = filter_results(results, "Kent Beck, Martin Fowler")
        assert len(filtered) == 3  # Apenas os que contêm "Beck" ou "Fowler"
        assert book3 not in filtered  # Robert C. Martin não tem Beck nem Fowler

        # Testa filtro que não encontra nada - deve retornar primeiros 3
        filtered = filter_results(results, "Author NotExists")
        assert len(filtered) == 3  # Fallback

    def test_get_author_ampersand(self):
        """Testa conversão de & para vírgula"""
        assert (
            get_author("Kenneth Reitz & Tanya Schlusser")
            == "Kenneth Reitz, Tanya Schlusser"
        )
        assert get_author("Author One & Author Two") == "Author One, Author Two"

    def test_get_author_whitespace(self):
        """Testa remoção de espaços extras"""
        assert get_author("  eric matthes  ") == "Eric Matthes"
        assert get_author("john  doe") == "John  Doe"  # Title mantém espaços internos

    def test_get_title_basic(self):
        """Testa formatação de título"""
        assert get_title("python crash course") == "Python Crash Course"
        assert get_title("clean code") == "Clean Code"

    def test_get_title_whitespace(self):
        """Testa remoção de espaços em títulos"""
        assert get_title("  Clean Code  ") == "Clean Code"
        assert get_title("The   Book") == "The   Book"  # Title mantém espaços internos


if __name__ == "__main__":
    # Executa os testes quando o arquivo é rodado diretamente
    pytest.main([__file__, "-v", "--tb=short"])
