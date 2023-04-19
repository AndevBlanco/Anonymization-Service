import csv
from faker import Faker


rows = []
def create_database():
    print("Creating own database")
    with open('database.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        columns = ['id', 'name', 'job','Gender', 'Birthdate', 'email', 'password', 'Mobile phone number', 'address', 'national identifier', 'security identifier']
        writer.writerow(columns)
        fake = Faker()
        for i in range(1, 1000):
            row = [
                    i,
                    fake.name(),
                    fake.job(),
                    fake.random_element(elements=('Male', 'Female')),
                     fake.date_between(start_date='-60y', end_date='-21y'),
                    fake.email(),
                    fake.password(),
                    fake.phone_number(),
                    fake.address(),
                    fake.ssn(),
                    fake.uuid4()
                ]
            rows.append(row)
        # Guardar los datos en un archivo CSV
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"Database created with {len(columns)} columns: {columns}")


if __name__ == '__main__':
    create_database()
