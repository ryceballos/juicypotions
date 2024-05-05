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
        connection.execute(sqlalchemy.text(
            "INSERT INTO ledger (sku, quantity) VALUES (:gold, :gold_initial), (:red_ml, :red_quantity), (:green_ml, :green_quantity), (:blue_ml, :blue_quantity), (:dark_ml, :dark_quantity)"),
                    [{"gold": 'gold', "gold_initial": 100, "red_ml": 'RED_ML', "red_quantity": 0, "green_ml": 'GREEN_ML', "green_quantity": 0, "blue_ml": 'BLUE_ML', "blue_quantity": 0, "dark_ml": 'DARK_ML', "dark_quantity": 0}])
    return "OK"

