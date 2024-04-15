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
        curr_green_ml = connection.execute(sqlalchemy.text("SELECT num_green_ml FROM global_inventory")).scalar()
        curr_green_potions = connection.execute(sqlalchemy.text("SELECT num_green_potions FROM global_inventory")).scalar()
        curr_red_ml = connection.execute(sqlalchemy.text("SELECT num_red_ml FROM global_inventory")).scalar()
        curr_red_potions = connection.execute(sqlalchemy.text("SELECT num_red_potions FROM global_inventory")).scalar()
        curr_blue_ml = connection.execute(sqlalchemy.text("SELECT num_blue_ml FROM global_inventory")).scalar()
        curr_blue_potions = connection.execute(sqlalchemy.text("SELECT num_blue_potions FROM global_inventory")).scalar()
        curr_gold = connection.execute(sqlalchemy.text("SELECT gold FROM global_inventory")).scalar()
    total_potions = curr_green_potions + curr_red_potions + curr_blue_potions
    total_ml = curr_green_ml + curr_red_ml + curr_blue_ml
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
