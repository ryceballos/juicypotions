from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset():
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "TRUNCATE ledger"))
        connection.execute(sqlalchemy.text("""
                                            INSERT INTO ledger (sku, quantity)
                                            VALUES ('gold', 100), ('RED_ML', 0), ('GREEN_ML', 0), ('BLUE_ML', 0),
                                                ('DARK_ML', 0), ('RED_POTION', 0), ('GREEN_POTION', 0),
                                                ('BLUE_POTION', 0), ('DARK_POTION', 0), ('YELLOW_POTION', 0),
                                                ('PURPLE_POTION', 0), ('CYAN_POTION', 0), ('BLACKOUT_POTION', 0)"""))
    return "OK"

