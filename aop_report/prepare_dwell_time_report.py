from pathlib import Path
import json
import datetime as dt
from numpy import busday_offset
from helper_functions import get_order_warehouse


def prepare_dwell_time_report(composite_dictionary, country_data):
    """
    Input:
    Output: A text file with what percent of orders are processed on time.

    Logic:
    On time is one day, and out before the end of the next
    accounting for some holidays and a few exceptional date swaps.
    """

    # Read in wh dict
    with open(Path('./Shared Config Files/warehouses.json'),
              mode="r") as json_file:
        wh_config_data = json.load(json_file)

    summary_dict = {}
    order_dict = {}

    # Constants
    # Cutoff time is in LOCAL time
    # If we add a cutoff time:
    # time.fromisoformat(country_data_dict['universal_cutoff_time'])

    # Calculate a status add it to the count dictionary
    # Keys: yyyy-mm and status key
    for order, data in composite_dictionary.items():
        country = data['country'].lower()
        import_datetime = dt.datetime.fromisoformat(data['import_datetime'])
        import_datetime = import_datetime.replace(tzinfo=None)

        warehouse = get_order_warehouse(wh_config_data, country_data,
                                        import_datetime, country)

        ship_datetime = dt.datetime.fromisoformat(data['ship_datetime'])

        # Begin status message construction
        status_message = ""

        # Set holidays
        holidays = []
        holidays += wh_config_data['holidays']['all']
        holidays += wh_config_data['holidays'][warehouse]

        # Set early, on-time, or late string:
        # used in status message where order is not shipped the same day,
        # or where order was received on holiday/weekend
        early_on_late_string = get_early_on_late_string(import_datetime,
                                                        ship_datetime,
                                                        holidays)

        # Check if the order was received on a holiday or weekend
        # If so,  append message:
        if import_datetime.date() in holidays\
           or import_datetime.date().isoweekday() > 5:
            if import_datetime.date() in holidays:
                status_message += "received on holiday: "
            elif import_datetime.date().isoweekday() > 5:
                status_message += "received on weekend: "

        status_message += early_on_late_string
        record_status(status_message, import_datetime,
                      summary_dict, order, warehouse, order_dict)

    # Write results to files
    with open(Path('./aop_report/Completed Reports/Dwell Time Report.csv'),
              mode="w", encoding="utf-8-sig", newline="") as results_file:
        results_file.write("facility,time,status,count\n")
        for facility, date_stamps in summary_dict.items():
            for date_stamp, status_messages in date_stamps.items():
                for message, count in status_messages.items():
                    results_file.write(f"{facility},{date_stamp},"
                                       f"{message},{count}\n")

    # Write order breakdown
    with open(Path('./aop_report/Completed Reports/'
                   'Dwell Time Order Details.txt'), mode="w")\
         as order_details_file:
        for order, status in order_dict.items():
            order_details_file.write(f"{order}: {status}\n")


def record_status(status_message, import_datetime, summary_dict,
                  order_num, order_warehouse, order_dict):
    """
    Record the status of an order in the summary_dict
    """

    if order_warehouse not in summary_dict:
        summary_dict.update({order_warehouse: {}})

    date_key = f'{import_datetime.year} - {import_datetime.month}'

    if date_key not in summary_dict[order_warehouse]:
        summary_dict[order_warehouse].update({date_key: {}})

    if status_message not in summary_dict[order_warehouse][date_key]:
        summary_dict[order_warehouse][date_key].update({status_message: 1})
    else:
        summary_dict[order_warehouse][date_key][status_message] += 1

    if order_num not in order_dict:
        order_dict.update({order_num: status_message})


def get_early_on_late_string(import_datetime,
                             ship_datetime, holidays):
    """
    Take in a workday and list of holidays to provide a date object that
    represents the next day that package should be shipped
    """

    CUTOFF_TIME = dt.time(17, 0)
    import_day = import_datetime.date()
    import_time = import_datetime.time()

    bus_day_offset = 1
    if import_time > CUTOFF_TIME and import_day.weekday() == 4:
        bus_day_offset = 2

    if import_day.weekday() == 5 or import_day.weekday() == 6:
        bus_day_offset = 2

    next_business_day = dt.date.fromisoformat(
        str(busday_offset(import_day.isoformat(), bus_day_offset, 'forward',
                          holidays=holidays)))

    ship_date = ship_datetime.date()
    if ship_date <= next_business_day:
        return "shipped on time"
    if ship_date > next_business_day:
        return "shipped late"
