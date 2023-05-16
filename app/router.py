from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/users",
    tags=["home"],
)

templates = Jinja2Templates(directory="templates")

