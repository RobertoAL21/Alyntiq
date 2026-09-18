import argparse
import json
from datetime import date

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import SessionLocal
from app.market_data.alpaca import AlpacaMarketDataProvider
from app.market_data.service import HistoricalMarketDataIngestionService
from app.observability.telemetry import configure_observability


def parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("dates must use YYYY-MM-DD") from error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest validated historical market data from Alpaca"
    )
    parser.add_argument("--symbol", required=True, help="US equity or ETF symbol, for example AAPL")
    parser.add_argument("--start", required=True, type=parse_date, help="Inclusive start date")
    parser.add_argument("--end", required=True, type=parse_date, help="Inclusive end date")
    parser.add_argument(
        "--timeframe",
        default="1D",
        choices=["1D"],
        help="Bar timeframe; Phase 1 supports only 1D",
    )
    return parser


def main() -> int:
    parser = build_parser()
    arguments = parser.parse_args()
    if arguments.start > arguments.end:
        parser.error("--start must not be after --end")

    configure_logging()
    settings = get_settings()
    configure_observability(settings)
    try:
        provider = AlpacaMarketDataProvider.from_settings(settings)
    except ValueError as error:
        parser.error(str(error))

    service = HistoricalMarketDataIngestionService(provider)
    with SessionLocal.begin() as session:
        result = service.ingest(
            session=session,
            symbol=arguments.symbol,
            start=arguments.start,
            end=arguments.end,
            timeframe=arguments.timeframe,
        )

    print(
        json.dumps(
            {
                "symbol": arguments.symbol.upper(),
                "received": result.storage.received,
                "inserted": result.storage.inserted,
                "skipped": result.storage.skipped,
                "potential_gaps": len(result.validation.potential_gaps),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
