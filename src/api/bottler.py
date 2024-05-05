from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver/{order_id}")
def post_deliver_bottles(potions_delivered: list[PotionInventory], order_id: int):
    """ """
    print(f"potions delievered: {potions_delivered} order_id: {order_id}")
    with db.engine.begin() as connection:
        for Potion in potions_delivered:
            item = connection.execute(sqlalchemy.text(
                "SELECT sku FROM potions WHERE potions.red = :red AND potions.green = :green AND potions.blue = :blue AND potions.dark = :dark"),
                               [{"red": Potion.potion_type[0], "green": Potion.potion_type[1], "blue": Potion.potion_type[2], "dark": Potion.potion_type[3]}]).scalar()
            connection.execute(sqlalchemy.text(
                "INSERT INTO ledger (sku, quantity) VALUES (:item, :quantity)"),
                               [{"item": item, "quantity": Potion.quantity}])
            connection.execute(sqlalchemy.text(
                "INSERT INTO ledger (sku, quantity) VALUES (:red_ml, :red_quantity), (:green_ml, :green_quantity), (:blue_ml, :blue_quantity), (:dark_ml, :dark_quantity)"),
                               [{"red_ml": 'RED_ML', "red_quantity": -1 * Potion.quantity * Potion.potion_type[0], "green_ml": 'GREEN_ML', "green_quantity": -1 * Potion.quantity * Potion.potion_type[1], "blue_ml": 'BLUE_ML', "blue_quantity": -1 * Potion.quantity * Potion.potion_type[2], "dark_ml": 'DARK_ML', "dark_quantity": -1 * Potion.quantity * Potion.potion_type[3]}])
    return "OK"

@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.
    bottle_plan = []
    bottler_plan = []
    with db.engine.begin() as connection:
        ml = connection.execute(sqlalchemy.text(
            "SELECT sku, COALESCE(SUM(quantity), 0) AS total FROM ledger WHERE sku LIKE '%ML' GROUP BY sku"))
        for sku, total in ml:
            if 'red' in sku.lower():
                curr_red_ml = total
            elif 'green' in sku.lower():
                curr_green_ml = total
            elif 'blue' in sku.lower():
                curr_blue_ml = total
            elif 'dark' in sku.lower():
                curr_dark_ml = total
        total_potions = connection.execute(sqlalchemy.text(
            "SELECT COALESCE(SUM(quantity), 0) FROM ledger WHERE sku LIKE '%POTION'")).scalar()
        caps = connection.execute(sqlalchemy.text(
            "SELECT potion_cap FROM capacities")).one()
        potion_cap = caps.potion_cap
        counter = 0
        while((total_potions < potion_cap) and (counter < (potion_cap + 10))):
            potions = connection.execute(sqlalchemy.text("""
                                                        SELECT potions.red, potions.green, potions.blue, potions.dark
                                                        FROM potions
                                                        LEFT JOIN (
                                                            SELECT sku, COALESCE(SUM(quantity), 0) AS total_quantity
                                                            FROM ledger
                                                            GROUP BY sku
                                                        ) AS ledger_quantity ON potions.sku = ledger_quantity.sku
                                                        WHERE potions.sku LIKE '%POTION' AND ledger_quantity.total_quantity < (potions.limit * :potion_cap)
                                                        GROUP BY potions.sku
                                                        ORDER BY COALESCE(SUM(ledger_quantity.total_quantity), 0) ASC"""),
                                         [{"potion_cap": potion_cap}])
            for red, green, blue, dark in potions:
                if (curr_red_ml >= red) and (curr_green_ml >= green) and (curr_blue_ml >= blue) and (curr_dark_ml >= dark) and (total_potions + 1 < potion_cap):
                    bottle_plan.append({
                        "potion_type": [red, green, blue, dark],
                        "quantity": 1,
                    })
                    curr_red_ml -= red
                    curr_green_ml -= green
                    curr_blue_ml -= blue
                    curr_dark_ml -= dark
                    total_potions += 1
                else:
                    counter += 1
            counter += 1
        potion_type_counts = {}
        for entry in bottle_plan:
            potion_type = tuple(entry["potion_type"])
            quantity = entry["quantity"]
            if potion_type in potion_type_counts:
                potion_type_counts[potion_type] += quantity
            else:
                potion_type_counts[potion_type] = quantity
        for potion_type, count in potion_type_counts.items():
            bottler_plan.append({
                "potion_type": list(potion_type),
                "quantity": count
            })
        print("Bottle Plan:")
        for step in bottler_plan:
            print(step)
    return bottler_plan

if __name__ == "__main__":
    print(get_bottle_plan())