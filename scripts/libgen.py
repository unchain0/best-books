from libgen_api_enhanced import LibgenSearch
from libgen_api_enhanced.book import Book
import requests
from utils import filter_results, get_author, get_title
from pathlib import Path


class Libgen:
    def __init__(self, mirror: str = "li", *, title: str = "", author: str = ""):
        self.search = LibgenSearch(mirror=mirror)
        self.title = get_title(title)
        self.author = get_author(author)

    def search_title(self) -> list[Book]:
        results = self.search.search_title_filtered(
            query=self.title,
            filters={"extension": "epub"},
        )
        return filter_results(results, self.author)

    def download(self, folder: Path, book: Book) -> None:
        book.resolve_direct_download_link()
        resp = requests.get(book.resolved_download_link)
        with open(folder / (book.title + ".epub"), "wb") as f:
            f.write(resp.content)


if __name__ == "__main__":
    libgen = Libgen(title="The Self-Taught Programmer", author="Cory Althoff")
    results = libgen.search_title()
    libgen.download(Path("."), results[0])
