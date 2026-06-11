from .alerts import router as alerts_router
from .screenshots import router as screenshots_router
from .rules import router as rules_router

__all__ = ['alerts_router', 'screenshots_router', 'rules_router']
