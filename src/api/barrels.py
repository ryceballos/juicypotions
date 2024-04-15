from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_barrels(barrels_delivered: list[Barrel], order_id: int):
    """Gold and ML"""
    new_green_ml = 0
    new_red_ml = 0
    new_blue_ml = 0
    gold_spent = 0
    with db.engine.begin() as connection:
        curr_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        curr_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        curr_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
        curr_gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()

    for barrel in barrels_delivered:
        gold_spent += (barrel.quantity * barrel.price)
        if barrel.potion_type == [1, 0, 0, 0]:
            new_red_ml += (barrel.quantity * barrel.ml_per_barrel)
        elif barrel.potion_type == [0, 1, 0, 0]:
            new_green_ml += (barrel.quantity * barrel.ml_per_barrel)
        elif barrel.potion_type == [0, 0, 1, 0]:
            new_blue_ml += (barrel.quantity * barrel.ml_per_barrel)

    curr_green_ml += new_green_ml
    curr_red_ml += new_red_ml
    curr_blue_ml += new_blue_ml
    curr_gold -= gold_spent
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            f"UPDATE global_inventory SET gold = {curr_gold}, num_green_ml = {curr_green_ml}"))
        connection.execute(sqlalchemy.text(
            f"UPDATE global_inventory SET num_red_ml = {curr_red_ml}, num_blue_ml = {curr_blue_ml}"))

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    purchase_plan = []
    with db.engine.begin() as connection:
        green_potions_num = connection.execute(sqlalchemy.text(
            "SELECT num_green_potions FROM global_inventory")).scalar()
        red_potions_num = connection.execute(sqlalchemy.text(
            "SELECT num_red_potions FROM global_inventory")).scalar()
        blue_potions_num = connection.execute(sqlalchemy.text(
            "SELECT num_blue_potions FROM global_inventory")).scalar()
        curr_gold = connection.execute(sqlalchemy.text(
            "SELECT gold FROM global_inventory")).scalar()
    # Randomly selects two potion types for which to buy (could also be one type)
    # 1 = R, 2 = G, 3 = B
    selection_1 = random.randint(1, 3)
    selection_2 = random.randint(1, 3)

    # Logic for Buying Barrels
    if ((selection_1 == 2) or (selection_2 == 2)) and (green_potions_num < 10):
        purchase_green_barrel = 1
    else:
        purchase_green_barrel = 0
    if ((selection_1 == 1) or (selection_2 == 1)) and (red_potions_num < 7):
        purchase_red_barrel = 1
    else:
        purchase_red_barrel = 0
    if ((selection_1 == 3) or (selection_2 == 3)) and (blue_potions_num < 7):
        purchase_blue_barrel = 1
    else:
        purchase_blue_barrel = 0

    # Choosing Barrels to Purchase from Catalog
    for barrel in wholesale_catalog:
        if barrel.potion_type == [1, 0, 0, 0] and purchase_red_barrel == 1:
            if curr_gold >= barrel.price:
                if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
                    curr_gold -= (barrel.price * 2)
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 2,
                    })
                elif barrel.quantity >= 1:
                    curr_gold -= barrel.price
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
        if barrel.potion_type == [0, 1, 0, 0] and purchase_green_barrel == 1:
            if curr_gold >= barrel.price:
                if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
                    curr_gold -= (barrel.price * 2)
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 2,
                    })
                elif barrel.quantity >= 1:
                    curr_gold -= barrel.price
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
        if barrel.potion_type == [0, 0, 1, 0] and purchase_blue_barrel == 1:
            if curr_gold >= barrel.price:
                if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
                    curr_gold -= (barrel.price * 2)
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 2,
                    })
                elif barrel.quantity >= 1:
                    curr_gold -= barrel.price
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })

    return purchase_plan

