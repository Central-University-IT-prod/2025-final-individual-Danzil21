from .clients import router as clients_router
from .advertisers import router as advertisers_router
from .campaigns import router as campaigns_router
from .ml_scores import router as ml_scores_router
from .ads import router as ads_router
from .time import router as time_router
from .stats import router as stats_router
from .upload import router as upload_router

__all__ = [
    "clients_router",
    "advertisers_router",
    "campaigns_router",
    "ml_scores_router",
    "ads_router",
    "time_router",
    "stats_router",
    "upload_router"
]
