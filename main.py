from fastapi import FastAPI , HTTPException,status,Depends
from pydantic import BaseModel
from sqlmodel import SQLModel, Field  , create_engine

sqlite_file_name = "bookstore.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)

app = FastAPI()

class Book(SQLModel , table=True):
    id : int | None = Field(default=None , primary_key=True)
    title : str
    author : str
    price : float


books_db:dict[int,dict]={}
next_id = 1

def get_book_or_404(book_id:int):
    if book_id not in books_db:
        raise HTTPException(status_code=404,detail="book not found")
    return books_db[book_id
                    ]
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
def get_book(book:dict = Depends(get_book_or_404)):
    return book
    

@app.delete("/books/{book_id}" , status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int,book:dict = Depends(get_book_or_404)):
    del books_db[book_id]
    return None


#next chapter is about async 

