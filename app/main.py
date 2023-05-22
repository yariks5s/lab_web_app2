from io import BytesIO

from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException
from PIL import Image
import uvicorn
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import join, session

from router import router as users_router
from database import con, create_db, users, books, chapters, authors, comments
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

@app.get("/show_all/")
async def show_all(request: Request):
    query = "SELECT * FROM books"
    res = con.execute(query)
    books = [book for book in res]
    query = "SELECT * FROM authors"
    res = con.execute(query)
    authors = [author for author in res]
    query = "SELECT * FROM chapters"
    res = con.execute(query)
    chapters = [chapter for chapter in res]
    query = "SELECT * FROM comments"
    res = con.execute(query)
    comments = [comment for comment in res]
    query = "SELECT * FROM users"
    res = con.execute(query)
    users = [user for user in res]


    context = {"users": users, "authors": authors, "books": books, "chapters": chapters, "comments": comments}
    return templates.TemplateResponse("show_all.html", {"request": request, **context})

# region Easy_queries
@app.post("/exec_query1/")
async def exec_query(request: Request, query1: str = Form('query1')):
    query = "SELECT * FROM users JOIN comments ON users.id = comments.user_id JOIN books ON comments.book_id = books.id " \
            "JOIN authors ON books.author_id = authors.id " \
            "WHERE authors.name = %s"
    result = con.execute(query, (query1, ))
    rows = result.fetchall()
    return templates.TemplateResponse("query_output.html", {"request": request, "rows": rows})

@app.post("/exec_query2/")
async def exec_query2(request: Request, query2: str = Form('query2')):
    query = "SELECT c.title FROM chapters c JOIN books b ON c.book_id = b.id WHERE b.author = %s;"
    result = con.execute(query, (query2, ))
    rows = result.fetchall()
    return templates.TemplateResponse("query_output.html", {"request": request, "rows": rows})

@app.post("/exec_query3/")
async def exec_query3(request: Request, query3: str = Form('query3')):
    query = "SELECT b.title FROM books b JOIN comments c ON c.book_id = b.id JOIN users u ON c.user_id = u.id " \
            "WHERE u.username = %s;"
    result = con.execute(query, (query3, ))
    rows = result.fetchall()
    return templates.TemplateResponse("query_output.html", {"request": request, "rows": rows})

@app.post("/exec_query4/")
async def exec_query4(request: Request, query4: str = Form('query4')):
    query = "SELECT DISTINCT a.city FROM authors a JOIN books b ON a.author_id = b.id JOIN chapters c ON b.book_id = c.id WHERE c.title = %s;"
    result = con.execute(query, (query4, ))
    rows = result.fetchall()
    return templates.TemplateResponse("query_output.html", {"request": request, "rows": rows})

@app.post("/exec_query5/")
async def exec_query5(request: Request, query5: str = Form('query5'), query51: str = Form('query5.1')):
    query = "SELECT b.title FROM books b JOIN authors a ON b.author_id = a.id JOIN comments c ON b.id = c.book_id JOIN users u ON c.user_id = u.id WHERE u.username = %s AND a.name = %s;"
    result = con.execute(query, (query5, query51, ))
    rows = result.fetchall()
    return templates.TemplateResponse("query_output.html", {"request": request, "rows": rows})
# endregion

# region Hard_queries
@app.post("/exec_query6/")
async def exec_query6(request: Request, query6: str = Form('query6')):
    query = "SELECT * FROM users u JOIN comments c ON u.id = c.user_id JOIN books b ON c.book_id = b.id WHERE u.username <> %s AND b.id IN (SELECT c2.book_id FROM comments c2 JOIN users u2 ON c2.user_id = u2.id WHERE u2.username = %s);"
    result = con.execute(query, (query6, query6,))
    rows = result.fetchall()
    return templates.TemplateResponse("query_output.html", {"request": request, "rows": rows})

@app.post("/exec_query7/")
async def exec_query7(request: Request, query7: str = Form('query7')):
    query = "SELECT distinct(u.username) FROM users u JOIN comments c ON u.id = c.user_id JOIN books b ON c.book_id = b.id JOIN authors a ON b.author_id = a.id WHERE lower(a.city) = lower(%s) AND NOT EXISTS (SELECT 1 FROM books b2 JOIN authors a2 ON b2.author_id = a2.id WHERE lower(a2.city) = lower(%s) AND NOT EXISTS (SELECT 1 FROM comments c2 WHERE c2.user_id = u.id AND c2.book_id = b2.id));"
    result = con.execute(query, (query7, query7,))
    rows = result.fetchall()
    return templates.TemplateResponse("query_output.html", {"request": request, "rows": rows})

@app.post("/exec_query8/")
async def exec_query8(request: Request, query8: str = Form('query8')):
    query = "SELECT distinct users.* FROM users, books b WHERE NOT EXISTS (SELECT 1 FROM users u WHERE NOT EXISTS (SELECT 1 FROM comments c WHERE c.user_id = u.id AND c.book_id = %s));"
    result = con.execute(query, (query8,))
    rows = result.fetchall()
    return templates.TemplateResponse("query_output.html", {"request": request, "rows": rows})
