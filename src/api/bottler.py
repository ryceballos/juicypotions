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

    new_green_potions = 0
    new_red_potions = 0
    new_blue_potions = 0
    green_ml_used = 0
    red_ml_used = 0
    blue_ml_used = 0
    for Potion in potions_delivered:
        if (Potion.potion_type == [100, 0, 0, 0]):
            new_red_potions += Potion.quantity
            red_ml_used += (Potion.quantity * 100) 
        elif (Potion.potion_type == [0, 100, 0, 0]):
            new_green_potions += Potion.quantity
            green_ml_used += (Potion.quantity * 100)
        elif (Potion.potion_type == [0, 0, 100, 0]):
            new_blue_potions += Potion.quantity
            blue_ml_used += (Potion.quantity * 100)

    with db.engine.begin() as connection:
        curr_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        curr_green_potions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Green Potion'")).scalar()
        curr_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        curr_red_potions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Red Potion'")).scalar()
        curr_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
        curr_blue_potions = connection.execute(sqlalchemy.text("SELECT quantity FROM potions WHERE name = 'Blue Potion'")).scalar()
        curr_green_ml -= green_ml_used
        curr_green_potions += new_green_potions
        curr_red_ml -= red_ml_used
        curr_red_potions += new_red_potions
        curr_blue_ml -= blue_ml_used
        curr_blue_potions += new_blue_potions
        connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET num_green_ml = {curr_green_ml}, num_red_ml = {curr_red_ml}, num_blue_ml = {curr_blue_ml}"))
        connection.execute(sqlalchemy.text(
                f"UPDATE potions SET quantity = {curr_red_potions} WHERE name = 'Red Potion'"))
        connection.execute(sqlalchemy.text(
                f"UPDATE potions SET quantity = {curr_green_potions} WHERE name = 'Green Potion'"))
        connection.execute(sqlalchemy.text(
                f"UPDATE potions SET quantity = {curr_blue_potions} WHERE name = 'Blue Potion'"))
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

    num_green_bottles = 0
    num_red_bottles = 0
    num_blue_bottles = 0
    bottle_plan = []
    with db.engine.begin() as connection:
        curr_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        curr_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        curr_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
    
    if curr_red_ml >= 100:
        while curr_red_ml >= 100:
            num_red_bottles += 1
            curr_red_ml -= 100
        bottle_plan.append({
            "potion_type": [100, 0, 0, 0],
            "quantity": num_red_bottles,
        })
    if curr_green_ml >= 100:
        while curr_green_ml >= 100:
            num_green_bottles += 1
            curr_green_ml -= 100
        bottle_plan.append({
            "potion_type": [0, 100, 0, 0],
            "quantity": num_green_bottles,
        })
    if curr_blue_ml >= 100:
        while curr_blue_ml >= 100:
            num_blue_bottles += 1
            curr_blue_ml -= 100
        bottle_plan.append({
            "potion_type": [0, 0, 100, 0],
            "quantity": num_blue_bottles,
        })

    return bottle_plan

if __name__ == "__main__":
    print(get_bottle_plan())