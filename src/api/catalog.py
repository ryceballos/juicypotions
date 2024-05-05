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
        potions = connection.execute(sqlalchemy.text("""
                                                     SELECT potions.sku, potions.name, potions.red, potions.green, potions.blue, potions.dark, potions.price, COALESCE(SUM(ledger.quantity), 0) AS total
                                                     FROM potions
                                                     LEFT JOIN ledger ON potions.sku = ledger.sku
                                                     WHERE potions.sku LIKE '%POTION'
                                                     GROUP BY potions.sku
                                                     ORDER BY total DESC LIMIT 6"""))
        for sku, name, red, green, blue, dark, price, total in potions:
            if (total != 0):
                catalog.append({
                    "sku": sku,
                    "name": name,
                    "quantity": total,
                    "price": price,
                    "potion_type": [red, green, blue, dark],
                })

    return catalog