# endregion


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

@app.post('/books/{book_id}')
def update_book(book_id: int, title: str = Form('title'), authors: str = Form('authors'), description: str = Form('description')):
    # Update the book fields with the received data
    query = con.execute("SELECT id FROM authors WHERE id = %s", (authors,))
    author = query.fetchone()[0]
    con.execute(
        books.update()
        .where(books.c.id == book_id)
        .values(
            title=title,
            description=description,
            author_id=author,
        )
    )

    return {'message': 'Book updated successfully'}

@app.get("/update_book_form/{book_id}", response_class=HTMLResponse)
def update_book_form(request: Request, book_id: int):
    # Fetch the book data from the database
    stmt = select([books]).where(books.c.id == book_id)
    result = con.execute(stmt)
    book = result.fetchone()
    query = con.execute("SELECT * FROM authors")
    author_list = [author for author in query]
    if not book:
        raise HTTPException(status_code=404, detail='Book not found')

    return templates.TemplateResponse(
        "update_book_form.html", {"request": request, "book": book, "authors": author_list}
    )

@app.post("/delete_book/{book_id}", response_class=HTMLResponse)
def delete_book(book_id: int, request: Request):
    # Delete the book from the database
    con.execute(books.delete().where(books.c.id == book_id))
    return templates.TemplateResponse("transfer.html", {"request": request})
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

@app.post('/chapters/{chapter_id}')
def update_book(chapter_id: int, title: str = Form('title'), books: str = Form('books'), context: str = Form('context')):
    # Update the book fields with the received data
    query = con.execute("SELECT id FROM books WHERE id = %s", (books,))
    book = query.fetchone()[0]
    con.execute(
        chapters.update()
        .where(chapters.c.id == chapter_id)
        .values(
            title=title,
            context=context,
            book_id=book,
        )
    )

    return {'message': 'Chapter updated successfully'}

@app.get("/update_chapter_form/{chapter_id}", response_class=HTMLResponse)
def update_chapter_form(request: Request, chapter_id: int):
    # Fetch the book data from the database
    stmt = select([chapters]).where(chapters.c.id == chapter_id)
    result = con.execute(stmt)
    chapter = result.fetchone()
    query = con.execute("SELECT * FROM books")
    book_list = [book for book in query]
    if not chapter:
        raise HTTPException(status_code=404, detail='Chapter not found')

    return templates.TemplateResponse(
        "update_chapter_form.html", {"request": request, "chapter": chapter, "books": book_list}
    )

@app.get("/delete_chapter/{chapter_id}", response_class=HTMLResponse)
def delete_chapter(chapter_id: int, request: Request):
    # Delete the book from the database
    con.execute(chapters.delete().where(chapters.c.id == chapter_id))
    return templates.TemplateResponse("transfer.html", {"request": request})
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

@app.post('/authors/{author_id}')
def update_book(author_id: int, name: str = Form('name'), city: str = Form('city'), description: str = Form('description')):
    con.execute(
        authors.update()
        .where(authors.c.id == author_id)
        .values(
            name=name,
            city=city,
            description=description,
        )
    )

    return {'message': 'Author updated successfully'}

@app.get("/update_author_form/{author_id}", response_class=HTMLResponse)
def update_author_form(request: Request, author_id: int):
    # Fetch the book data from the database
    stmt = select([authors]).where(authors.c.id == author_id)
    result = con.execute(stmt)
    author = result.fetchone()
    if not author:
        raise HTTPException(status_code=404, detail='Author not found')

    return templates.TemplateResponse(
        "update_author_form.html", {"request": request, "author": author}
    )

@app.get("/delete_author/{author_id}", response_class=HTMLResponse)
def delete_author(author_id: int, request: Request):
    # Delete the book from the database
    con.execute(authors.delete().where(authors.c.id == author_id))
    return templates.TemplateResponse("transfer.html", {"request": request})
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

@app.post('/users/{user_id}')
def update_book(user_id: int, username: str = Form('username'), email: str = Form('email'),):
    con.execute(
        users.update()
        .where(users.c.id == user_id)
        .values(
            username=username,
            email=email,
        )
    )

    return {'message': 'User updated successfully'}

@app.get("/update_user_form/{user_id}", response_class=HTMLResponse)
def update_user_form(request: Request, user_id: int):
    # Fetch the book data from the database
    stmt = select([users]).where(users.c.id == user_id)
    result = con.execute(stmt)
    user = result.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail='User not found')

    return templates.TemplateResponse(
        "update_user_form.html", {"request": request, "user": user}
    )

@app.get("/delete_user/{user_id}", response_class=HTMLResponse)
def delete_user(user_id: int, request: Request):
    # Delete the book from the database
    con.execute(users.delete().where(users.c.id == user_id))
    return templates.TemplateResponse("transfer.html", {"request": request})
# endregion

