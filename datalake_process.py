import json
import argparse

def update_json(original_json, new_data):
    """ Updates the VMware IP list in the original JSON with new data. """

    manufacturer_name = str(new_data.get("manufacturer_name", "")).strip().lower()
    manufacturer_url = str(new_data.get("manufacturer_url", "")).strip()

    # Check if manufacturer is "vmware" and the "VmWare" key exists in the original JSON
    if manufacturer_name == "vmware" and "VmWare" in original_json:
        if "VMwareIP" in original_json["VmWare"]:
            # Avoid duplicates
            if manufacturer_url not in original_json["VmWare"]["VMwareIP"]:
                original_json["VmWare"]["VMwareIP"].append(manufacturer_url)
        else:
            # If "VMwareIP" key doesn't exist, create it
            original_json["VmWare"]["VMwareIP"] = [manufacturer_url]

    return original_json

def main():
    """ Parses input files, updates JSON, and overwrites the original file. """

    parser = argparse.ArgumentParser(description="Update JSON data and overwrite the original file.")
    parser.add_argument("new_data_file", help="Path to the JSON file containing new data.")
    parser.add_argument("config_file", help="Path to the JSON file to be updated (will be overwritten).")

    args = parser.parse_args()

    try:
        with open(args.new_data_file, "r") as file:
            new_data = json.load(file)

        with open(args.config_file, "r") as file:
            original_json = json.load(file)

    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading JSON files: {e}")
        return

    updated_json = update_json(original_json, new_data)

    try:
        # Overwrite the existing file
        with open(args.config_file, "w") as output_file:
            json.dump(updated_json, output_file, indent=4)
        print(f"Updated JSON has been saved to {args.config_file}")
    except IOError as e:
        print(f"Error saving the output file: {e}")

if __name__ == "__main__":
    main()
