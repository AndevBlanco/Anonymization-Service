import os
import csv
from faker import Faker
import random
from termcolor import colored


def create_database(database_name: str, database_type: str):
    if database_type == 'l' or database_type == 'local':
        create_local_database(database_name)
    elif database_type == 'e' or database_type == 'external':
        create_external_database(database_name)
    else:
        raise ValueError(f"Unknown database type: {database_type}")

def create_external_database(database_name: str):
    pass

def create_local_database(database_name: str):
    dataset_length = 200
    rows = []
    print(colored("Creating own database", "green"))
    local_databases_path = "local-databases"
    os.makedirs(name=local_databases_path, exist_ok=True)
    with open(f"{local_databases_path}/{database_name}", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        columns = ['id', 'name', 'job','Gender', 'Age', 'email', 'password', 'Mobile phone number', 'zipcode', 'national identifier', 'security identifier']
        writer.writerow(columns)
        fake = Faker()
        for i in range(1, dataset_length):
            row = [
                    i,
                    fake.name(),
                    fake.job(),
                    fake.random_element(elements=('Male', 'Female')),
                    random.randint(20,60),
                    fake.email(),
                    fake.password(),
                    str(random.randint(600000000, 999999999)),
                    fake.postcode(),
                    fake.ssn(),
                    fake.uuid4()
                ]
            rows.append(row)
        # Guardar los datos en un archivo CSV
        writer = csv.writer(f)
        writer.writerows(rows)
    print(colored(f"Database created with {len(columns)} columns: {columns}", "green"))


if __name__ == '__main__':
    database_name = "database.csv"
    database_type = "local"
    create_database(database_name, database_type)
