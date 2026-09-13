import random
from dataclasses import dataclass, field
from decimal import Decimal

from app.backtesting.types import BacktestBar, Portfolio, Signal, SignalSide, Strategy


@dataclass(frozen=True)
class BaselineStrategyParameters:
    """Explicit, shared research inputs for the Phase 8 baseline strategy set."""

    quantity: int
    fast_window: int = 20
    slow_window: int = 50
    rsi_window: int = 14
    rsi_oversold: Decimal = Decimal("30")
    rsi_overbought: Decimal = Decimal("70")
    momentum_window: int = 20
    random_seed: int = 42
    random_action_probability: float = 0.1

    def __post_init__(self) -> None:
        if self.quantity < 1:
            raise ValueError("quantity must be at least 1")
        if self.fast_window < 1 or self.slow_window <= self.fast_window:
            raise ValueError(
                "slow_window must be greater than fast_window, and both must be positive"
            )
        if self.rsi_window < 1:
            raise ValueError("rsi_window must be positive")
        if not Decimal("0") < self.rsi_oversold < self.rsi_overbought < Decimal("100"):
            raise ValueError("RSI thresholds must satisfy 0 < oversold < overbought < 100")
        if self.momentum_window < 1:
            raise ValueError("momentum_window must be positive")
        if not 0 <= self.random_action_probability <= 1:
            raise ValueError("random_action_probability must be between 0 and 1")


@dataclass(frozen=True)
class BaselineStrategy:
    name: str
    strategy: Strategy


def build_baseline_strategies(
    parameters: BaselineStrategyParameters,
) -> tuple[BaselineStrategy, ...]:
    """Create fresh strategy state so every baseline receives the same bar period and costs."""
    return (
        BaselineStrategy("buy_and_hold", BuyAndHoldStrategy(parameters.quantity)),
        BaselineStrategy(
            "moving_average_crossover",
            MovingAverageCrossoverStrategy(
                parameters.quantity,
                fast_window=parameters.fast_window,
                slow_window=parameters.slow_window,
            ),
        ),
        BaselineStrategy(
            "rsi_mean_reversion",
            RsiMeanReversionStrategy(
                parameters.quantity,
                window=parameters.rsi_window,
                oversold=parameters.rsi_oversold,
                overbought=parameters.rsi_overbought,
            ),
        ),
        BaselineStrategy(
            "momentum",
            MomentumStrategy(parameters.quantity, window=parameters.momentum_window),
        ),
        BaselineStrategy(
            "random",
            RandomStrategy(
                parameters.quantity,
                seed=parameters.random_seed,
                action_probability=parameters.random_action_probability,
            ),
        ),
    )


@dataclass
class BuyAndHoldStrategy:
    quantity: int
    _submitted: bool = field(default=False, init=False)

    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None:
        if self._submitted:
            return None
        self._submitted = True
        return Signal(bar.timestamp, bar.symbol, SignalSide.BUY, self.quantity)


@dataclass
class MovingAverageCrossoverStrategy:
    quantity: int
    fast_window: int
    slow_window: int
    _closes: list[Decimal] = field(default_factory=list, init=False)
    _previous_fast: Decimal | None = field(default=None, init=False)
    _previous_slow: Decimal | None = field(default=None, init=False)

    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None:
        self._closes.append(bar.close)
        if len(self._closes) < self.slow_window:
            return None
        fast = _mean(self._closes[-self.fast_window :])
        slow = _mean(self._closes[-self.slow_window :])
        signal = None
        if self._previous_fast is not None and self._previous_slow is not None:
            crossed_above = self._previous_fast <= self._previous_slow and fast > slow
            crossed_below = self._previous_fast >= self._previous_slow and fast < slow
            if crossed_above and portfolio.position is None:
                signal = Signal(bar.timestamp, bar.symbol, SignalSide.BUY, self.quantity)
            elif crossed_below and portfolio.position is not None:
                signal = Signal(
                    bar.timestamp, bar.symbol, SignalSide.SELL, portfolio.position.quantity
                )
        self._previous_fast = fast
        self._previous_slow = slow
        return signal


@dataclass
class RsiMeanReversionStrategy:
    quantity: int
    window: int
    oversold: Decimal
    overbought: Decimal
    _closes: list[Decimal] = field(default_factory=list, init=False)

    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None:
        self._closes.append(bar.close)
        rsi = _rsi(self._closes, self.window)
        if rsi is None:
            return None
        if rsi < self.oversold and portfolio.position is None:
            return Signal(bar.timestamp, bar.symbol, SignalSide.BUY, self.quantity)
        if rsi > self.overbought and portfolio.position is not None:
            return Signal(bar.timestamp, bar.symbol, SignalSide.SELL, portfolio.position.quantity)
        return None


@dataclass
class MomentumStrategy:
    quantity: int
    window: int
    _closes: list[Decimal] = field(default_factory=list, init=False)

    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None:
        self._closes.append(bar.close)
        if len(self._closes) <= self.window:
            return None
        momentum = bar.close / self._closes[-self.window - 1] - Decimal("1")
        if momentum > 0 and portfolio.position is None:
            return Signal(bar.timestamp, bar.symbol, SignalSide.BUY, self.quantity)
        if momentum <= 0 and portfolio.position is not None:
            return Signal(bar.timestamp, bar.symbol, SignalSide.SELL, portfolio.position.quantity)
        return None


@dataclass
class RandomStrategy:
    quantity: int
    seed: int
    action_probability: float
    _random: random.Random = field(init=False)

    def __post_init__(self) -> None:
        self._random = random.Random(self.seed)

    def on_bar(self, bar: BacktestBar, portfolio: Portfolio) -> Signal | None:
        if self._random.random() >= self.action_probability:
            return None
        if portfolio.position is None:
            return Signal(bar.timestamp, bar.symbol, SignalSide.BUY, self.quantity)
        return Signal(bar.timestamp, bar.symbol, SignalSide.SELL, portfolio.position.quantity)


def _mean(values: list[Decimal]) -> Decimal:
    return sum(values, Decimal("0")) / len(values)


def _rsi(closes: list[Decimal], window: int) -> Decimal | None:
    if len(closes) <= window:
        return None
    changes = [current - previous for previous, current in zip(closes, closes[1:], strict=False)]
    recent_changes = changes[-window:]
    average_gain = (
        sum((max(change, Decimal("0")) for change in recent_changes), Decimal("0")) / window
    )
    average_loss = (
        sum((max(-change, Decimal("0")) for change in recent_changes), Decimal("0")) / window
    )
    if average_loss == 0:
        return Decimal("100") if average_gain > 0 else Decimal("50")
    relative_strength = average_gain / average_loss
    return Decimal("100") - Decimal("100") / (Decimal("1") + relative_strength)
