from fastapi import FastAPI
from app.api.chat import router as chat_router
from app.ui.routes import router as ui_router

app = FastAPI()
app.include_router(chat_router)
app.include_router(ui_router)