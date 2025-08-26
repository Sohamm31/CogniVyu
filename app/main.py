from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware

from .database import engine
from . import models, config
from . import auth_routes, chat_routes  

app = FastAPI()

origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(SessionMiddleware, secret_key=config.settings.SECRET_KEY, https_only=False, same_site="lax")

models.Base.metadata.create_all(engine)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth_routes.router)
app.include_router(chat_routes.router)



@app.get("/")
async def read_index():
    return FileResponse("app/static/landing.html")
