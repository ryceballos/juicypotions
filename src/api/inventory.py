from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import math
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/inventory",
    tags=["inventory"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/audit")
def get_inventory():
    """ """
    with db.engine.begin() as connection:
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku LIKE '%POTION'")).scalar()
        total_ml = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku LIKE '%ML'")).scalar()
        curr_gold = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'gold' ")).scalar()
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": curr_gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    cap_plan = []
    cap_potion = 0
    cap_ml = 0
    with db.engine.begin() as connection:
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku LIKE '%POTION'")).scalar()
        total_ml = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku LIKE '%ML'")).scalar()
        curr_gold = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'gold' ")).scalar()
        caps = connection.execute(sqlalchemy.text(
            "SELECT ml_cap, potion_cap FROM capacities")).one()
        ml_cap = caps.ml_cap
        potion_cap = caps.potion_cap
        if (total_ml >= ml_cap * 0.75) and (curr_gold - 1000 >= 0):
            cap_ml = 1
            curr_gold -= 1000
        if (total_potions >= potion_cap * 0.80) and (curr_gold - 1000 >= 0):
            cap_potion = 1

    return {
        "potion_capacity": cap_potion,
        "ml_capacity": cap_ml
        }

class CapacityPurchase(BaseModel):
    potion_capacity: int
    ml_capacity: int

# Gets called once a day
@router.post("/deliver/{order_id}")
def deliver_capacity_plan(capacity_purchase : CapacityPurchase, order_id: int):
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "UPDATE capacities SET potion_cap = capacities.potion_cap + :cap_potion, ml_cap = capacities.ml_cap + :cap_ml"),
                           [{"cap_potion": capacity_purchase.potion_capacity * 50, "cap_ml": capacity_purchase.ml_capacity * 10000}])
        connection.execute(sqlalchemy.text(
            "INSERT INTO ledger (sku, quantity) VALUES (:gold, :gold_spent)"),
                [{"gold": 'gold', "gold_spent": (-1 * capacity_purchase.potion_capacity * 1000) + (capacity_purchase.ml_capacity * 1000 * -1)}])
    return "OK"