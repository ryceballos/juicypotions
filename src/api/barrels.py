from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db
import random

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

    for barrel in barrels_delivered:
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text("UPDATE global_inventory SET gold = global_inventory.gold - :gold_spent"),
                               [{"gold_spent": barrel.quantity * barrel.price}])
            connection.execute(sqlalchemy.text(
                "UPDATE global_inventory SET num_red_ml = global_inventory.num_red_ml + :red, num_green_ml = global_inventory.num_green_ml + :green, num_blue_ml = global_inventory.num_blue_ml + :blue"),
                               [{"red": barrel.potion_type[0] * (barrel.quantity * barrel.ml_per_barrel), "green": barrel.potion_type[1] * (barrel.quantity * barrel.ml_per_barrel), "blue": barrel.potion_type[2] * (barrel.quantity * barrel.ml_per_barrel)}])

    print(f"barrels delievered: {barrels_delivered} order_id: {order_id}")
    return "OK"

# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    purchase_plan = []
    red_potions_num = 0
    green_potions_num = 0
    blue_potions_num = 0
    with db.engine.begin() as connection:
        potions = connection.execute(sqlalchemy.text(
            "SELECT red, green, blue, quantity FROM potions"))
        for red, green, blue, quantity in potions:
            if (red > 0):
                red_potions_num += quantity
            if (green > 0):
                green_potions_num += quantity
            if (blue > 0):
                blue_potions_num += quantity
        curr_gold = connection.execute(sqlalchemy.text(
            "SELECT gold FROM global_inventory")).scalar()
        curr_green_ml = connection.execute(sqlalchemy.text(
            "SELECT num_green_ml FROM global_inventory")).scalar()
        curr_red_ml = connection.execute(sqlalchemy.text(
            "SELECT num_red_ml FROM global_inventory")).scalar()
        curr_blue_ml = connection.execute(sqlalchemy.text(
            "SELECT num_blue_ml FROM global_inventory")).scalar()

    # Logic for Buying Barrels
    if ((red_potions_num < 10) and (curr_red_ml < 1000)):
        purchase_red_barrel = 1
        selection_1 = 1
    else:
        purchase_red_barrel = 0
    if ((green_potions_num < 10) and (curr_green_ml < 1000)):
        purchase_green_barrel = 5
        selection_1 = 2
    else:
        purchase_green_barrel = 0
    if ((blue_potions_num < 10) and (curr_blue_ml < 1000)):
        purchase_blue_barrel = 10
        selection_1 = 3
    else:
        purchase_blue_barrel = 0
    selection_2 = selection_1
    # Randomly selects two potion types for which to buy (could also be one type)
    # 1 = R, 2 = G, 3 = B
    if (purchase_red_barrel + purchase_green_barrel + purchase_blue_barrel) == 16:
        selection_1 = random.randint(1, 3)
        selection_2 = random.randint(1, 3)
    elif (purchase_red_barrel + purchase_green_barrel + purchase_blue_barrel) == 6:
        selection_1 = random.choice([1, 2])
        selection_2 = selection_1
    elif (purchase_red_barrel + purchase_green_barrel + purchase_blue_barrel) == 11:
        selection_1 = random.choice([1, 3])
        selection_2 = selection_1
    elif (purchase_red_barrel + purchase_green_barrel + purchase_blue_barrel) == 15:
        selection_1 = random.choice([2, 3])
        selection_2 = selection_1

    # Choosing Barrels to Purchase from Catalog
    for barrel in wholesale_catalog:
        if barrel.potion_type == [1, 0, 0, 0] and ((selection_1 == 1) or (selection_2 == 1)):
            if curr_gold >= barrel.price:
                if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
                    curr_gold -= (barrel.price * 2)
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 2,
                    })
                elif barrel.quantity >= 1:
                    curr_gold -= barrel.price
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
        if barrel.potion_type == [0, 1, 0, 0] and ((selection_1 == 2) or (selection_2 == 2)):
            if curr_gold >= barrel.price:
                if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
                    curr_gold -= (barrel.price * 2)
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 2,
                    })
                elif barrel.quantity >= 1:
                    curr_gold -= barrel.price
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })
        if barrel.potion_type == [0, 0, 1, 0] and ((selection_1 == 3) or (selection_2 == 3)):
            if curr_gold >= barrel.price:
                if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
                    curr_gold -= (barrel.price * 2)
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 2,
                    })
                elif barrel.quantity >= 1:
                    curr_gold -= barrel.price
                    purchase_plan.append({
                        "sku": barrel.sku,
                        "quantity": 1,
                    })

    return purchase_plan

