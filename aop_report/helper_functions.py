from datetime import datetime


def get_order_warehouse(wh_data, country_data, import_datetime, order_country):
    order_country = order_country.lower()
    order_warehouse = country_data[order_country]['warehouse']

    if order_country in wh_data['warehouse_swap_dates']:
        swap_date = datetime.fromisoformat(
            wh_data['warehouse_swap_dates'][order_country]['date'])

        if import_datetime >= swap_date:
            order_warehouse = \
                wh_data['warehouse_swap_dates'][order_country]['swap_to']
    return order_warehouse
