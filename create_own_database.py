import os
import csv
import shutil
from faker import Faker
import random
from termcolor import colored
import pandas as pd


def create_database(database_name: str, use_local_database: bool):
    if use_local_database:
        create_local_database(database_name)
    else:
        create_external_database(database_name)
    
def create_external_database(database_name: str):
    external_databases_folder = "external-databases"
    os.makedirs(name=external_databases_folder, exist_ok=True)
    external_database = f"external-data/german.data"
    column_names = ["chk_acct", "duration", "credit_history", "purpose", "amount", "saving_acct", "present_emp", "installment_rate", "sex", "other_debtor", "present_resid", "property", "age", "other_install", "housing", "n_credits", "job", "n_people", "telephone", "foreign", "response"]

    data = pd.read_csv(external_database, sep=" ", names=column_names)
    
    relevant_numerical_columns = ["duration", "amount", "age"]
    relevant_categorical_columns = ["purpose", "credit_history"]
    relevant_columns = relevant_numerical_columns + relevant_categorical_columns
    data = data[relevant_columns]

    value_mapping = {
        # purpose
        "A40" : "car (new)",
        "A41" : "car (used)",
        "A42" : "furniture/equipment",
        "A43" : "radio/television",
        "A44" : "domestic appliances",
        "A45" : "repairs",
        "A46" : "education",
        "A48" : "retraining",
        "A49" : "business",
        "A410" : "others",
        # credit history
        "A30" : "no credits taken/ all credits paid back duly",
        "A31" : "all credits at this bank paid back duly",
        "A32" : "existing credits paid back duly till now",
        "A33" : "delay in paying off in the past",
        "A34" : "critical account/ other credits existing (not at this bank)"
    }
    for col in relevant_categorical_columns:
        data[col] = data[col].map(value_mapping).fillna(data[col])

    data = data.rename_axis('id').reset_index()
    data['id'] += 1
    data.to_csv(f"{external_databases_folder}/{database_name}", sep=',', index=False)
    shutil.copyfile(f"{external_databases_folder}/{database_name}", f"{external_databases_folder}/original_{database_name}")
    print(colored(f"External database created with {len(data.columns)} columns: {data.columns}", "green"))


def create_local_database(database_name: str):
    local_databases_folder = "local-databases"
    os.makedirs(name=local_databases_folder, exist_ok=True)
    dataset_length = 200
    rows = []
    print(colored("Creating own database", "green"))
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
    
    shutil.copyfile(f"{local_databases_folder}/{database_name}", f"{local_databases_folder}/original_{database_name}")
    print(colored(f"Local database created with {len(columns)} columns: {columns}", "green"))


if __name__ == '__main__':
    # database_name = "db.csv"
    # database_type = "local"
    database_name = "db.csv"
    database_type = "external"
    create_database(database_name, database_type)
