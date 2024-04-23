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
    total_potions = 0
    total_ml = 0
    with db.engine.begin() as connection:
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT SUM(quantity) FROM potions")).scalar()
        total_ml = connection.execute(sqlalchemy.text(
            "SELECT SUM(num_green_ml + num_red_ml + num_blue_ml) FROM global_inventory")).scalar()
        curr_gold = connection.execute(sqlalchemy.text(
            "SELECT gold FROM global_inventory")).scalar()
    return {"number_of_potions": total_potions, "ml_in_barrels": total_ml, "gold": curr_gold}

# Gets called once a day
@router.post("/plan")
def get_capacity_plan():
    """ 
    Start with 1 capacity for 50 potions and 1 capacity for 10000 ml of potion. Each additional 
    capacity unit costs 1000 gold.
    """

    return {
        "potion_capacity": 0,
        "ml_capacity": 0
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

    return "OK"