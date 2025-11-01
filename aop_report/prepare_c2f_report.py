from pathlib import Path
from datetime import datetime
from numpy import busday_count
from helper_functions import get_order_warehouse
from zoneinfo import ZoneInfo


def prepare_c2f_report(country_data_json, warehouse_config_data,
                       composite_dict):
    """
    Input: json objects with each warehouse's data
    Output: A text file with what percent of orders
    are on-time according to the config file.

    Logic:
        On time is defined as when the valid delivery date
        (i.e. no returned status) - the invoice date is
        equal to or lower than the
        "on-time threshold" provided on the config file.
    """

    # Prepare result dictionaries
    wh_dict = {}
    wh_list = []
    for warehouse in warehouse_config_data['warehouse_locations']:
        if warehouse not in wh_list:
            temp_dict = {}
            temp_dict.update({"on_time_deliveries": {}})
            temp_dict.update({"late_deliveries": {}})

            wh_dict.update({warehouse: temp_dict})
            wh_list.append(warehouse)

    country_dict = {}
    country_list = country_data_json.keys()
    for country in country_list:
        temp_dict = {}
        temp_dict.update({"on_time_deliveries": {}})
        temp_dict.update({"late_deliveries": {}})

        country_dict.update({country: temp_dict})

    for order, data in composite_dict.items():

        if data["status"] != "clean":
            continue

        result = determine_late_or_ontime(order, data, country_data_json)

        # Get the yyyy-mm dictionary key
        invoice_date = result['invoice_date']
        date_key = invoice_date[:7]

        # Get order warehouse, taking into account the days the warehouses
        # Were swapped
        order_wh = get_order_warehouse(warehouse_config_data,
                                       country_data_json,
                                       datetime.fromisoformat(invoice_date),
                                       data['country'])
        # Get order country
        country = data['country'].lower()

        # Decide destination dict
        if result['result'] == 'on time':
            dest_dict = 'on_time_deliveries'
        elif result['result'] == 'late':
            dest_dict = 'late_deliveries'

        # Update the warehouse dictionaries
        if date_key in wh_dict[order_wh][dest_dict]:
            wh_dict[order_wh][dest_dict][date_key] += 1
        else:
            wh_dict[order_wh][dest_dict].update({date_key: 1})

        # Update the country dictionaries
        if date_key in country_dict[country][dest_dict]:
            country_dict[country][dest_dict][date_key] += 1
        else:
            country_dict[country][dest_dict].update({date_key: 1})

    write_report_data(wh_dict, wh_list, country_dict, country_list)


def determine_late_or_ontime(order, data,
                             country_config_json):
    return_dict = {}
    return_dict.update({'invoice_date': ''})
    return_dict.update({'result': ''})

    # Get the ship_q method and country
    ship_q = data['ship_q']
    country = data['country'].lower()

    # For each order, get the shipping date and latest status date
    # Data is stored in datetime strings,
    # but numpy requries iso strings, hence the weird conversion
    invoice_date_datetime = datetime.fromisoformat(
        data['invoice_datetime'])

    # Included here to account for the American invoice date
    time_zone_diff = daylight_savings_time_adjustment(
        invoice_date_datetime, country)

    invoice_date = (invoice_date_datetime + time_zone_diff)\
        .date() \
        .isoformat()

    latest_status_date = datetime.fromisoformat(data['delivery_datetime'])\
        .date() \
        .isoformat()

    # Get num of business days:
    num_business_days = busday_count(invoice_date, latest_status_date)

    # Get the needed sla
    otd_days = country_config_json[country]['otd_days'][ship_q]

    # Assign results
    if num_business_days <= (otd_days + 2):
        return_dict['result'] = 'on time'
    else:
        return_dict['result'] = 'late'

    return_dict['invoice_date'] = invoice_date

    return return_dict


def write_report_data(wh_dict, wh_list, country_dict, ctry_list):
    # Write out warheouse report data
    with open(Path('./aop_report/Completed Reports/c2f wh report.csv'),
              mode='w') as report_file:
        report_file.write("On time deliveries per month: \n")

        for wh in wh_list:
            for month, value in wh_dict[wh]['on_time_deliveries']\
                                .items():
                report_file.write(f"{wh},{str(month)},{str(value)}\n")
        report_file.write("\n")

        report_file.write("Late deliveries per month: \n")
        for wh in wh_list:
            for month, value in wh_dict[wh]['late_deliveries']\
                                .items():
                report_file.write(f"{wh},{str(month)},{str(value)}\n")
        report_file.write("\n")

    # Write out country report data
    with open(Path('./aop_report/Completed Reports/c2f country report.csv'),
              mode='w') as report_file:
        report_file.write("On time deliveries per month: \n")

        for ctry in ctry_list:
            for month, value in country_dict[ctry]['on_time_deliveries']\
                                .items():
                report_file.write(f"{ctry},{str(month)},{str(value)}\n")
        report_file.write("\n")

        report_file.write("Late deliveries per month: \n")
        for ctry in ctry_list:
            for month, value in country_dict[ctry]['late_deliveries']\
                                .items():
                report_file.write(f"{ctry},{str(month)},{str(value)}\n")
        report_file.write("\n")


def daylight_savings_time_adjustment(date_time, country):
    """
    Apply daylight savings to report data
    """
    eu_tz_name = "Europe/Warsaw"
    if country == 'uk':
        eu_tz_name = "Europe/London"
    eu_tz = ZoneInfo(eu_tz_name)
    us_tz = ZoneInfo("America/Denver")

    dt_aware_eu = date_time.replace(tzinfo=eu_tz)
    dt_aware_us = date_time.replace(tzinfo=us_tz)

    offset_eu = dt_aware_eu.utcoffset()
    offset_us = dt_aware_us.utcoffset()

    return abs(offset_eu - offset_us)
