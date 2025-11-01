from pathlib import Path
import json
import csv
import datetime as dt


def prepare_program_data():
    """
    This function reads all the files in the Input Data folder,
    Maps the headers, and saves the useful data into json objects.
    Check for errors.
    Saves objects live in the Program Data folder for later use
    """
    with open(Path('./Shared Config Files/headers.json'),
              mode="r", encoding="utf-8-sig") as json_file:
        headers_dict = json.load(json_file)

    # Read input files and extract meaningful data
    input_data = {}
    all_input_data = {}
    for input_type in Path("./Input Data/").iterdir():
        input_data = {}
        print(f"\nReading {input_type.name} files")
        if input_type.name == "data_extract":
            input_data = prepare_dataextract_data()
        else:
            input_data = jsonify_data(headers_dict, input_type.name)
        all_input_data.update({input_type.name: input_data})

    combined_data = combine_data(all_input_data, headers_dict)
    grouped_data = group_input_data(combined_data)
    sorted_group_data = run_error_checks(grouped_data)

    # Line commened out, as reports are to include "pure" SLA, not adjusted
    # filtered_data = perform_exceptional_date_swap(filtered_data)
    update_program_data(sorted_group_data)


def jsonify_data(headers_dict, file_type):
    """
    Read in data of the specifified file type,
    return the data from that object as a dictionary
    Inputs:
        headers_dict: headers.json file contents as a dictionary
                      Maps wanted data to headers in the file type
        file_type: string specifying the name input data directory.
                   Specified directory will be iterated through for
                   data files. Also specifies which header mapping set to use.
    """
    # These headers will be looped through for each file type.
    # This allows us to store other data in the headers config file besides,
    # Just the header mappings like time offset
    normal_headers = headers_dict["normal_headers"]
    return_dict = {}
    temp_dict = {}
    headers_set = headers_dict[file_type]
    try:
        for file in Path(f"./Input Data/{file_type}/").iterdir():
            with open(file, mode="r", encoding="utf-8-sig",
                      newline="") as file:
                print(f"    Now processing {file.name}")
                csv_reader = csv.DictReader(file)
                for entry in csv_reader:
                    order_num = entry[headers_set['order_number']]\
                                .replace("DT", "")\
                                .replace("_DOTERRA", "")

                    if order_num not in return_dict:
                        for header in normal_headers:
                            if header in headers_set.keys():
                                if "datetime" in header:
                                    good_date = return_iso_date(
                                        entry[headers_set[header]],
                                        headers_set["datetime_format"])
                                    temp_dict.update({header: good_date})
                                else:
                                    temp_dict.update(
                                        {header: entry[headers_set[header]]})

                        return_dict.update({order_num: temp_dict})
                        temp_dict = {}
                    else:
                        # Compare the two entry's data.
                        # If one is empty, take the one with data.
                        # If both have data, stick with what was entered first
                        # by taking no action
                        for header in normal_headers:
                            if return_dict[order_num].get(header) is None \
                             and header in headers_set.keys():
                                if "datetime" in header:
                                    good_date = return_iso_date(
                                        entry[headers_set[header]],
                                        headers_set["datetime_format"])
                                    return_dict[order_num][header] =\
                                        good_date
                                else:
                                    return_dict[order_num][header] = \
                                        entry[headers_set[header]]
    except KeyError as e:
        print(f"Uh oh! I can't find the column header {e.args[0]}")
        print("Make sure the data in the Settings/headers.json file match the "
              "data in every file, then rerun.\n")
        print(e)
        exit()
    except UnicodeDecodeError as e:
        print("Error! I'm having trouble decoding the file.\n"
              "Copy the data over to a new excel, save as .csv then rerun\n.")
        print(e)
        exit()
    except Exception as e:
        print("An error that I wasn't prepared for has occured!")
        print(f"Current File: {file.name}\n")
        print(e)
        exit()

    return return_dict


