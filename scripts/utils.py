from libgen_api_enhanced.book import Book


def get_author(author: str) -> str:
    return author.replace(" &", ",").strip().title()


def get_title(title: str) -> str:
    return title.strip().title()


def filter_results(results: list[Book], author: str) -> list[Book]:
    return [result for result in results if result.author == author]
