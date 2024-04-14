from fastapi import APIRouter
import sqlalchemy
from src import database as db

router = APIRouter()

@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    catalog = []
    with db.engine.begin() as connection:
        green_quantity = connection.execute(sqlalchemy.text(
            "SELECT num_green_potions FROM global_inventory")).scalar()

        if green_quantity == 0:
            return catalog
        else:
            green_quantity = 1

        catalog.append({
            "sku": "Green_POTION_0",
            "name": "Green potion",
            "quantity": green_quantity,
            "price": 50,
            "potion_type": [0, 100, 0, 0],
        })
    return catalog