def prepare_dataextract_data():
    dataextract_data_dict = {}
    temp_dict = {}
    for file in Path("./Input Data/data_extract/").iterdir():
        print(f"    Now processing {file.name}")
        with open(file, mode="r",
                  encoding="utf-8-sig", newline="") as dataextract_csv_file:
            csv_reader = csv.DictReader(dataextract_csv_file)

            for entry in csv_reader:
                # ignore all orders that were ship verified by an agent
                if entry['order_verify_init'] != "":
                    continue
                if entry['order_number'] not in dataextract_data_dict:
                    temp_dict = {}
                    temp_dict.update({"id": entry['dist_id']})

                    read_invoice_date = \
                        dt.date.fromisoformat(entry['invoice_date'])
                    read_invoice_time =\
                        dt.time.fromisoformat(entry['invoice_time']) if \
                        entry['invoice_time'] != "::" else \
                        dt.time(0, 0)

                    # Offset invoice time by 7 hours if country is UK
                    # 8 if Europe
                    invoice_datetime = dt.datetime.combine(read_invoice_date,
                                                           read_invoice_time)

                    match entry['ship_to_country']:
                        case "EO":
                            temp_dict.update(
                                {"country": entry['ship_to_addr_3'].lower()})
                        case "GBR":
                            temp_dict.update({"country": "uk"})
                        case "MDA":
                            temp_dict.update({"country": "moldova"})
                        case "DEU":
                            temp_dict.update({"country": "germany"})
                        case "ITA":
                            temp_dict.update({"country": "italy"})
                        case "ISR":
                            temp_dict.update({"country": "israel"})
                        case "FRA":
                            temp_dict.update({"country": "france"})
                        case "POL":
                            temp_dict.update({"country": "poland"})
                        case _:
                            temp_dict.update({"country": "missing from prepare_program_data"})

                    temp_dict.update(
                        {"invoice_datetime": invoice_datetime.isoformat()})

                    if entry['ship_via'].lower().find("stan") == -1:
                        temp_dict.update({"ship_q": "prem"})
                    else:
                        temp_dict.update({"ship_q": "stand"})

                    dataextract_data_dict.update(
                        {entry['order_number']: temp_dict})
    return dataextract_data_dict


def return_iso_date(date_string, date_format_string):
    if date_string == "":
        return ""
    if date_format_string == "iso":
        return date_string
    return dt.datetime.strptime(date_string, date_format_string).isoformat()


def combine_data(combined_file_data, headers_dict):
    """
    Combine all data into a single JSON object.
    Loops through all DataExtract data and adds transit and WH data
    """
    print("\nCombining input data")
    consolidated_dict = {}

    # Add transit and other input data
    for type, dict in combined_file_data.items():
        for order, data in dict.items():
            # If the data does not exist in the consolidated dict, add it
            if order not in consolidated_dict:
                consolidated_dict.update({order: data})
            else:
                # If it does, check each key in the data dict.
                for key in data.keys():
                    if key not in consolidated_dict[order].keys():
                        # If the key doesn't exist in the dict, add it
                        consolidated_dict[order].update(
                            {key: data[key]}
                        )
                    else:
                        # Check if the overwrite tag.
                        # If true, overwrrite, and if not, ignore
                        if headers_dict[type].get("overwrite", False):
                            consolidated_dict[order].update(
                                {key: data[key]}
                            )

    return consolidated_dict


