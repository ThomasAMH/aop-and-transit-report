from pathlib import Path
import json


def main():
    """
    Extract a list of reasons from each order in combined_temp that are NOT
    in the statuses.csv config file and write them to a file with a count
    for how often they appear
    """

    data_path = Path("./Program Data/combined_files/combined-unfiltered.json")
    with open(data_path, mode="r", encoding="utf-8-sig", newline='') as file:
        data_dict = json.load(file)

    status_dict = {}
    for data in data_dict.values():
        if 'latest_status' in data.keys():
            if data['latest_status'] in status_dict:
                status_dict[data['latest_status']] += 1
            else:
                status_dict.update({data['latest_status']: 1})
    with open(Path("./Program Data/Input Data Errors/unseen status.csv"),
              mode="w") as txt_file:
        for status, count in status_dict.items():
            txt_file.write(status + "," + str(count) + "\n")


if __name__ == "__main__":
    main()
    print("Execution Complete")
