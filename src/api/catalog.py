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

# @router.get("/catalog/", tags=["catalog"])
# def get_catalog():
#     """
#     Each unique item combination must have only a single price.
#     """
#     catalog = []
#     with db.engine.begin() as connection:
#         green_quantity = connection.execute(sqlalchemy.text(
#             "SELECT num_green_potions FROM global_inventory")).scalar()
#         red_quantity = connection.execute(sqlalchemy.text(
#             "SELECT num_red_potions FROM global_inventory")).scalar()
#         blue_quantity = connection.execute(sqlalchemy.text(
#             "SELECT num_blue_potions FROM global_inventory")).scalar()

#     if red_quantity >= 1:
#         catalog.append({
#             "sku": "Red_Potion",
#             "name": "Red potion",
#             "quantity": red_quantity,
#             "price": 50,
#             "potion_type": [100, 0, 0, 0],
#         })
#     if green_quantity >= 1:
#         catalog.append({
#             "sku": "Green_Potion",
#             "name": "Green potion",
#             "quantity": green_quantity,
#             "price": 50,
#             "potion_type": [0, 100, 0, 0],
#         })
#     if blue_quantity >= 1:
#         catalog.append({
#             "sku": "Blue_Potion",
#             "name": "Blue potion",
#             "quantity": blue_quantity,
#             "price": 50,
#             "potion_type": [0, 0, 100, 0],
#         })

#     return catalog