def run_error_checks(grouped_data):
    """
    Run checks on the data and remove "unclean" data to a log file
    """
    print("Running error checks\n")
    with open("./Shared Config Files/countries.json", mode="r") as file:
        country_data = json.load(file)

    with open("./Shared Config Files/statuses.csv", mode="r") as file:
        status_data = {}
        status_data_reader = csv.DictReader(file)
        for row in status_data_reader:
            status_data.update({row["status_message"]: "is_delivered"})

    sorted_data = {}

    # Missing data by period (yyyy-m)
    for month, month_data in grouped_data.items():
        fyi_dict = {}
        dirty_data = {}
        clean_data = {}
        for order, data in month_data.items():

            # Check for dataextract data
            if not data.get("country", False):
                update_error_dict(dirty_data, order,
                                  data, "No DataExtract Data")
                continue

            # Check if data has warehouse data
            # i.e.: Does it have valid ship import date
            if data.get("ship_datetime", "") == "" or\
               data.get("import_datetime", "") == "":
                order_year = dt.datetime.fromisoformat(
                    data["invoice_datetime"]).year
                order_month = dt.datetime.fromisoformat(
                    data["invoice_datetime"]).month
                date_stamp = f"{order_year}-{order_month}"

                if date_stamp not in fyi_dict:
                    fyi_dict.update({date_stamp: {}})

                update_error_dict(fyi_dict, order,
                                  data, "Missing Warehouse Data",
                                  ("invoice datetime"
                                   f"={data['invoice_datetime']}"))

                fyi_dict["Missing Warehouse Data"][date_stamp].update({
                    order: data["invoice_datetime"]
                    })
                continue

            # Check if country is valid
            if data["country"].lower() not in country_data.keys():
                update_error_dict(dirty_data, order,
                                  data, "Invalid Country", data["country"])
                continue

            ship_dt = dt.datetime.fromisoformat(data['ship_datetime'])
            if ship_dt.tzinfo is not None:
                ship_dt = convert_to_pl_time(ship_dt)
                data['ship_datetime'] = ship_dt.isoformat()

            # Check for delivery status.
            if data['delivery_datetime'] == '':
                data_string = data.get("country", "") + "," + \
                    data.get("import_datetime", "")

                update_error_dict(dirty_data, order,
                                  data, "No Delivery Date", data_string)

                data.update({"status": "wh_data_only"})
                clean_data.update({order: data})
                continue

            # Check if delivery time is after shipping time
            delivery_dt = dt.datetime.fromisoformat(data['delivery_datetime'])
            if delivery_dt.tzinfo is not None:
                delivery_dt = convert_to_pl_time(delivery_dt)
                data['delivery_datetime'] = delivery_dt.isoformat()

            if delivery_dt < ship_dt:
                detail_string = ""
                detail_string = \
                    f"Shipped: {ship_dt.isoformat()}, " + \
                    f"Delivered: {delivery_dt.isoformat()}"

                update_error_dict(dirty_data, order,
                                  data, "Delivered Before Shipped",
                                  detail_string)

                data.update({"status": "wh_data_only"})
                continue

            # Check if status exists in statuses dict
            if data['latest_status'] not in status_data.keys():
                update_error_dict(dirty_data, order, data,
                                  "Unknown Delivery Status",
                                  data['latest_status'])
                data.update({"status": "wh_data_only"})

                clean_data.update({order: data})
                continue

            # Check if status is a delivery status
            # Looking up a status returns the "is_valid" value
            if not status_data[data['latest_status']]:
                update_error_dict(dirty_data, order, data,
                                  "Package Not Delivered")

                data.update({"status": "wh_data_only"})
                clean_data.update({order: data})
                continue

            # Check if shipping estimate time exists
            ship_q = data['ship_q']
            country = data['country'].lower()
            if ship_q not in country_data[country]['carrier_slas']:
                detail_string = ""
                detail_string = f"Country: {country}, Ship-to: {ship_q}"
                update_error_dict(dirty_data, order, data,
                                  "Invalid Ship-to Code for Country",
                                  detail_string)

                data.update({"status": "wh_data_only"})
                clean_data.update({order: data})
                continue

            if data.get("status", True):
                data.update({"status": "clean"})
            clean_data.update({order: data})

        sorted_data.update({month: {}})
        sorted_data[month].update({"clean_data": clean_data})
        sorted_data[month].update({"dirty_data": dirty_data})
        sorted_data[month].update({"fyi_data": fyi_dict})

    return sorted_data


def update_error_dict(dict, order_num, order_data, err_code, detail=""):
    dict.update({order_num: order_data})
    if detail != "":
        err_code += ": " + detail
    dict[order_num].update({"error_code": err_code})
    return


