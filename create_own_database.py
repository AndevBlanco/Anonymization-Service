import os
import csv
from faker import Faker
import random
from termcolor import colored
import pandas as pd


def create_database(database_name: str, database_type: str):
    if database_type == 'l' or database_type == 'local':
        create_local_database(database_name)
    elif database_type == 'e' or database_type == 'external':
        create_external_database(database_name)
    else:
        raise ValueError(f"Unknown database type: {database_type}")

def create_external_database(database_name: str):
    column_names = ["chk_acct", "duration", "credit_history", "purpose", "amount", "saving_acct", "present_emp", "installment_rate", "sex", "other_debtor",                   "present_resid", "property", "age", "other_install", "housing", "n_credits", "job", "n_people", "telephone", "foreign", "response"]
    print(type(column_names))
    data = pd.read_csv(f"external-data/{database_name}", sep=" ", names=column_names)
    
    relevant_numerical_columns = ["duration", "amount", "age"]
    relevant_categorical_columns = ["sex", "purpose", "credit_history", "housing"]
    relevant_columns = relevant_numerical_columns + relevant_categorical_columns
    data = data[relevant_columns]
    print(data)

    value_mapping = {
        # purpose
        "A40" : "car (new)",
        "A41" : "car (used)",
        "A42" : "furniture/equipment",
        "A43" : "radio/television",
        "A44" : "domestic appliances",
        "A45" : "repairs",
        "A46" : "education",
        "A47" : "(vacation - does not exist?)",
        "A48" : "retraining",
        "A49" : "business",
        "A410" : "others",
        # credit history
        "A30" : "no credits taken/ all credits paid back duly",
        "A31" : "all credits at this bank paid back duly",
        "A32" : "existing credits paid back duly till now",
        "A33" : "delay in paying off in the past",
        "A34" : "critical account/ other credits existing (not at this bank)",
        # housing
        "A151" : "rent",
        "A152" : "own",
        "A153" : "for free"
    }
    for col in relevant_categorical_columns:
        data[col] = data[col].map(value_mapping).fillna(data[col])
    print(data)


def create_local_database(database_name: str):
    dataset_length = 200
    rows = []
    print(colored("Creating own database", "green"))
    local_databases_folder = "local-databases"
    os.makedirs(name=local_databases_folder, exist_ok=True)
    with open(f"{local_databases_folder}/{database_name}", 'w', newline='', encoding='utf-8') as f:
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
    # database_name = "database.csv"
    # database_type = "local"
    database_name = "german.data"
    database_type = "external"
    create_database(database_name, database_type)
