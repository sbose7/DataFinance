"""deal-analyzer: underwrite rental, flip, and BRRRR real estate deals."""

from .brrrr import BRRRRDeal, analyze_brrrr
from .compare import compare
from .finance import irr, npv
from .flip import FlipDeal, analyze_flip
from .kinds import KINDS, run
from .mortgage import amortization_schedule, monthly_payment, remaining_balance
from .projection import ProjectionAssumptions, project
from .refi import RefiScenario, analyze_refi
from .rental import RentalDeal, analyze_rental
from .sensitivity import sensitivity

__all__ = [
    "monthly_payment", "amortization_schedule", "remaining_balance",
    "RentalDeal", "analyze_rental",
    "FlipDeal", "analyze_flip",
    "RefiScenario", "analyze_refi",
    "BRRRRDeal", "analyze_brrrr",
    "ProjectionAssumptions", "project",
    "irr", "npv",
    "KINDS", "run", "compare", "sensitivity",
]

__version__ = "0.2.0"