def convert_to_pl_time(datetime_obj):
    """
    Sometimes we get our datetime objects in Z time, and need to convert them
    to local time. Poland is the only one who does this, though.
    """
    # If datetime string has a + or a Z in it, convert it to native PL time.

    pl_timezone = dt.timezone(dt.timedelta(hours=2))
    new_time = datetime_obj.astimezone(pl_timezone)
    new_time = new_time.replace(tzinfo=None)
    return new_time


def group_input_data(combined_dict):
    """
    Take the dictionary and orders sub-dictionaries files by import months
    """
    print("Grouping input data\n")
    ERROR_PATH = Path("./Program Data/Input Data Errors"
                      "/batch_errors/no_invoice_date.txt")
    return_dict = {}
    error_dict = {}

    for order_num, data in combined_dict.items():
        datetime_valid_flag = True
        try:
            import_datetime =\
                dt.datetime.fromisoformat(data.get("import_datetime", ""))
        except ValueError:
            datetime_valid_flag = False
        if "import_datetime" not in data or not datetime_valid_flag:
            error_dict.update({order_num: data})
            continue
        import_date = import_datetime
        date_str = f"{import_date.year}-{import_date.month}"

        if date_str not in return_dict:
            return_dict.update({date_str: {}})

        if order_num not in return_dict[date_str].keys():
            return_dict[date_str].update({order_num: data})

    with open(ERROR_PATH, mode="w", encoding="utf-8-sig") as file:
        file.write("Total number of orders without invoice"
                   f"date in input batch: {len(error_dict.keys())}\n")
        file.write("Orders without warehouse data from Dataextract"
                   "from the most recent run? Bad datetime format?")
        file.write("Orders:\n")
        for order_num in error_dict.keys():
            file.write(f"{order_num},")

    return return_dict


def update_program_data(sorted_data):
    """
    Read in the month's .json file, if it exists,
    and update it with the data from the input files
    Heirarchy of data:
    clean > dirty > fyi
    If data can move up a tier, move and delete the data in the previous tier
    If not, just update the one in the list
    """
    print("Updating program data files\n")
    DIR_STRING = "./Program Data/data_by_month/"

    for month, month_data in sorted_data.items():
        file_name = month + ".json"

        if not Path(DIR_STRING + file_name).is_file():
            with open(Path(DIR_STRING + file_name),
                      mode="w", encoding="utf-8-sig") as month_f:
                json.dump(month_data, month_f)
            continue

        with open(Path(DIR_STRING + file_name),
                  mode="r", encoding="utf-8-sig") as month_f:

            file_data = json.load(month_f)

        # Cleans
        for order_num, data in month_data["clean_data"].items():
            file_data["clean_data"].update({order_num: data})

            if order_num in file_data["dirty_data"]:
                del file_data["dirty_data"][order_num]
                continue

            if order_num in file_data["fyi_data"]:
                del file_data["fyi_data"][order_num]
                continue

        # Dirties
        for order_num, data in month_data["dirty_data"].items():
            if order_num in file_data["clean_data"]:
                continue

            if order_num in file_data["dirty_data"]:
                file_data["dirty_data"].update({order_num: data})
                continue

            if order_num in file_data["fyi_data"]:
                del file_data["fyi_data"][order_num]
                file_data["dirty_data"].update({order_num: data})
                continue

        # FYI's
        for order_num, data in month_data["fyi_data"].items():
            if order_num in file_data["clean_data"]:
                continue

            if order_num in file_data["dirty_data"]:
                continue

            if order_num in file_data["fyi_data"]:
                file_data["fyi_data"].update({order_num: data})
                continue

        with open(Path(DIR_STRING + file_name),
                  mode="w", encoding="utf-8-sig") as month_f:
            json.dump(file_data, month_f)


if __name__ == "__main__":
    prepare_program_data()
    print("Program Data Prepared")
