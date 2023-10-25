from fastapi import FastAPI

from app.routers import checker

checker_app = FastAPI()
checker_app.include_router(checker.router)
