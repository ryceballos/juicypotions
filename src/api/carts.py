from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth
from enum import Enum
import sqlalchemy
from src import database as db

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """
    results = []
    prev_results = []
    next_results = []
    full_result = []
    with db.engine.begin() as connection:
        if customer_name and potion_sku:
            search_results = connection.execute(sqlalchemy.text("""
                                                                SELECT cart_items.line_item_id, customers.created_at AS timestamp, cart_items.quantity
                                                                FROM cart_items
                                                                JOIN carts on cart_items.cart_id = carts.cart_id
                                                                JOIN potions on potions.sku = cart_items.sku
                                                                JOIN customers on customers.customer_id = carts.customer_id
                                                                WHERE cart_items.sku = :sku AND customers.name = :name
                                                                ORDER BY {} {}""".format(sort_col.value, sort_order.value)),
                                                                [{"sku": potion_sku, "name": customer_name}])
            if search_results:
                for line_item_id, created_at, quantity in search_results:
                    price = connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE sku = :sku"),
                                               [{"sku": potion_sku}]).scalar()
                    total = price * quantity
                    full_result.append({
                        "line_item_id": line_item_id,
                        "item_sku": potion_sku,
                        "customer_name": customer_name,
                        "line_item_total": total,
                        "timestamp": created_at,
                    })
        elif customer_name:
            search_results = connection.execute(sqlalchemy.text("""
                                                                SELECT cart_items.line_item_id, customers.created_at AS timestamp, cart_items.sku, cart_items.quantity
                                                                FROM cart_items
                                                                JOIN carts on cart_items.cart_id = carts.cart_id
                                                                JOIN potions on potions.sku = cart_items.sku
                                                                JOIN customers on customers.customer_id = carts.customer_id
                                                                WHERE customers.name = :name
                                                                ORDER BY {} {}""".format(sort_col.value, sort_order.value)),
                                                                [{"name": customer_name}])
            if search_results:
                for line_item_id, created_at, sku, quantity in search_results:
                    price = connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE sku = :sku"),
                                               [{"sku": sku}]).scalar()
                    total = price * quantity
                    full_result.append({
                        "line_item_id": line_item_id,
                        "item_sku": sku,
                        "customer_name": customer_name,
                        "line_item_total": total,
                        "timestamp": created_at,
                    })
        elif potion_sku:
            search_results = connection.execute(sqlalchemy.text("""
                                                                SELECT cart_items.line_item_id, customers.created_at AS timestamp, customers.name, cart_items.quantity
                                                                FROM cart_items
                                                                JOIN carts on cart_items.cart_id = carts.cart_id
                                                                JOIN potions on potions.sku = cart_items.sku
                                                                JOIN customers on customers.customer_id = carts.customer_id
                                                                WHERE cart_items.sku = :sku
                                                                ORDER BY {} {}""".format(sort_col.value, sort_order.value)),
                                                                [{"sku": potion_sku}])
            if search_results:
                for line_item_id, created_at, name, quantity in search_results:
                    price = connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE sku = :sku"),
                                               [{"sku": potion_sku}]).scalar()
                    total = price * quantity
                    full_result.append({
                        "line_item_id": line_item_id,
                        "item_sku": potion_sku,
                        "customer_name": name,
                        "line_item_total": total,
                        "timestamp": created_at,
                    })
        else:
            search_results = connection.execute(sqlalchemy.text("""
                                                                SELECT cart_items.line_item_id, customers.created_at AS timestamp, customers.name, cart_items.sku, cart_items.quantity
                                                                FROM cart_items
                                                                JOIN carts on cart_items.cart_id = carts.cart_id
                                                                JOIN potions on potions.sku = cart_items.sku
                                                                JOIN customers on customers.customer_id = carts.customer_id
                                                                ORDER BY {} {}""".format(sort_col.value, sort_order.value)))
            if search_results:
                for line_item_id, created_at, name, sku, quantity in search_results:
                    price = connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE sku = :sku"),
                                               [{"sku": sku}]).scalar()
                    total = price * quantity
                    full_result.append({
                        "line_item_id": line_item_id,
                        "item_sku": sku,
                        "customer_name": name,
                        "line_item_total": total,
                        "timestamp": created_at,
                    })
        if search_page == "":
            search_page = 2
        else:
            search_page = int(search_page) + 2
        if search_page > 1:
            prev_results = full_result[(((search_page - 1) * 5) - 5):(((search_page - 1) * 5) - 1)]
            results = full_result[((search_page * 5) - 5):((search_page * 5) - 1)]
            next_results = full_result[(((search_page + 1) * 5) - 5):(((search_page + 1) * 5) - 1)]
    return {
        "previous": prev_results,
        "next": next_results,
        "results": results
    }
    # return {
    #     "previous": "",
    #     "next": "",
    #     "results": [
    #         {
    #             "line_item_id": 1,
    #             "item_sku": "1 oblivion potion",
    #             "customer_name": "Scaramouche",
    #             "line_item_total": 50,
    #             "timestamp": "2021-01-01T00:00:00Z",
    #         }
    #     ],
    # }


class Customer(BaseModel):
    customer_name: str
    character_class: str
    level: int

@router.post("/visits/{visit_id}")
def post_visits(visit_id: int, customers: list[Customer]):
    """
    Which customers visited the shop today?
    """
    print(customers)

    
    return "OK"

@router.post("/")
def create_cart(new_cart: Customer):
    """ Create a cart for a new customer """
    with db.engine.begin() as connection:
        customer_id = connection.execute(sqlalchemy.text("INSERT INTO customers (name, class, level) VALUES (:name, :class, :level) RETURNING customer_id"),
                                         [{"name": new_cart.customer_name, "class": new_cart.character_class, "level": new_cart.level}]).scalar()
        cart_id = connection.execute(sqlalchemy.text("INSERT INTO carts (customer_id) VALUES (:customer_id) RETURNING cart_id"),
                                     [{"customer_id": customer_id}]).scalar()
    return {"cart_id": cart_id}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(
            "INSERT INTO cart_items (cart_id, sku, quantity) VALUES( :cart_id, :sku, :quantity)"),
                        [{"cart_id": cart_id, "sku": item_sku, "quantity": cart_item.quantity}])
    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    print(cart_checkout)
    total_gold_gained = 0
    total_potions_sold = 0
    with db.engine.begin() as connection:
        items = connection.execute(sqlalchemy.text("SELECT cart_id AS items_cart_id, sku, quantity FROM cart_items"))
        for items_cart_id, sku, quantity in items:
            price = connection.execute(sqlalchemy.text("SELECT price FROM potions WHERE sku = :sku"),
                                       [{"sku": sku}]).scalar()
            if (items_cart_id == cart_id):
                total_gold_gained += (quantity * 50)
                total_potions_sold += quantity
                connection.execute(sqlalchemy.text(
                    "INSERT INTO ledger (sku, quantity) VALUES (:gold, :gold_gained), (:sku, :quantity)"),
                            [{"gold": 'gold', "gold_gained": quantity * price, "sku": sku, "quantity": -1 * quantity}])
    return {"total_potions_bought": total_potions_sold, "total_gold_paid": total_gold_gained}