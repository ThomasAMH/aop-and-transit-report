from pathlib import Path
import json
from datetime import datetime
from prepare_otd_report import prepare_otd_report
from prepare_dwell_time_report import prepare_dwell_time_report
from prepare_c2f_report import prepare_c2f_report


def main():
    """
    Script for preparing aop report, creating a month-by-month performance %
    of 3 key indicators:
        Click to Delivery
        On-time delivery
        Click to fuilfill
    """

    start_time = datetime.now()

    # Read in program data files
    with open(Path('./Program Data/combined_files/combined-filtered.json'),
              mode="r", encoding="utf-8-sig") as json_file:
        composite_dictionary = json.load(json_file)

    # Read in needed config files
    with open(Path('./Shared Config Files/countries.json'), mode="r",
              encoding="utf-8-sig") as json_file:
        country_config_data = json.load(json_file)

    with open(Path('./Shared Config Files/warehouses.json'), mode="r",
              encoding="utf-8-sig") as json_file:
        warehouse_config_data = json.load(json_file)

    print("O - OTD Report")
    print("D - Dwell Time Report")
    print("C - CTF Report")
    print("All - All reports")
    user_input = input("Which reports do you want?\n").lower()

    if user_input.find("o") != -1 or user_input.find("a") != -1:
        print("Preparing OTD Report")
        prepare_otd_report(country_config_data, composite_dictionary)

    if user_input.find("d") != -1 or user_input.find("a") != -1:
        print("Preparing Dwell Time Report")
        prepare_dwell_time_report(composite_dictionary, country_config_data)

    if user_input.find("c") != -1 or user_input.find("a") != -1:
        print("Preparing C2F Report")
        prepare_c2f_report(country_config_data, warehouse_config_data,
                           composite_dictionary)

    end_time = datetime.now()
    duration = end_time - start_time

    print(f'Report(s) prepared in in {str(duration.seconds)} seconds')


if __name__ == "__main__":
    main()
