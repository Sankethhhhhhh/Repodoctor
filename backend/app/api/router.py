from fastapi import APIRouter

from app.api.compare_router import compare_router
from app.api.export_router import export_router
from app.api.remediation_router import remediation_router
from app.api.reports_router import reports_router
from app.api.schedules_router import schedules_router
from app.api.webhooks_router import webhooks_router
from app.auth.router import auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(reports_router)
api_router.include_router(export_router)
api_router.include_router(compare_router)
api_router.include_router(schedules_router)
api_router.include_router(webhooks_router)
api_router.include_router(remediation_router)
