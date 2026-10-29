"""deal-analyzer: underwrite rental, flip, and BRRRR real estate deals."""

from .mortgage import monthly_payment, amortization_schedule, remaining_balance
from .rental import RentalDeal, analyze_rental
from .flip import FlipDeal, analyze_flip
from .refi import RefiScenario, analyze_refi

__all__ = [
    "monthly_payment",
    "amortization_schedule",
    "remaining_balance",
    "RentalDeal",
    "analyze_rental",
    "FlipDeal",
    "analyze_flip",
    "RefiScenario",
    "analyze_refi",
]

__version__ = "0.1.0"
