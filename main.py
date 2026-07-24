from fastapi import FastAPI , HTTPException,status
from pydantic import BaseModel

app = FastAPI()

class Book(BaseModel):
    title:str
    author : str
    price : float

books_db:dict[int,dict]={}
next_id = 1

@app.post("/books" , status_code=status.HTTP_201_CREATED)
def create_book(book: Book):
    global next_id
    book_data = book.dict()
    book_data["id"]=next_id
    books_db[next_id] = book_data
    next_id +=1
    return book_data

@app.get("/books")
def list_books():
    return list(books_db.values())

@app.get("/books/{book_id}")
def get_book(book_id:int):
    if book_id not in books_db:
        raise HTTPException(status_code=404 , detail="book not found")
    return books_db[book_id]

