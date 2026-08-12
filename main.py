from fastapi import FastAPI , HTTPException,status,Depends
from pydantic import BaseModel
from sqlmodel import SQLModel, Field  , create_engine , Session , select
from contextlib import asynccontextmanager


sqlite_file_name = "bookstore.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url)
@asynccontextmanager
async def lifespan(app:FastAPI):
    SQLModel.metadata.create_all(engine)
    print("Server has been Started ...")
    yield
    print("Server is Shutting down ...")
    
app = FastAPI(lifespan=lifespan)

class Book(SQLModel , table=True):
    id : int | None = Field(default=None , primary_key=True)
    title : str
    author : str
    price : float

class BookCreate(SQLModel):
    title: str
    author: str
    price: float

def get_session():
    with Session(engine) as session:
        yield session

books_db:dict[int,dict]={}
next_id = 1

def get_book_or_404(book_id:int , session: Session= Depends(get_session)):
    book = session.get(Book , book_id)
    if book is None:
        raise HTTPException(status_code=404,detail="book not found")
    return book




@app.post("/books" , status_code=status.HTTP_201_CREATED)
def create_book(book_data: BookCreate , session: Session=Depends(get_session)):
    book = Book(**book_data.dict())
    session.add(book)
    session.commit()
    session.refresh(book)
    return book

@app.get("/books")
def list_books(session : Session = Depends(get_session)):
    books = session.exec(select(Book)).all()
    return books

@app.get("/books/{book_id}")
def get_book(book:Book = Depends(get_book_or_404)):
    return book
    

@app.delete("/books/{book_id}" , status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book: Book,session: Session = Depends(get_session)):
    session.delete(book)
    session.commit()
    return None


#next chapter is about async 

