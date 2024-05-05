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
    
    barrel_plan = []
    purchase_plan = []
    with db.engine.begin() as connection:
        ml = connection.execute(sqlalchemy.text(
            "SELECT sku, COALESCE(SUM(quantity), 0) AS total FROM ledger WHERE sku LIKE '%ML' GROUP BY sku"))
        curr_gold = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'gold' ")).scalar()
        for sku, total in ml:
            if 'red' in sku.lower():
                curr_red_ml = total
            elif 'green' in sku.lower():
                curr_green_ml = total
            elif 'blue' in sku.lower():
                curr_blue_ml = total
            elif 'dark' in sku.lower():
                curr_dark_ml = total
        total_ml = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku LIKE '%ML' ")).scalar()
        caps = connection.execute(sqlalchemy.text(
            "SELECT ml_cap FROM capacities")).one()
        ml_cap = caps.ml_cap
        counter = 0
        while((total_ml < ml_cap) and (counter < ml_cap)):
            for barrel in wholesale_catalog:
                if ((barrel.ml_per_barrel + total_ml) < ml_cap):
                    mls = connection.execute(sqlalchemy.text("""
                                                                SELECT potions.red, potions.green, potions.blue, potions.dark, potions.limit
                                                                FROM potions
                                                                LEFT JOIN (
                                                                    SELECT sku, COALESCE(SUM(quantity), 0) AS total_quantity
                                                                    FROM ledger
                                                                    GROUP BY sku
                                                                ) AS ledger_quantity ON potions.sku = ledger_quantity.sku
                                                                WHERE potions.red = :red AND potions.green = :green AND potions.blue = :blue AND potions.dark = :dark AND ledger_quantity.total_quantity < (potions.limit * :ml_cap)
                                                                GROUP BY potions.sku"""),
                                                [{"ml_cap": ml_cap, "red": barrel.potion_type[0], "green": barrel.potion_type[1], "blue": barrel.potion_type[2], "dark": barrel.potion_type[3]}])
                    for red, green, blue, dark, limit in mls:
                        if (curr_gold >= barrel.price) and ((curr_red_ml < (red * limit * ml_cap)) or (curr_green_ml < (green * limit * ml_cap)) or (curr_blue_ml < (blue * limit * ml_cap)) or (curr_dark_ml < (dark * limit * ml_cap))):
                            barrel_plan.append({
                                "potion_type": [red, green, blue, dark],
                                "quantity": 1,
                            })
                            curr_red_ml += barrel.potion_type[0] * barrel.ml_per_barrel
                            curr_green_ml += barrel.potion_type[1] * barrel.ml_per_barrel
                            curr_blue_ml += barrel.potion_type[2] * barrel.ml_per_barrel
                            curr_dark_ml += barrel.potion_type[3] * barrel.ml_per_barrel
                            curr_gold -= barrel.price
                            total_ml += barrel.ml_per_barrel
                        else:
                            counter += 200
                else:
                    counter += 200
        potion_type_counts = {}
        for entry in barrel_plan:
            potion_type = tuple(entry["potion_type"])
            quantity = entry["quantity"]
            if potion_type in potion_type_counts:
                potion_type_counts[potion_type] += quantity
            else:
                potion_type_counts[potion_type] = quantity
        for potion_type, count in potion_type_counts.items():
            barrel_type = list(potion_type)
            for barrel in wholesale_catalog:
                if (barrel_type == barrel.potion_type) and (count > barrel.quantity):
                    count = barrel.quantity
            purchase_plan.append({
                "potion_type": list(potion_type),
                "quantity": count
            })
        print("Purchase Plan:")
        for step in purchase_plan:
            print(step)
    return purchase_plan

    # purchase_plan = []
    # red_potions_num = 0
    # green_potions_num = 0
    # blue_potions_num = 0
    # dark_potions_num = 0
    # with db.engine.begin() as connection:
    #     potions = connection.execute(sqlalchemy.text("""
    #                                                  SELECT potions.red, potions.green, potions.blue, potions.dark, COALESCE(SUM(ledger.quantity), 0) AS total
    #                                                  FROM potions
    #                                                  LEFT JOIN ledger ON potions.sku = ledger.sku
    #                                                  WHERE potions.sku LIKE '%POTION'
    #                                                  GROUP BY potions.sku"""))
    #     for red, green, blue, dark, quantity in potions:
    #         if (red > 0):
    #             red_potions_num += quantity
    #         if (green > 0):
    #             green_potions_num += quantity
    #         if (blue > 0):
    #             blue_potions_num += quantity
    #         if (dark > 0):
    #             dark_potions_num += quantity
    #     curr_gold = connection.execute(sqlalchemy.text(
    #         "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'gold' ")).scalar()
    #     curr_green_ml = connection.execute(sqlalchemy.text(
    #         "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'GREEN_ML' ")).scalar()
    #     curr_red_ml = connection.execute(sqlalchemy.text(
    #         "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'RED_ML' ")).scalar()
    #     curr_blue_ml = connection.execute(sqlalchemy.text(
    #         "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'BLUE_ML' ")).scalar()
    #     curr_dark_ml = connection.execute(sqlalchemy.text(
    #         "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku = 'DARK_ML' ")).scalar()
    #     total_ml = connection.execute(sqlalchemy.text(
    #         "SELECT SUM(quantity) FROM ledger WHERE sku LIKE '%ML'")).scalar()
    #     caps = connection.execute(sqlalchemy.text(
    #         "SELECT ml_cap, barrel_limit FROM capacities")).one()
    #     ml_cap = caps.ml_cap
    #     barrel_limit = caps.barrel_limit

    # # Logic for Buying Barrels
    # selection_1 = 0
    # if ((red_potions_num < 10) and (curr_red_ml < barrel_limit)):
    #     purchase_red_barrel = 1
    #     selection_1 = 1
    # else:
    #     purchase_red_barrel = 0
    # if ((green_potions_num < 10) and (curr_green_ml < barrel_limit)):
    #     purchase_green_barrel = 5
    #     selection_1 = 2
    # else:
    #     purchase_green_barrel = 0
    # if ((blue_potions_num < 10) and (curr_blue_ml < barrel_limit)):
    #     purchase_blue_barrel = 10
    #     selection_1 = 3
    # else:
    #     purchase_blue_barrel = 0

    # selection_2 = selection_1
    # # Randomly selects two potion types for which to buy (could also be one type)
    # # 1 = R, 2 = G, 3 = B
    # if (purchase_red_barrel + purchase_green_barrel + purchase_blue_barrel) == 16:
    #     selection_1 = random.randint(1, 3)
    #     selection_2 = random.randint(1, 3)
    # elif (purchase_red_barrel + purchase_green_barrel + purchase_blue_barrel) == 6:
    #     selection_1 = random.choice([1, 2])
    #     selection_2 = selection_1
    # elif (purchase_red_barrel + purchase_green_barrel + purchase_blue_barrel) == 11:
    #     selection_1 = random.choice([1, 3])
    #     selection_2 = selection_1
    # elif (purchase_red_barrel + purchase_green_barrel + purchase_blue_barrel) == 15:
    #     selection_1 = random.choice([2, 3])
    #     selection_2 = selection_1

    # # Choosing Barrels to Purchase from Catalog
    # for barrel in wholesale_catalog:
    #     if barrel.potion_type == [1, 0, 0, 0] and ((selection_1 == 1) or (selection_2 == 1)):
    #         if curr_gold >= barrel.price:
    #             if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
    #                 curr_gold -= (barrel.price * 2)
    #                 purchase_plan.append({
    #                     "sku": barrel.sku,
    #                     "quantity": 2,
    #                 })
    #             elif barrel.quantity >= 1:
    #                 curr_gold -= barrel.price
    #                 purchase_plan.append({
    #                     "sku": barrel.sku,
    #                     "quantity": 1,
    #                 })
    #     if barrel.potion_type == [0, 1, 0, 0] and ((selection_1 == 2) or (selection_2 == 2)):
    #         if curr_gold >= barrel.price:
    #             if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
    #                 curr_gold -= (barrel.price * 2)
    #                 purchase_plan.append({
    #                     "sku": barrel.sku,
    #                     "quantity": 2,
    #                 })
    #             elif barrel.quantity >= 1:
    #                 curr_gold -= barrel.price
    #                 purchase_plan.append({
    #                     "sku": barrel.sku,
    #                     "quantity": 1,
    #                 })
    #     if barrel.potion_type == [0, 0, 1, 0] and ((selection_1 == 3) or (selection_2 == 3)):
    #         if curr_gold >= barrel.price:
    #             if (selection_1 == selection_2) and (curr_gold >= (barrel.price * 2)) and (barrel.quantity >= 2):
    #                 curr_gold -= (barrel.price * 2)
    #                 purchase_plan.append({
    #                     "sku": barrel.sku,
    #                     "quantity": 2,
    #                 })
    #             elif barrel.quantity >= 1:
    #                 curr_gold -= barrel.price
    #                 purchase_plan.append({
    #                     "sku": barrel.sku,
    #                     "quantity": 1,
    #                 })

    # return purchase_plan