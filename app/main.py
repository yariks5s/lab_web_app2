from io import BytesIO
from fastapi import FastAPI, Request, File, UploadFile, Form
from PIL import Image
import uvicorn
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from router import router as users_router
from database import con, create_db, users, books, chapters, authors
from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

app.include_router(users_router)


templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
async def database():
    create_db()

@app.get("/")
async def get_index(request: Request):
    query_for_books = "SELECT * FROM books"
    res = con.execute(query_for_books)
    books = [book for book in res]
    # print(books)
    context = {"books": books}
    return templates.TemplateResponse("index.html", {"request": request, **context})

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    query = "SELECT * FROM users WHERE id = %s"
    result = con.execute(query, (user_id,))

    return result.fetchone()

# region Create Book
@app.post("/add_books/")
async def submit_form(title: str = Form('title'), authors: str = Form('authors'), description: str = Form('description')
                      , photo: UploadFile = File(None)):
    query = con.execute("SELECT id FROM authors WHERE id = %s", (authors,))
    author = query.fetchone()[0]  # extract id from dictionary

    if photo is not None and photo.content_type.split("/")[0] == "image":
        try:
            with Image.open(photo.file) as img:
                # Resize the photo to a maximum width and height of 800 pixels
                img.thumbnail((800, 800))

                # Convert the photo to RGB mode
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Convert the photo to bytes
                with BytesIO() as output:
                    img.save(output, format="JPEG")
                    photo_bytes = output.getvalue()

                data = con.execute(books.insert().values(
                    title=title,
                    description=description,
                    author_id=author,
                    photo=photo_bytes,
                ))
        except Exception as e:
            return {"message": "Error processing photo: {}".format(e)}
    else:
        try:
            with Image.open("templates/static/img/default_user.png") as img:
                # Resize the photo to a maximum width and height of 800 pixels
                img.thumbnail((800, 800))

                # Convert the photo to RGB mode
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Convert the photo to bytes
                with BytesIO() as output:
                    img.save(output, format="JPEG")
                    photo_bytes = output.getvalue()

                data = con.execute(books.insert().values(
                    title=title,
                    description=description,
                    author_id=author,
                    photo=photo_bytes,
                ))
        except Exception as e:
            return {"message": "Error processing photo: {}".format(e)}

    return {"message": "Form submitted successfully."}

@app.get("/upload_book/")
async def form(request: Request):
    query = con.execute("SELECT * FROM authors")
    author_list = [author for author in query]
    context = {"authors": author_list}
    return templates.TemplateResponse("upload_book.html", {"request": request, **context})
# endregion

# region Create Chapter
@app.post("/add_chapter/")
async def submit_form(books: str = Form('books'), title: str = Form('title'), context: str = Form('context')):
    query = con.execute("SELECT id FROM books WHERE id = %s", (books,))
    book = query.fetchone()[0]  # extract id from dictionary
    data = con.execute(chapters.insert().values(
        title=title,
        context=context,
        book_id=book,
    ))
    return {"message": "Form submitted successfully."}

@app.get("/upload_chapter/", response_class=HTMLResponse)
async def form(request: Request):
    query = con.execute("SELECT * FROM books")
    books = [book for book in query]
    context = {"books": books}
    return templates.TemplateResponse("upload_chapter.html", {"request": request, **context})
# endregion

# region Create Author
@app.post("/add_author/")
async def submit_form(name: str = Form('name'), city: str = Form('city'), description: str = Form('desc'),
                      photo: UploadFile = File(None)):
    if photo is not None and photo.content_type.split("/")[0] == "image":
        try:
            with Image.open(photo.file) as img:
                # Resize the photo to a maximum width and height of 800 pixels
                img.thumbnail((800, 800))

                # Convert the photo to RGB mode
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Convert the photo to bytes
                with BytesIO() as output:
                    img.save(output, format="JPEG")
                    photo_bytes = output.getvalue()

                data = con.execute(authors.insert().values(
                    name=name,
                    description=description,
                    city=city,
                    photo=photo_bytes,
                ))
        except Exception as e:
            return {"message": "Error processing photo: {}".format(e)}
    else:
        try:
            with Image.open("templates/static/img/default_user.png") as img:
                # Resize the photo to a maximum width and height of 800 pixels
                img.thumbnail((800, 800))

                # Convert the photo to RGB mode
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Convert the photo to bytes
                with BytesIO() as output:
                    img.save(output, format="JPEG")
                    photo_bytes = output.getvalue()

                data = con.execute(authors.insert().values(
                    name=name,
                    city=city,
                    description=description,
                    photo=photo_bytes,
                ))
        except Exception as e:
            return {"message": "Error processing photo: {}".format(e)}

    return {"message": "Form submitted successfully."}

@app.get("/upload_author/")
async def form():
    return FileResponse("templates/upload_author.html")
# endregion

# region Create User
@app.post("/add_user/")
async def submit_form(username: str = Form('username'), email: str = Form('email'), photo: UploadFile = File(None)):
    if photo is not None and photo.content_type.split("/")[0] == "image":
        try:
            with Image.open(photo.file) as img:
                # Resize the photo to a maximum width and height of 800 pixels
                img.thumbnail((800, 800))

                # Convert the photo to RGB mode
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Convert the photo to bytes
                with BytesIO() as output:
                    img.save(output, format="JPEG")
                    photo_bytes = output.getvalue()

                data = con.execute(users.insert().values(
                    username=username,
                    email=email,
                    photo=photo_bytes,
                ))
        except Exception as e:
            return {"message": "Error processing photo: {}".format(e)}
    else:
        try:
            with Image.open("templates/static/img/default_user.png") as img:
                # Resize the photo to a maximum width and height of 800 pixels
                img.thumbnail((800, 800))

                # Convert the photo to RGB mode
                if img.mode != "RGB":
                    img = img.convert("RGB")

                # Convert the photo to bytes
                with BytesIO() as output:
                    img.save(output, format="JPEG")
                    photo_bytes = output.getvalue()

                data = con.execute(users.insert().values(
                    username=username,
                    email=email,
                    photo=photo_bytes,
                ))
        except Exception as e:
            return {"message": "Error processing photo: {}".format(e)}

    return {"message": "Form submitted successfully."}

@app.get("/upload_user/")
async def form():
    return FileResponse("templates/upload_user.html")
# endregion

@app.delete("/users/{user_id}")
async def delete_user(user_id: int):
    data = con.execute("DELETE FROM users WHERE id = %s", (user_id,))
    return {"message": "User deleted successfully"}



if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
