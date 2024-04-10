from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")

    new_potions = 0
    green_ml_used = 0
    for Potion in potions_delivered:
        if (Potion.potion_type == [0, 100, 0, 0]):
            new_potions += Potion.quantity
            green_ml_used += (Potion.quantity * 100)
    with db.engine.begin() as connection:
        curr_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        curr_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        curr_green_ml -= green_ml_used
        curr_green_potions += new_potions
        connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET num_green_ml = {curr_green_ml}, num_green_potions = {curr_green_potions}"))
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    ml_to_bottle = 0
    with db.engine.begin() as connection:
        curr_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        while curr_green_ml >= 100:
            ml_to_bottle += 1
            curr_green_ml -= 100
    if ml_to_bottle == 0:
        return[]
    return [
            {
                "potion_type": [0, 100, 0, 0],
                "quantity": ml_to_bottle,
            }
        ]

if __name__ == "__main__":
    print(get_bottle_plan())