# @router.post("/plan")
# def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
#     """ """
#     print(wholesale_catalog)
#     purchase_plan = []
#     with db.engine.begin() as connection:
#         green_potions_num = connection.execute(sqlalchemy.text(
#             "SELECT num_green_potions FROM global_inventory")).scalar()
#         red_potions_num = connection.execute(sqlalchemy.text(
#             "SELECT num_red_potions FROM global_inventory")).scalar()
#         blue_potions_num = connection.execute(sqlalchemy.text(
#             "SELECT num_blue_potions FROM global_inventory")).scalar()
#         curr_gold = connection.execute(sqlalchemy.text(
#             "SELECT gold FROM global_inventory")).scalar()
#         curr_green_ml = connection.execute(sqlalchemy.text(
#             "SELECT num_green_ml FROM global_inventory")).scalar()
#         curr_red_ml = connection.execute(sqlalchemy.text(
#             "SELECT num_red_ml FROM global_inventory")).scalar()
#         curr_blue_ml = connection.execute(sqlalchemy.text(
#             "SELECT num_blue_ml FROM global_inventory")).scalar()
#     # Randomly selects two potion types for which to buy (could also be one type)
#     # 1 = R, 2 = G, 3 = B
#     selection_1 = random.randint(1, 3)
#     selection_2 = random.randint(1, 3)

#     # Logic for Buying Barrels
#     if ((selection_1 == 2) or (selection_2 == 2)) and ((green_potions_num < 10) and (curr_green_ml < 1000)):
#         purchase_green_barrel = 1
#     else:
#         purchase_green_barrel = 0
#     if ((selection_1 == 1) or (selection_2 == 1)) and ((red_potions_num < 7) and (curr_red_ml < 1000)):
#         purchase_red_barrel = 1
#     else:
#         purchase_red_barrel = 0
#     if ((selection_1 == 3) or (selection_2 == 3)) and ((blue_potions_num < 7) and (curr_blue_ml < 1000)):
#         purchase_blue_barrel = 1
#     else:
#         purchase_blue_barrel = 0

#     # Choosing Barrels to Purchase from Catalog
#     for barrel in wholesale_catalog:
#         if barrel.potion_type == [1, 0, 0, 0] and purchase_red_barrel == 1:
#             if curr_gold >= barrel.price:
#                 if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
#                     curr_gold -= (barrel.price * 2)
#                     purchase_plan.append({
#                         "sku": barrel.sku,
#                         "quantity": 2,
#                     })
#                 elif barrel.quantity >= 1:
#                     curr_gold -= barrel.price
#                     purchase_plan.append({
#                         "sku": barrel.sku,
#                         "quantity": 1,
#                     })
#         if barrel.potion_type == [0, 1, 0, 0] and purchase_green_barrel == 1:
#             if curr_gold >= barrel.price:
#                 if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
#                     curr_gold -= (barrel.price * 2)
#                     purchase_plan.append({
#                         "sku": barrel.sku,
#                         "quantity": 2,
#                     })
#                 elif barrel.quantity >= 1:
#                     curr_gold -= barrel.price
#                     purchase_plan.append({
#                         "sku": barrel.sku,
#                         "quantity": 1,
#                     })
#         if barrel.potion_type == [0, 0, 1, 0] and purchase_blue_barrel == 1:
#             if curr_gold >= barrel.price:
#                 if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
#                     curr_gold -= (barrel.price * 2)
#                     purchase_plan.append({
#                         "sku": barrel.sku,
#                         "quantity": 2,
#                     })
#                 elif barrel.quantity >= 1:
#                     curr_gold -= barrel.price
#                     purchase_plan.append({
#                         "sku": barrel.sku,
#                         "quantity": 1,
#                     })

#     return purchase_plan
