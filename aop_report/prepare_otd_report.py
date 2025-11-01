from pathlib import Path
import json
import datetime as dt
from numpy import busday_count
import csv


def prepare_otd_report(country_config, composite_dict):
    '''
    Input: json objects with each warehouse's data
    Output: A text file with what percent of orders are on-time
    according to the each market's shipping criteria.

    Logic:
    Ontime is defined as when the valid delivery date (i.e. no returned status)
    the shipping date is equal to or lower than the 'on-time threshold'
    as provided in the config file.
    '''

    with open(Path("./Shared Config Files/holidays.json"),
              "r", newline='', encoding="utf-8-sig") as f:
        holiday_data = json.load(f)

    otd_report_data = {}
    otd_report_data.update({'country_data': {}})

    late_order_data = []

    for order, data in composite_dict.items():

        if data['status'] == "wh_data_only":
            continue

        # Get the ship_q method and country
        ship_q = data['ship_q']
        country = data['country'].lower()

        # Get the needed on time delivery deadline day
        if ship_q not in country_config[country]['otd_days']:
            print(f"Missing {ship_q} from {country} config!")
            continue

        otd_days = country_config[country]['otd_days'][ship_q]

        # Get holidays
        current_holidays = []
        for holiday in holiday_data["all"]:
            current_holidays.append(holiday)
        if country in holiday_data:
            current_holidays.extend(holiday_data[country])

        # For each order, get the shipping date and latest status date
        # Data is stored in datetime strings, but numpy requries iso strings
        # hence the weird conversion
        shipping_date = dt.datetime\
                          .fromisoformat(data['ship_datetime'])\
                          .date()\
                          .isoformat()
        latest_status_date = dt.datetime\
                               .fromisoformat(data['delivery_datetime'])\
                               .date()\
                               .isoformat()

        # Check num of business days:
        num_business_days = busday_count(shipping_date, latest_status_date,
                                         holidays=current_holidays)

        # Negative business days mean the data is wonky.
        if num_business_days < 0:
            otd_report_data['bad_wh_data'].append(order)
            continue

        # If an order gets through ALL THAT... get the yyyy-mm dictionary key
        date_key = shipping_date[:7]

        # Final sorting:
        if num_business_days <= otd_days:
            dest_dict = 'on_time_deliveries'
        else:
            dest_dict = 'late_deliveries'
            update_late_order_data(order, data, otd_days, late_order_data)

        if country not in otd_report_data['country_data']:
            temp_dict = {}
            temp_dict.update({'on_time_deliveries': {}})
            temp_dict.update({'late_deliveries': {}})

            otd_report_data['country_data'].update({country: temp_dict})

        if date_key in otd_report_data['country_data'][country][dest_dict]:
            otd_report_data['country_data'][country][dest_dict][date_key] += 1
        else:
            otd_report_data['country_data'][country][dest_dict]\
                .update({date_key: 1})

    # Write out report data
    with open(Path('./aop_report/Completed Reports/OTD Report.csv'),
              mode='w') as report_file:
        # Write main data in csv format:
        report_file.write('Late deliveries per month\n')
        report_file.write('country,month,count\n')
        for country, data in otd_report_data['country_data'].items():
            for month, value in data['late_deliveries'].items():
                report_file.write(f'{country},{str(month)},{str(value)}\n')
        report_file.write('\n')

        report_file.write('On time deliveries per month\n')
        report_file.write('country,month,count\n')
        for country, data in otd_report_data['country_data'].items():
            for month, value in data['on_time_deliveries'].items():
                report_file.write(f'{country},{str(month)},{str(value)}\n')
        report_file.write('\n')

    export_late_data(late_order_data)


def update_late_order_data(order, data, paige_day_arg, late_order_data):
    # Late order: order_number, country, ship_date,
    #            delivery_date, paige_day

    temp_obj = {
        "order_number": order,
        "country": data['country'].lower(),
        "paige_day": paige_day_arg,

        "shipping_date": dt.datetime
        .fromisoformat(data['ship_datetime'])
        .date()
        .isoformat(),

        "latest_status_date": dt.datetime
        .fromisoformat(data['delivery_datetime'])
        .date()
        .isoformat()
    }
    late_order_data.append(temp_obj)


def export_late_data(late_order_data):
    p = Path("./aop_report/Completed Reports/Late Order Data.csv")
    with open(p, mode="w", encoding="utf-8-sig", newline='') as f:
        iterator = iter(late_order_data)
        curr_record = next(iterator)
        writer = csv.DictWriter(f, fieldnames=curr_record.keys())
        writer.writeheader()
        writer.writerow(curr_record)
        for record in iterator:
            writer.writerow(record)
