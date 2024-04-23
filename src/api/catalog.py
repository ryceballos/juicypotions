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
        potions = connection.execute(sqlalchemy.text("SELECT * FROM potions"))
        for SKU, name, red, green, blue, dark, quantity, price in potions:
            if (quantity != 0):
                catalog.append({
                    "sku": SKU,
                    "name": name,
                    "quantity": quantity,
                    "price": price,
                    "potion_type": [red, green, blue, dark],
                })

    return catalog