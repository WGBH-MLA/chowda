from fastapi import APIRouter

from chowda.routers import sony_ci

api = APIRouter()

api.include_router(sony_ci, prefix='/sony_ci')
