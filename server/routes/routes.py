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
from .orchestrator import router as orchestrator_router
from .eval_endpoint import router as eval_router
from .human_input import router as human_input_router
from .invoice_templates import router as invoice_templates_router
from .templates import router as templates_router
from .validation import router as validation_router

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
routes_router.include_router(orchestrator_router, prefix="/api/v1/orchestrator", tags=["🤖 Agentic Orchestrator"])
routes_router.include_router(eval_router, prefix="/api/v1", tags=["🧪 Evaluation & Testing"])
routes_router.include_router(human_input_router, tags=["👤 Human-in-the-Loop"])
routes_router.include_router(invoice_templates_router, tags=["🎨 Invoice Templates"])
routes_router.include_router(templates_router, tags=["🎨 Template Engine"])
routes_router.include_router(validation_router, tags=["✅ Validation & Human Input"])