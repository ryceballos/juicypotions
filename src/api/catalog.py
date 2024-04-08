from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """

    with db.engine.begin() as connection:
        green_quantity = connection.execute(sqlalchemy.text(
            "SELECT num_green_potions FROM global_inventory")).scalar()

        if green_quantity is None:
            green_quantity = 0

        return [
                {
                    "sku": "Green_POTION_0",
                    "name": "Green potion",
                    "quantity": green_quantity,
                    "price": 50,
                    "potion_type": [0, 0, 100, 0],
                }
            ]
