import datetime as dt
from pathlib import Path
import json
import os


def query_program_data():
    """
    Prepare program data and error reports based on user-selected date range
    """
    raw_program_data = read_program_data()
    prepare_error_reports(raw_program_data)

    # Finalize object
    prepare_program_data(raw_program_data)


def prepare_error_reports(raw_program_data):

    # Clear the error directory of all .txt files
    output_data_dir = Path('./Data Handling/Input Data Errors/').glob("*.txt")
    for file in output_data_dir:
        os.remove(file)

    error_dict = prepare_error_dict(raw_program_data)

    # Write error summary file
    with open(Path("./Data Handling/Input Data Errors/0 - Error Summary.txt"),
              mode="w", encoding="utf-8-sig", newline='') as error_file:
        total_wh_orders = error_dict["num_unique_orders"]
        error_file.write("Total number of warehouse orders: "
                         f"{total_wh_orders:,}\n")
        sum_errors = error_dict["sum_errors"]
        error_file.write(f"Total number of errors: {sum_errors:,}\n")
        error_percent = (sum_errors / total_wh_orders)*100
        error_file.write(f"Error Percentage: {error_percent:.2f}%\n")
        error_file.write("-"*60+"\n")

        iter_error_dict = error_dict["error_dict"]
        for error_type, errors in iter_error_dict.items():
            if len(errors) == 0:
                continue
            error_file.write(error_type+"\n")
            error_file.write("-"*60+"\n")
            error_file.write("  Instances of this error: "
                             f"{len(errors):,}\n")

            error_percent = (len(errors) / total_wh_orders)*100
            error_file.write("  Percent of all orders with this error: "
                             f"{error_percent:.2f}%\n")

            error_percent = (len(errors) / sum_errors)*100
            error_file.write("  Percent of errors this error represents: "
                             f"{error_percent:.2f}%\n")
            error_file.write("-"*60+"\n")

    # Write order details file, if any
    for error_type, errors in iter_error_dict.items():
        if len(errors) == 0:
            continue

        with open(Path(f"./Data Handling/Input Data Errors/{error_type}.txt"),
                  mode="w", encoding="utf-8-sig", newline='') as error_file:

            error_file.write(error_type+"\n")
            error_file.write("-"*60+"\n")
            error_file.write("  Instances of this error: " +
                             f"{len(errors):,}\n")

            error_percent = (len(errors) / total_wh_orders)*100
            error_file.write("  Percent of all orders with this error: "
                             f"{error_percent:.2f}%\n")

            error_percent = (len(errors) / sum_errors)*100
            error_file.write("  Percent of errors this error represents: "
                             f"{error_percent:.2f}%\n")
            error_file.write("-"*60+"\n")

            for order, order_data in errors.items():
                error_file.write(f"{order}{order_data}\n")


def prepare_error_dict(raw_program_data):
    error_dict = {}
    unique_orders = {}
    error_dict.update({"sum_errors": 0})
    error_dict.update({"error_dict": {}})
    error_code = ""
    details = ""
    # The first colon marks the end of the code and start of the details
    colon_index = 0

    for month_data in raw_program_data.values():
        curr_error_dict = month_data["dirty_data"]

        for order, data in curr_error_dict.items():
            if order not in unique_orders.keys():
                unique_orders.update({order: ""})
                error_dict["sum_errors"] += 1

            colon_index = data["error_code"].find(":")
            if colon_index == -1:
                error_code = data["error_code"]
                details = ""
            else:
                error_code = data["error_code"][:colon_index]
                details = data["error_code"][colon_index:]
            if error_code not in error_dict["error_dict"].keys():
                error_dict["error_dict"].update({error_code: {}})

            error_dict["error_dict"][error_code].update(
                {order: details})

        clean_order_dict = month_data["clean_data"]
        for order in clean_order_dict.keys():
            if order not in unique_orders.keys():
                unique_orders.update({order: ""})

    error_dict.update({"num_unique_orders": len(unique_orders.keys())})

    return error_dict


"""
This is the code for writing the FYI file:
    # Write out information file
    with open(Path("./Data Handling/Input Data Errors/0 - Input Data FYI.txt"),
            mode="w", encoding="utf-8-sig", newline='') as FYI_file:
        FYI_file.write("Input Data Information\n")
        FYI_file.write("-"*60+"\n")

        FYI_file.write('Count of orders without warehouse data by period\n')
        FYI_file.write('possibly due to extra DataExtract data,\n')
        for period, period_data in fyi_dict["Missing Warehouse Data"].items():
            FYI_file.write(f"{period}: {len(period_data)}\n")

        FYI_file.write("-"*60+"\n")

        for period, data in fyi_dict["Missing Warehouse Data"].items():
            FYI_file.write("-"*60+"\n")
            FYI_file.write(f"{period}\n")
            FYI_file.write("-"*60+"\n")
            FYI_file.write("order,invoice_date,country\n")
            for order, import_date in data.items():
                date = dt.datetime.fromisoformat(import_date)\
                                .date().isoformat()
                country = grouped_data[order].get("country", "")
                FYI_file.write(f"{order},{date},{country}\n")
            FYI_file.write("-"*60+"\n")
"""


def read_program_data():
    """
    Get a start date and an end date from the user.
    Prepare filtered program data objects using those dates.
    """
    print("Note: Regardless of date entered, entire month will be included!")
    start_date_str =\
        input("Input the start date (inclusive; format: yyyy-mm-dd):\n")
    end_date_str =\
        input("Input the end date (exclusive; format: yyyy-mm-dd):\n")

    start_dt = dt.datetime.fromisoformat(start_date_str)
    end_dt = dt.datetime.fromisoformat(end_date_str)
    start_file = str(start_dt.year) + "-" + str(start_dt.month) + ".json"
    end_file = str(end_dt.year) + "-" + str(end_dt.month) + ".json"
    curr_file = start_file
    next_month = start_dt.month
    year_offset = 0

    raw_program_data = {}
    break_flag = False
    while True:
        if curr_file == end_file:
            break_flag = True

        curr_file_path = Path("./Program Data/data_by_month/" + curr_file)
        if not curr_file_path.is_file():
            print(f"Warning! Missing file: {curr_file_path.name}. Skipping.")
        else:
            with open(curr_file_path, mode="r", encoding="utf-8-sig") as f:
                file_data = json.load(f)
                raw_program_data.update({curr_file: file_data})

        next_month += 1
        if next_month == 13:
            next_month = 1
            year_offset += 1

        curr_file = str(start_dt.year + year_offset) +\
            "-" + str(next_month) + ".json"

        if break_flag:
            return raw_program_data


def prepare_program_data(raw_program_data):
    program_data_path =\
        Path("./Program Data/combined_files/combined-filtered.json")

    clean_data = {}
    for month_data in raw_program_data.values():
        clean_data.update(month_data["clean_data"])

    with open(program_data_path, mode="w", encoding="utf-8-sig") as f:
        json.dump(clean_data, f)


if __name__ == "__main__":
    query_program_data()
    print("Program data loaded - Check Error Reports")
