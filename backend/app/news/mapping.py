import re
from collections.abc import Mapping, Sequence

from app.news.types import NewsArticle, NewsEntity

DEFAULT_TICKER_ALIASES: Mapping[str, tuple[str, ...]] = {
    "AAPL": ("Apple", "Apple Inc"),
    "MSFT": ("Microsoft", "Microsoft Corporation"),
    "NVDA": ("NVIDIA", "Nvidia Corporation"),
    "SPY": ("SPDR S&P 500 ETF",),
    "QQQ": ("Invesco QQQ Trust",),
}


class TickerMapper:
    """Map known company aliases and explicit ticker mentions without guessing symbols."""

    def __init__(self, aliases: Mapping[str, Sequence[str]] = DEFAULT_TICKER_ALIASES) -> None:
        normalized: dict[str, tuple[str, ...]] = {}
        for ticker, names in aliases.items():
            normalized_ticker = ticker.strip().upper()
            if not re.fullmatch(r"[A-Z]{1,5}", normalized_ticker):
                raise ValueError("ticker mapper symbols must be one-to-five uppercase letters")
            normalized_names = tuple(name.strip() for name in names if name.strip())
            if not normalized_names:
                raise ValueError("ticker mapper aliases must contain at least one non-blank name")
            normalized[normalized_ticker] = normalized_names
        if not normalized:
            raise ValueError("ticker mapper aliases must not be empty")
        self._aliases = normalized

    def extract(self, article: NewsArticle) -> tuple[NewsEntity, ...]:
        """Return deterministically ordered entity mentions from the article text."""
        matches: list[tuple[int, NewsEntity]] = []
        text = article.text
        for ticker, aliases in self._aliases.items():
            for alias in aliases:
                for match in re.finditer(rf"(?<!\w){re.escape(alias)}(?!\w)", text, re.IGNORECASE):
                    matches.append((match.start(), NewsEntity(ticker, match.group())))
            for match in re.finditer(rf"(?<![A-Za-z])\$?{ticker}(?![A-Za-z])", text):
                matches.append((match.start(), NewsEntity(ticker, match.group())))
        unique: dict[tuple[str, str], tuple[int, NewsEntity]] = {}
        for index, entity in matches:
            unique.setdefault((entity.ticker, entity.mention.casefold()), (index, entity))
        return tuple(
            entity
            for _, entity in sorted(unique.values(), key=lambda item: (item[0], item[1].ticker))
        )
