import csv
from faker import Faker
import random
from termcolor import colored


def create_database(database_name):
    rows = []
    print(colored("Creating own database", "green"))
    with open(database_name, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        columns = ['id', 'name', 'job','Gender', 'Age', 'email', 'password', 'Mobile phone number', 'zipcode', 'national identifier', 'security identifier']
        writer.writerow(columns)
        fake = Faker()
        for i in range(1, 1000):
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
    create_database(database_name)
