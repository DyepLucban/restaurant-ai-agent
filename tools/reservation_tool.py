from langchain_core.tools import tool
from repository.table_repository import browse, edit
from database.connection import SessionAsync
from sqlalchemy.exc import SQLAlchemyError

@tool
async def search_available_tables(capacity: int | None = None) -> str:
    """
    Check which restaurant's tables are currently available for booking.

    Use this when the user wants to reserve a table or asks about availability.
    Optionally pass `capacity` (the party size) to return only tables that
    can seat that many people. If omitted, all available tables are returned.
    """
    try:
        async with SessionAsync() as db:
            tables = await browse(db)

        # If user doesn't specify party size
        available_tables = [table for table in tables if not table.is_reserved]

        # If user specify party size
        if capacity:
            available_tables = [table for table in tables if not table.is_reserved and table.capacity >= capacity]

        # If no available table
        if not available_tables:
            return "No available tables at the moment."

        response = "Available tables:\n"
        for table in available_tables:
            response += f"Table Number: {table.table_number}, Capacity: {table.capacity}\n"

        print(f"RESERVATION MESSAGE: {response}")

        return response
    except SQLAlchemyError as e:
        return f"Error searching for available tables: {str(e)}"

@tool
async def book_table(table_number: int, reserved_date: str) -> str:
    """
    Book a table for a specific date.
    Pass the table number and the date in YYYY-MM-DD format.
    """
    try:
        async with SessionAsync() as db:
            await edit(table_number, reserved_date, db)
            await db.commit()

        return f"Table {table_number} has been successfully booked for {reserved_date}."
    except SQLAlchemyError as e:
        await db.rollback()
        return f"Error booking table: {str(e)}"