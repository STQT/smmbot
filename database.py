import json
import logging

FILENAME = "data.json"


def convert_boolean_values(obj):
    if isinstance(obj, dict):
        return {key: convert_boolean_values(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_boolean_values(element) for element in obj]
    elif obj.lower() == "false":
        return False
    elif obj.lower() == "true":
        return True
    else:
        return obj


# Function to load JSON data from a file
def load_data():
    try:
        with open(FILENAME, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


# Function to save JSON data to a file
def save_data(data):
    with open(FILENAME, 'w') as file:
        json.dump(data, file, indent=2)


# Function to create a new record in the JSON data
def create_record(record, scheduled_time, utc):
    data = load_data()
    json_data = json.loads(record)
    logging.info(json_data)
    data.append(
        {
            "id": json_data['message_id'],
            "scheduled": scheduled_time,
            "post": json_data,
            'utc': utc
        }
    )
    return data


# Function to read data from the JSON file
def read_data():
    data = load_data()
    if data is not None:
        for record in data:
            print(record)
    else:
        print("File not found or empty.")


# Function to update a record in the JSON data
def update_record(data, record_id, updated_data):
    for record in data:
        if record.get('id') == record_id:
            record.update(updated_data)
            break


def delete_object_by_id(id_to_delete):
    data_list = load_data()
    # Use a list comprehension to filter out the object with the specified ID
    updated_data = [item for item in data_list if item["id"] != id_to_delete]
    save_data(updated_data)

# # Example usage
# filename = 'data.json'
#
# # Creating initial data or loading existing data
# # initial_data = [{'id': 1, 'name': 'John'}, {'id': 2, 'name': 'Jane'}]
# # save_data(initial_data, filename)
#
# # Reading data
# print("Initial Data:")
# read_data(filename)
#
# # Creating a new record
# new_record = {'id': 3, 'name': 'Bob'}
# initial_data = load_data(filename)
# create_record(initial_data, new_record)
# save_data(initial_data, filename)
#
# # Reading data after creating a new record
# print("\nData after creating a new record:")
# read_data(filename)
#
# # Updating a record
# update_record(initial_data, 1, {'name': 'Updated John'})
# save_data(initial_data, filename)
#
# # Reading data after updating a record
# print("\nData after updating a record:")
# read_data(filename)
#
# # Deleting a record
# delete_record(initial_data, 2)
# save_data(initial_data, filename)
#
# # Reading data after deleting a record
# print("\nData after deleting a record:")
# read_data(filename)
