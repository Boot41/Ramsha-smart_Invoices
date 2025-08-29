from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .documents import router as documents_router
from .invoices import router as invoices_router
from .bots import router as bots_router
from .emails import router as emails_router
from .llm import router as llm_router
from .contracts import router as contracts_router
from .embeddings import router as embeddings_router

routes_router = APIRouter()

routes_router.include_router(auth_router)
routes_router.include_router(users_router)
routes_router.include_router(documents_router)
routes_router.include_router(invoices_router)
routes_router.include_router(bots_router)
routes_router.include_router(emails_router)
routes_router.include_router(llm_router)
routes_router.include_router(contracts_router)
routes_router.include_router(embeddings_router)