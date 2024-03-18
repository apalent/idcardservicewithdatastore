from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, MetaData, Table, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from databases import Database
import os
from sqlalchemy import inspect
from io import StringIO
import json

# Create a FastAPI instance
app = FastAPI()
Base = declarative_base()

# Add the CORS middleware to allow any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

# Define the IDCard model
class IDCard(Base):
    __tablename__ = "id_cards"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    bank_name = Column(String)
    phone_number = Column(String, unique=True, index=True)
    date_of_birth = Column(String)
    blood_group = Column(String)
    address = Column(String)
    branch = Column(String)  # Add the "branch" field as a string

# Check if the database file exists, and create it if it doesn't
if not os.path.exists("id_card.db"):
    open("id_card.db", "w").close()

# Database setup
DATABASE_URL = "sqlite:///./id_card.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
database = Database(DATABASE_URL)

# Create the metadata and the table if it doesn't exist
metadata = MetaData()
id_cards_table = Table(
    "id_cards",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("name", String, index=True),
    Column("bank_name", String),
    Column("phone_number", String, unique=True, index=True),
    Column("date_of_birth", String),
    Column("blood_group", String),
    Column("address", String),
    Column("branch", String),  # Add the "branch" field
    extend_existing=True,
)

# Create the table if it doesn't exist
if not inspect(engine).has_table("id_cards"):
    metadata.create_all(engine)

# Pydantic model for ID card data
class IDCardCreate(BaseModel):
    name: str
    bank_name: str
    phone_number: str
    date_of_birth: str
    blood_group: str
    address: str
    branch: str  # Add the "branch" field

class IDCardResponse(BaseModel):
    id: int
    name: str
    bank_name: str
    phone_number: str
    date_of_birth: str
    blood_group: str
    address: str
    branch: str  # Add the "branch" field

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
                f"blood_group = :blood_group, "
                f"address = :address, "  # Include the "address" field
                f"branch = :branch "  # Include the "branch" field
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
                "INSERT INTO id_cards (name, bank_name, phone_number, date_of_birth, blood_group, address, branch) "
                "VALUES (:name, :bank_name, :phone_number, :date_of_birth, :blood_group, :address, :branch)"  # Include the "address" and "branch" fields
            )
            last_record_id = await database.execute(query, values=id_card.dict())
            id_card_record = await database.fetch_one(
                "SELECT * FROM id_cards WHERE id = :id",
                values={"id": last_record_id},
            )

        return IDCardResponse(**id_card_record)

# Endpoint to get ID card details by phone number (optional)
@app.get("/id_card/")
async def read_id_card(phone_number: str = None):
    if phone_number is not None:
        # If a phone number is provided, return specific data
        id_card_record = await database.fetch_one(
            "SELECT * FROM id_cards WHERE phone_number = :phone_number",
            values={"phone_number": phone_number},
        )
        if id_card_record is None:
            raise HTTPException(status_code=404, detail="ID card not found")
        return IDCardResponse(**id_card_record)
    else:
        # If no phone number is provided, return all data
        id_card_records = await database.fetch_all("SELECT * FROM id_cards")
        return id_card_records

@app.delete("/id_card/{phone_number}", response_model=str)
async def delete_id_card(phone_number: str):
    async with database.transaction():
        # Check if the phone number exists in the database
        existing_record = await database.fetch_one(
            "SELECT * FROM id_cards WHERE phone_number = :phone_number",
            values={"phone_number": phone_number},
        )

        if not existing_record:
            raise HTTPException(status_code=404, detail="ID card not found")

        # If the phone number exists, delete the record
        await database.execute(
            "DELETE FROM id_cards WHERE phone_number = :phone_number",
            values={"phone_number": phone_number},
        )

    return "ID card deleted successfully"
    
@app.delete("/delete_all_id_cards/", response_model=str)
async def delete_all_id_cards():
    async with database.transaction():
        # Check if any records exist in the id_cards table
        existing_records = await database.fetch_all("SELECT * FROM id_cards")

        # If no records found, return appropriate message
        if not existing_records:
            return "No ID cards found to delete"

        # If records found, delete all records from the id_cards table
        await database.execute("DELETE FROM id_cards")

    return "All ID cards deleted successfully"


@app.post("/copy_data_from_json/")
async def copy_data_from_json(json_data_str: str):
    # Attempt to parse the JSON data from the input string
    try:
        customer_data = json.loads(json_data_str)
    except json.JSONDecodeError as e:
        return {"error": "Invalid JSON format"}

    # Process the JSON data
    for item in customer_data:
        # Extract relevant fields from the JSON data
        name = item.get("name")
        bank_name = item.get("bank_name")
        phone_number = item.get("phone_number")
        blood_group = item.get("blood_group")
        address = item.get("address")
        branch = item.get("branch")
        date_of_birth = item.get("date_of_birth")  # This may be None

        # Here you can decide how to handle a None date_of_birth, e.g., use a default date, or continue as is

        # Check if all required fields are present (excluding date_of_birth if it's optional)
        if not all([name, bank_name, phone_number, blood_group, address, branch]):
            # Skip the record or handle missing fields as needed
            continue

        # Check if the phone number already exists in the database
        existing_record = await database.fetch_one(
            "SELECT * FROM id_cards WHERE phone_number = :phone_number",
            values={"phone_number": phone_number},
        )
        if existing_record:
            # If the phone number exists, update the existing record, including date_of_birth handling
            query = (
                "UPDATE id_cards SET "
                "name = :name, "
                "bank_name = :bank_name, "
                "blood_group = :blood_group, "
                "address = :address, "
                "branch = :branch, "
                "date_of_birth = :date_of_birth "  # Include date_of_birth in the update
                "WHERE phone_number = :phone_number"
            )
            await database.execute(
                query,
                values={"name": name, "bank_name": bank_name, "blood_group": blood_group,
                        "address": address, "branch": branch, "phone_number": phone_number,
                        "date_of_birth": date_of_birth},
            )
        else:
            # If the phone number doesn't exist, insert a new record, including date_of_birth
            query = (
                "INSERT INTO id_cards (name, bank_name, phone_number, date_of_birth blood_group, address, branch) "
                "VALUES (:name, :bank_name, :phone_number,:date_of_birth :blood_group, :address, :branch)"
            )
            await database.execute(
                query,
                values={"name": name, "bank_name": bank_name, "phone_number": phone_number, "date_of_birth": date_of_birth
                        "blood_group": blood_group, "address": address, "branch": branch},
            )

    return {"message": "Data processed successfully"}
    
# Run the FastAPI app
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
