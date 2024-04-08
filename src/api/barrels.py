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
    """ """
    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")

    return "OK"


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)

    with db.engine.begin() as connection:
        #Mix availible green ml
        green_ml_quantity = connection.execute(sqlalchemy.text(
            "SELECT num_green_ml FROM global_inventory")).scalar()
        
        if green_ml_quantity is not None and green_ml_quantity > 0:
            connection.execute(sqlalchemy.text(
                "UPDATE global_inventory SET num_green_ml = 0"))


        green_potions_num = connection.execute(sqlalchemy.text(
            "SELECT num_green_potions FROM global_inventory")).scalar()

        #If the inventory from db table is less than 10, plan to purchase 1
        if green_potions_num is not None and green_potions_num < 10:
            return [
                {
                    "sku": "SMALL_GREEN_BARREL",
                    "quantity": 1,
                }
            ]
    return "No Purchase"

