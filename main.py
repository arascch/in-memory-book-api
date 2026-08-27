from fastapi import FastAPI , HTTPException,status,Depends
from pydantic import BaseModel
from sqlmodel import SQLModel, Field  , create_engine , Session , select
from contextlib import asynccontextmanager
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta,timezone
from fastapi.security import OAuth2PasswordRequestForm , OAuth2PasswordBearer



SECRET_KEY = ""
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def create_access_token(data:dict)->str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY , algorithm=ALGORITHM)

    

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

class User(SQLModel,table = True):
    id : int| None = Field(default=None , primary_key=True)
    username: str
    hashed_password: str

class UserCreate(SQLModel):
    username: str
    password: str

pwd_context = CryptContext(schemes=["bcrypt"] , deprecated = "auto")

def hash_password(password: str)-> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password , hashed_password)

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

def get_current_user(token:str=Depends(oauth2_scheme) , session: Session = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=401,
        detail= "Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token , SECRET_KEY , algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.JWTError:
        raise credentials_exception

    user = session.exec(select(User).where(User.username == username)).first()
    if user is None:
        raise credentials_exception
    return user


@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends() , session:Session=Depends(get_session)):
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password , user.hashed_password ):
        raise HTTPException(status_code=401, detail="incorrect username or password")


    token = create_access_token(data={"sub": user.username})
    return {"access_token":token , "token_type":"bearer"}


@app.post("/books" , status_code=status.HTTP_201_CREATED)
def create_book(book_data: BookCreate , session: Session=Depends(get_session), current_user: User=Depends(get_current_user),):
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

@app.post("/register", status_code = status.HTTP_201_CREATED)
def register(user_data:UserCreate , session:Session=Depends(get_session)):
    existing = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="username already taken")

    user = User(username=user_data.username , hashed_password=hash_password(user_data.password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return{"id":user.id , "username":user.username}