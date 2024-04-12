from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

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
    gold_spent = 0
    with db.engine.begin() as connection:
        curr_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        curr_gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
        for barrel in barrels_delivered:
            new_green_ml += (barrel.quantity * barrel.ml_per_barrel)
            gold_spent += (barrel.quantity * barrel.price)
        curr_green_ml += new_green_ml
        curr_gold -= gold_spent
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(
                f"UPDATE global_inventory SET gold = {curr_gold}, num_green_ml = {curr_green_ml}"))
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    green_barrel_purchase = 0
    sku = ''
    with db.engine.begin() as connection:
        green_potions_num = connection.execute(sqlalchemy.text(
            "SELECT num_green_potions FROM global_inventory")).scalar()

        #If the inventory from db table is less than 10, plan to purchase 1
        if green_potions_num < 10:
            green_barrel_purchase = 1
        else:
            return []
    for barrel in wholesale_catalog:
        if barrel.potion_type == [0, 100, 0, 0]:
            sku = barrel.sku
        else:
            return[]
    return [
        {
            "sku": sku,
            "quantity": green_barrel_purchase,
        }
    ]

