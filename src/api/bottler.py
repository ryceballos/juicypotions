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
    for Potion in potions_delivered:
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                "UPDATE potions SET quantity = potions.quantity + :quantity WHERE potions.red = :red AND potions.green = :green AND potions.blue = :blue"),
                               [{"quantity": Potion.quantity, "red": Potion.potion_type[0], "green": Potion.potion_type[1], "blue": Potion.potion_type[2]}])
            connection.execute(sqlalchemy.text(
                "UPDATE global_inventory SET num_red_ml = global_inventory.num_red_ml - :red, num_green_ml = global_inventory.num_green_ml - :green, num_blue_ml = global_inventory.num_blue_ml - :blue"),
                               [{"red": (Potion.quantity * Potion.potion_type[0]), "green": (Potion.quantity * Potion.potion_type[1]), "blue": (Potion.quantity * Potion.potion_type[2])}])
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

    
    bottle_plan = []
    with db.engine.begin() as connection:
        ml = connection.execute(sqlalchemy.text(
            "SELECT num_red_ml AS red_ml, num_green_ml AS green_ml, num_blue_ml AS blue_ml FROM global_inventory")).one()
        curr_red_ml = ml.red_ml
        curr_green_ml = ml.green_ml
        curr_blue_ml = ml.blue_ml
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT SUM(quantity) FROM potions")).scalar()
        while(total_potions < (50 - 1)):
            potions = connection.execute(sqlalchemy.text(
                "SELECT red, green, blue FROM potions WHERE quantity < 8"))
            for red, green, blue in potions:
                if (curr_red_ml >= red) and (curr_green_ml >= green) and (curr_blue_ml >= blue):
                    bottle_plan.append({
                        "potion_type": [red, green, blue, 0],
                        "quantity": 1,
                    })
                    curr_red_ml -= red
                    curr_green_ml -= green
                    curr_blue_ml -= blue
                    total_potions += 1

    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())