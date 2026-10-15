from langchain_core.tools import tool
from repository.table_repository import browse, edit
from database.connection import SessionAsync
from sqlalchemy.exc import SQLAlchemyError
from itertools import combinations

def find_tables(capacity: int, free_tables: list):
    singles = sorted(
        (t for t in free_tables if t.capacity >= capacity),
        key=lambda t: t.capacity,
    )
    if singles:
        return "single", singles

    for n in range(2, len(free_tables) + 1):
        combos = [
            c for c in combinations(free_tables, n)
            if sum(t.capacity for t in c) >= capacity
        ]
        if combos:
            best = min(combos, key=lambda c: sum(t.capacity for t in c) - capacity)
            return "split", list(best)

    return "none", []

@tool
async def search_available_tables(capacity: int | None = None) -> str:
    """
    Check which restaurant tables are currently available for booking.

    Use this when the user wants to reserve a table or asks about availability.
    Pass `capacity` (the party size). The result starts with a type:
    - single: tables that each seat the whole party
    - split: no single table fits; the listed tables together seat the party
    - none: not enough free tables
    If `capacity` is omitted, all free tables are returned.
    """
    try:
        async with SessionAsync() as db:
            tables = await browse(db)

        free_tables = [t for t in tables if not t.is_reserved]

        if capacity:
            result_type, chosen = find_tables(capacity, free_tables)
        else:
            result_type, chosen = ("single", free_tables) if free_tables else ("none", [])

        if result_type == "none":
            return "Type: none. Sorry, currently we don't have available tables for that party size."

        lines = [f"Type: {result_type}"]
        for t in chosen:
            lines.append(f"Table Number: {t.table_number}, Capacity: {t.capacity}")
        if result_type == "split":
            lines.append(f"Combined capacity: {sum(t.capacity for t in chosen)}")

        response = "\n".join(lines)
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