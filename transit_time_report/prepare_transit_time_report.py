import json
import datetime as dt
from pathlib import Path
import numpy as np
import sys


def prepare_transit_time_report(input_file_path=""):
    with open(Path("./Shared Config Files/holidays.json"),
              "r", newline='', encoding="utf-8-sig") as f:
        holiday_data = json.load(f)

    # Read in input data
    order_data = {}
    if input_file_path == "":
        input_path = Path(
            "./Program Data/combined_files/combined-filtered.json")
    else:
        input_path = Path(input_file_path)
    with open(input_path, mode="r", encoding="utf-8-sig", newline='') as file:
        order_data = json.load(file)

    # Record transit time
    wh_data_only_count = 0
    result_dictionary = {}
    for order, data in order_data.items():
        if data['status'] == "wh_data_only":
            wh_data_only_count += 1
            continue
        record_transit_time(order, data, result_dictionary, holiday_data)

    # Write results to completed report
    with open(Path("./Transit Time Report/completed_reports/"
                   f"{dt.date.today().isoformat()}.txt"),
              mode="w") as report_file:
        report_file.write("Transit Time Report\n")
        report_file.write("-"*60+"\n")
        no_transit_percent = (wh_data_only_count / len(order_data)) * 100
        report_file.write("% of orders without transit data: "
                          f"{no_transit_percent:.2f}%\n")
        report_file.write(f"{wh_data_only_count} / {len(order_data)} orders\n")
        report_file.write("-"*60+"\n")
        report_file.write("Data\n")
        report_file.write("-"*60+"\n")
        report_file.write("country,carrier_code,date_stamp,"
                          "order,bus_days_in_transit\n")
        for ctry in result_dictionary.keys():
            carrier_codes = result_dictionary[ctry].keys()
            for carrier in carrier_codes:
                date_stamps = result_dictionary[ctry][carrier].keys()
                for date in date_stamps:
                    order_data = result_dictionary[ctry][carrier][date].items()
                    for order, days_in_transit in order_data:
                        report_file.write(f"{ctry},{carrier},{date},"
                                          f"{order},{days_in_transit}")
                        report_file.write('\n')

    print("Report Complete!")


def has_error(order_data_dict, unique_orders_dict, statuses_dict, error_dict):
    """
    Check if an order has anything that would be an error.
    Update error handling dictionary, if so, and return true, otherwise false
    """
    order_num = order_data_dict['Shipment Reference'].replace("DT", "")\
                                                     .replace("_DOTERRA", "")

    if order_num in unique_orders_dict:
        return True

    # Unknown tracking status check
    if order_data_dict['Latest Status'].lower() not in statuses_dict:
        temp_object = {
            order_num: order_data_dict['Latest Status'].lower()
        }
        error_dict['unknown_tracking_message'].append(temp_object)
        return True

    # No delivery message check
    # statuses_dict returns true if status message is delivered.
    # blank messages are interpreted as not delivered
    if not statuses_dict[order_data_dict['Latest Status'].lower()]:
        temp_object = {
            order_num: order_data_dict['Latest Status'].lower()
        }
        error_dict['order_not_delivered'].append(temp_object)
        return True

    # Ship date validity check
    try:
        ship_date = dt.datetime.fromisoformat(
            order_data_dict['Processed Date'])
    except ValueError:
        temp_object = {
            order_num: order_data_dict['Processed Date'].lower()
        }
        error_dict['none_or_invalid_ship_date'].append(temp_object)
        return True

    # Delivery date validity check
    try:
        delivery_date = dt.datetime.fromisoformat(
            order_data_dict['First Delivery Date'])
    except ValueError:
        temp_object = {
            order_num: order_data_dict['First Delivery Date'].lower()
        }
        error_dict['none_or_invalid_delivery_date'].append(temp_object)
        return True

    if delivery_date < ship_date:
        temp_object = {
            order_num: f"ship: {ship_date.isoformat()},"
                       f"delivery: {delivery_date.isoformat()}"
        }
        error_dict['ship_date_after_delivery_date'].append(temp_object)
        return True

    return False


def record_transit_time(order, data, result_dictionary, holiday_data):
    """
    Record the transit time into the result dictionary
    """

    country = data['country'].lower()
    ship_to_code = data['ship_q']

    ship_date = dt.datetime.fromisoformat(
        data['ship_datetime'])
    delivery_date = dt.datetime.fromisoformat(
        data['delivery_datetime'])
    time_stamp = f"{ship_date.year}-{ship_date.month}"

    # Get holidays
    current_holidays = []
    for holiday in holiday_data["all"]:
        current_holidays.append(holiday)
    if country in holiday_data:
        current_holidays.extend(holiday_data[country])

    # Code for business days
    days_in_transit = np.busday_count(ship_date.date(), delivery_date.date(),
                                      holidays=current_holidays)

    if country not in result_dictionary:
        result_dictionary.update({country: {}})

    if ship_to_code not in result_dictionary[country]:
        result_dictionary[country].update({ship_to_code: {}})

    if time_stamp not in result_dictionary[country][ship_to_code]:
        result_dictionary[country][ship_to_code].update({time_stamp: {}})

    temp_object = {order: days_in_transit}

    result_dictionary[country][ship_to_code][time_stamp].update(temp_object)


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) > 1:
        print("Passing in " + argv[1])
        prepare_transit_time_report(argv[1])
    else:
        prepare_transit_time_report()
