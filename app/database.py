from sqlalchemy import create_engine, Column, Integer, String, MetaData, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv
from sqlalchemy import create_engine, Table, Column, Integer, String, MetaData, BLOB

load_dotenv()

import os

engine = create_engine(f'mysql+mysqlconnector://root:password@172.26.0.2/lab2')

meta = MetaData()

con = engine.connect()

Session = sessionmaker(bind=engine)

Base = declarative_base()

# create a metadata object
metadata = MetaData()

# define a users table with username and email columns
users = Table("users", metadata,
              Column("id", Integer, primary_key=True),
              Column("username", String(50)),
              Column("email", String(30)),
              Column("photo", BLOB), )

books = Table("books", metadata,
              Column("id", Integer, primary_key=True),
              Column("title", String(50)),
              Column("description", String(500)),
              Column("photo", BLOB),
              Column("author_id", Integer, ForeignKey("authors.id", ondelete="CASCADE")),
              )

authors = Table("authors", metadata,
                Column("id", Integer, primary_key=True),
                Column("name", String(50)),
                Column("city", String(50)),
                Column("description", String(500)),
                Column("photo", BLOB),
                )

chapters = Table("chapters", metadata,
                 Column("id", Integer, primary_key=True),
                 Column("title", String(50)),
                 Column("context", String(500)),
                 Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE")),
                 )

comments = Table("comments", metadata,
                 Column("id", Integer, primary_key=True),
                 Column("text", String(500)),
                 Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE")),
                 Column("book_id", Integer, ForeignKey("books.id", ondelete="CASCADE")),
                 )


def create_db() -> None:
    # create the users table if it doesn't already exist
    metadata.create_all(engine)
