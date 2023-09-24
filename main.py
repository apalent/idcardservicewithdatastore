from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, update
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from databases import Database

# Create a FastAPI instance
app = FastAPI()
Base = declarative_base()
# Database setup
DATABASE_URL = "sqlite:///./id_card.db"
# Check if the database file exists, and if not, create it
if not os.path.exists("id_card.db"):
    engine = create_engine(DATABASE_URL)
    engine.execute("""
    CREATE TABLE id_cards (
        id INTEGER PRIMARY KEY,
        name TEXT,
        bank_name TEXT,
        phone_number TEXT UNIQUE,
        date_of_birth TEXT,
        blood_group TEXT
    )
    """)
database = Database(DATABASE_URL)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the IDCard model
class IDCard(Base):
    __tablename__ = "id_cards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    bank_name = Column(String)
    phone_number = Column(String, unique=True, index=True)
    date_of_birth = Column(String)
    blood_group = Column(String)

# Pydantic model for ID card data
class IDCardCreate(BaseModel):
    name: str
    bank_name: str
    phone_number: str
    date_of_birth: str
    blood_group: str

class IDCardResponse(BaseModel):
    id: int
    name: str
    bank_name: str
    phone_number: str
    date_of_birth: str
    blood_group: str

# Endpoint to save ID card details
@app.post("/id_card/", response_model=IDCardResponse)
async def create_id_card(id_card: IDCardCreate):
    async with database.transaction():
        # Check if the phone number already exists in the database
        existing_record = await database.fetch_one(
            "SELECT * FROM id_cards WHERE phone_number = :phone_number",
            values={"phone_number": id_card.phone_number},
        )

        if existing_record:
            # If the phone number exists, update the existing record
            query = (
                f"UPDATE id_cards SET "
                f"name = :name, "
                f"bank_name = :bank_name, "
                f"date_of_birth = :date_of_birth, "
                f"blood_group = :blood_group "
                f"WHERE phone_number = :phone_number"
            )
            await database.execute(
                query,
                values=id_card.dict(),
            )
            id_card_record = await database.fetch_one(
                "SELECT * FROM id_cards WHERE phone_number = :phone_number",
                values={"phone_number": id_card.phone_number},
            )
        else:
            # If the phone number doesn't exist, insert a new record
            query = (
                "INSERT INTO id_cards (name, bank_name, phone_number, date_of_birth, blood_group) "
                "VALUES (:name, :bank_name, :phone_number, :date_of_birth, :blood_group)"
            )
            last_record_id = await database.execute(query, values=id_card.dict())
            id_card_record = await database.fetch_one(
                "SELECT * FROM id_cards WHERE id = :id",
                values={"id": last_record_id},
            )

        return IDCardResponse(**id_card_record)

# Endpoint to get ID card details by phone number
@app.get("/id_card/{phone_number}", response_model=IDCardResponse)
async def read_id_card(phone_number: str = Path(..., title="The phone number of the ID card owner")):
    id_card_record = await database.fetch_one(
        "SELECT * FROM id_cards WHERE phone_number = :phone_number",
        values={"phone_number": phone_number},
    )
    if id_card_record is None:
        raise HTTPException(status_code=404, detail="ID card not found")
    return IDCardResponse(**id_card_record)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
