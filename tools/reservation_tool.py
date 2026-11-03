from langchain_core.tools import tool
from repository.table_repository import browse, edit
from database.connection import SessionAsync
from sqlalchemy.exc import SQLAlchemyError

def find_tables(capacity: int, free_tables: list, max_extra: int = 2):
    # Tables that fit the party without wasting too many seats
    singles = sorted(
        (t for t in free_tables if capacity <= t.capacity <= capacity + max_extra),
        key=lambda t: t.capacity,
    )
    # Fallback: any table that fits, if nothing is close in size
    if not singles:
        singles = sorted(
            (t for t in free_tables if t.capacity >= capacity),
            key=lambda t: t.capacity,
        )
    if singles:
        return "single", singles

    # No single table fits: offer all free tables if together they can seat the party
    if sum(t.capacity for t in free_tables) >= capacity:
        return "split", sorted(free_tables, key=lambda t: t.table_number)

    return "none", []

def min_tables_needed(tables: list, capacity: int) -> int:
    """Fewest tables needed to seat the party, using the largest tables first."""
    total = 0
    for count, t in enumerate(sorted(tables, key=lambda t: t.capacity, reverse=True), start=1):
        total += t.capacity
        if total >= capacity:
            return count
    return len(tables)

@tool
async def search_available_tables(capacity: int | None = None) -> str:
    """
    Check which restaurant tables are currently available for booking.

    Use this when the user wants to reserve a table or asks about availability.
    Pass `capacity` (the party size). The result starts with a type:
    - single: each listed table seats the whole party on its own. They are
      OPTIONS; the user picks ONE. Ask which they'd like.
    - split: no single table fits. The listed tables are separate OPTIONS, not
      one group. The user picks several whose combined capacity is at least the
      party size. Never propose booking all of them. Tell the user the minimum
      number of tables they need, list the options, and ask which ones they want.
    - all: every free table (no party size given). Just list them.
    - none: not enough free tables.

    When the user chooses tables from a split result, add up the capacities of
    the chosen tables using the list from this tool. If the total is less than
    the party size, do NOT book. Tell the user the total and how many seats
    they are short, and ask them to choose again. Only call book_table when the
    total is at least the party size.
    """
    try:
        async with SessionAsync() as db:
            tables = await browse(db)

        free_tables = [t for t in tables if not t.is_reserved]

        if capacity:
            result_type, chosen = find_tables(capacity, free_tables)
        else:
            result_type, chosen = ("all", free_tables) if free_tables else ("none", [])

        if result_type == "none":
            return "Type: none. Sorry, currently we don't have available tables for that party size."

        lines = [f"Type: {result_type}"]
        if capacity:
            lines.append(f"Party size: {capacity}")

        if result_type == "single":
            lines.append("Tables that each fit the whole party (choose one):")
        elif result_type == "split":
            lines.append(f"Minimum tables needed: {min_tables_needed(chosen, capacity)}")
            lines.append("Free tables to choose from:")
        else:
            lines.append("Available tables:")

        for t in chosen:
            lines.append(f"Table Number: {t.table_number}, Capacity: {t.capacity}")

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