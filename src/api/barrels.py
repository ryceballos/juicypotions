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
            connection.execute(sqlalchemy.text(
                "INSERT INTO ledger (sku, quantity) VALUES (:gold, :gold_spent), (:red_ml, :red_quantity), (:green_ml, :green_quantity), (:blue_ml, :blue_quantity), (:dark_ml, :dark_quantity)"),
                        [{"gold": 'gold', "gold_spent": -1 * barrel.quantity * barrel.price, "red_ml": 'RED_ML', "red_quantity": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[0], "green_ml": 'GREEN_ML', "green_quantity": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[1], "blue_ml": 'BLUE_ML', "blue_quantity": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[2], "dark_ml": 'DARK_ML', "dark_quantity": barrel.quantity * barrel.ml_per_barrel * barrel.potion_type[3]}])
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
        potions = connection.execute(sqlalchemy.text("""
                                                     SELECT potions.red, potions.green, potions.blue, COALESCE(SUM(ledger.quantity), 0) AS total
                                                     FROM potions
                                                     LEFT JOIN ledger ON potions.sku = ledger.sku
                                                     WHERE potions.sku LIKE '%POTION'
                                                     GROUP BY potions.sku"""))
        for red, green, blue, quantity in potions:
            if (red > 0):
                red_potions_num += quantity
            if (green > 0):
                green_potions_num += quantity
            if (blue > 0):
                blue_potions_num += quantity
        curr_gold = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'gold' ")).scalar()
        curr_green_ml = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'GREEN_ML' ")).scalar()
        curr_red_ml = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'RED_ML' ")).scalar()
        curr_blue_ml = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'BLUE_ML' ")).scalar()
        # curr_dark_ml = connection.execute(sqlalchemy.text(
        #     "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'DARK_ML' ")).scalar()

    # Logic for Buying Barrels
    selection_1 = 0
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