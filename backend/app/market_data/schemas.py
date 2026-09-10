from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class HistoricalBar(BaseModel):
    """A provider-neutral, validated historical OHLCV bar."""

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(min_length=1, max_length=16)
    timestamp: datetime
    open: Decimal = Field(gt=0)
    high: Decimal = Field(gt=0)
    low: Decimal = Field(gt=0)
    close: Decimal = Field(gt=0)
    volume: int = Field(ge=0)
    source: str = Field(min_length=1, max_length=32)
    timeframe: str = Field(min_length=1, max_length=8)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("symbol must not be blank")
        return normalized

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_ohlc_range(self) -> "HistoricalBar":
        if not self.low <= self.open <= self.high:
            raise ValueError("open must be between low and high")
        if not self.low <= self.close <= self.high:
            raise ValueError("close must be between low and high")
        return self


class LatestQuote(BaseModel):
    """A provider-neutral latest best bid and ask quote."""

    model_config = ConfigDict(frozen=True)

    symbol: str = Field(min_length=1, max_length=16)
    timestamp: datetime
    bid_price: Decimal = Field(gt=0)
    ask_price: Decimal = Field(gt=0)
    bid_size: int = Field(ge=0)
    ask_size: int = Field(ge=0)
    source: str = Field(min_length=1, max_length=32)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("symbol must not be blank")
        return normalized

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return value.astimezone(UTC)

    @model_validator(mode="after")
    def validate_spread(self) -> "LatestQuote":
        if self.ask_price < self.bid_price:
            raise ValueError("ask price must not be below bid price")
        return self