# region Create Comment

@app.post("/add_comment/")
async def submit_form(books: str = Form('books'), users: str = Form('users'), title: str = Form('title'), context: str = Form('context')):
    query = con.execute("SELECT id FROM books WHERE id = %s", (books,))
    book = query.fetchone()[0]  # extract id from dictionary
    query = con.execute("SELECT id FROM users WHERE id = %s", (users,))
    user = query.fetchone()[0]  # extract id from dictionary
    data = con.execute(comments.insert().values(
        text=context,
        book_id=book,
        user_id=user,
    ))
    return {"message": "Form submitted successfully."}

@app.get("/upload_comment/")
async def form(request: Request):
    query = con.execute("SELECT * FROM books")
    books = [book for book in query]
    query = con.execute("SELECT * FROM users")
    users = [user for user in query]
    context = {"books": books, "users": users}
    return templates.TemplateResponse("upload_comment.html", {"request": request, **context})

@app.post('/comments/{comment_id}')
def update_book(comment_id: int, text: str = Form('text'), books: str = Form('books'), users: str = Form('users')):
    # Update the book fields with the received data
    query = con.execute("SELECT id FROM books WHERE id = %s", (books,))
    book = query.fetchone()[0]
    query = con.execute("SELECT id FROM users WHERE id = %s", (users,))
    user = query.fetchone()[0]
    con.execute(
        comments.update()
        .where(comments.c.id == comment_id)
        .values(
            text=text,
            book_id=book,
            user_id=user,
        )
    )

    return {'message': 'Comment updated successfully'}

@app.get("/update_comment_form/{comment_id}", response_class=HTMLResponse)
def update_comment_form(request: Request, comment_id: int):
    # Fetch the book data from the database
    stmt = select([comments]).where(comments.c.id == comment_id)
    result = con.execute(stmt)
    comment = result.fetchone()
    query = con.execute("SELECT * FROM books")
    book_list = [book for book in query]
    query = con.execute("SELECT * FROM users")
    user_list = [user for user in query]
    if not comment:
        raise HTTPException(status_code=404, detail='Comment not found')

    return templates.TemplateResponse(
        "update_comment_form.html", {"request": request, "comment": comment, "books": book_list, "users": user_list}
    )

@app.get("/delete_comment/{comment_id}", response_class=HTMLResponse)
def delete_comment(comment_id: int, request: Request):
    # Delete the book from the database
    con.execute(comments.delete().where(comments.c.id == comment_id))
    return templates.TemplateResponse("transfer.html", {"request": request})
# endregion


# region Create data to test
@app.get("/test_data/")
async def test_data():
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
    except Exception as e:
        return {"message": "Error processing photo: {}".format(e)}
    # region Test tables
    names_for_users = ["Alan", "Bob", "Charles", "Diana", "Eve"]
    names_for_authors = ["Max", "Steven", "John", "Hailey", "Molly"]
    cities_for_authors = ["London", "Paris", "New York", "Kyiv", "Amsterdam"]
    descriptions_for_authors = ["Description 1", "Description 2", "Description 3", "Description 4", "Description 5"]
    names_for_books = ["book1", "book2", "book3", "book4", "book5"]
    descriptions_for_books = ["Book description 1", "Book description 2", "Book description 3", "Book description 4", "Book description 5"]
    names_for_chapters = ["chapter1", "chapter2", "chapter3", "chapter4", "chapter5"]
    contexts_for_chapters = ["Chapter description 1", "Chapter description 2", "Chapter description 3", "Chapter description 4", "Chapter description 5"]
    names_for_comments = ["comment1", "comment2", "comment3", "comment4", "comment5"]
    # endregion
    for i in range(5):
        data = con.execute(users.insert().values(
            username=names_for_users[i],
            email="{}@gmail.com".format(names_for_users[i]),
            photo=photo_bytes,
        ))
        data = con.execute(authors.insert().values(
            name=names_for_authors[i],
            city=cities_for_authors[i],
            description=descriptions_for_authors[i],
            photo=photo_bytes,
        ))
        query = con.execute("SELECT id FROM authors WHERE name = %s", (names_for_authors[i],))
        author = query.fetchone()[0]  # extract id from dictionary
        data = con.execute(books.insert().values(
            title=names_for_books[i],
            description=descriptions_for_books[i],
            photo=photo_bytes,
            author_id=author,
        ))
        query = con.execute("SELECT id FROM books WHERE title = %s", (names_for_books[i],))
        book = query.fetchone()[0]  # extract id from dictionary
        data = con.execute(chapters.insert().values(
            title=names_for_chapters[i],
            context=contexts_for_chapters[i],
            book_id=book,
        ))
        query = con.execute("SELECT id FROM users WHERE username = %s", (names_for_users[i],))
        user = query.fetchone()[0]  # extract id from dictionary
        data = con.execute(comments.insert().values(
            text=names_for_comments[i],
            book_id=book,
            user_id=user,
        ))
    return {"message": "Test data inserted successfully."}

# endregion


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
