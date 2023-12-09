import json
import logging

FILENAME = "data.json"
GROUPS = "groups.json"


def load_data_groups():
    try:
        with open(GROUPS, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


# Function to save JSON data to a file
def save_data_groups(data):
    with open(GROUPS, 'w') as file:
        json.dump(data, file, indent=2)


# Function to create a new record in the JSON data
def create_record_groups(name, group_id):
    data = load_data_groups()
    data.append(
        {
            "name": name,
            'group_id': group_id
        }
    )
    return data


def delete_object_by_name_groups(id_to_delete):
    data_list = load_data_groups()
    updated_data = [item for item in data_list if item["name"] != id_to_delete]
    save_data_groups(updated_data)


def get_object_by_name_groups(name):
    data_list = load_data_groups()
    for item in data_list:
        if item['name'] == name:
            return item['group_id']


def get_groups_having_posts() -> list[str]:
    posts = load_data()
    selected_groups = []
    for post in posts:
        selected_groups.append(post['group_id'])
    return list(set(selected_groups))


def get_groups_name() -> list[str]:
    groups = get_groups_having_posts()
    db_groups = load_data_groups()
    groups_name_list = []
    for group in db_groups:
        group_id = group['group_id']
        if group_id in groups:
            groups_name_list.append(group['name'])
    return groups_name_list


def load_data():
    try:
        with open(FILENAME, 'r') as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def load_posts_using_group_id(group_id):
    posts = load_data()
    selected_posts = []
    for post in posts:
        if post['group_id'] == group_id:
            selected_posts.append(post)
    return selected_posts


def get_group_posts(group_id: str):
    posts = load_data()
    selected_posts = []
    for post in posts:
        if post['group_id'] == group_id:
            selected_posts.append(post)
    return selected_posts


# Function to save JSON data to a file
def save_data(data):
    with open(FILENAME, 'w') as file:
        json.dump(data, file, indent=2)


# Function to create a new record in the JSON data
def create_record(record, scheduled_time, utc, group_id):
    data = load_data()
    json_data = json.loads(record)
    data.append(
        {
            "id": json_data['message_id'],
            "scheduled": scheduled_time,
            "post": json_data,
            'utc': utc,
            "group_id": group_id
        }
    )
    return data


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
