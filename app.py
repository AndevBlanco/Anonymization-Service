import pandas as pd
import numpy as np
import csv, json, os, bson, random
from pandas.api.types import is_integer_dtype, is_float_dtype
from dotenv import load_dotenv
from flask import Flask, render_template
from argparse import ArgumentParser
from faker import Faker
import csv, json, os, bson
import pandas as pd
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from termcolor import colored
import create_own_database
from kanonymity import generalize, suppress, is_k_anonymous

load_dotenv()

app = Flask(__name__)

parser = ArgumentParser()
parser.add_argument('-d', '--database', choices=['local', 'external'], help='Define if you want to use the local or external database')
parser.add_argument("-i", "--import", dest="import", required=False, help="Import the database")
parser.add_argument("-a", "--anonymization", dest="anonymization", required=False, help="Anonymization")
parser.add_argument("-ps", "--pseudonyms",choices=['random', 'secure'], dest="pseudonyms", default='secure', required=False, help="This attribuye will indicate if the pseudonyms are randoms or reversable and secure")
parser.add_argument("-m", "--mode",choices=['cli', 'web'], dest="mode", default='cli', required=False, help="This attribuye will indicate if the user wants to use the CLI or the WEB interface")

fake = Faker()

args = parser.parse_args()
print(args)


master_key = None

def read_database(database_path, use_local_database):
    print(colored("    >> Reading database","green"))
    if use_local_database:
        local_database_rows = []
        with open(database_path, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                local_database_rows.append(row)
        return local_database_rows
    else:
        df = pd.read_csv(database_path, sep=",")
        return df

    
def generalize_database(database, database_path, columns, use_local_database):
    if use_local_database:
        local_database_rows = database
        columns = [4,7, 8]
        for row in local_database_rows[1:]:
            for i in columns:
                old_value = row[i]
                try:
                    old_value = int(old_value)
                    row[i] = generalize_numeric_data(old_value)
                except ValueError:
                    # TODO: implement
                    # row[i] = generalize_categorical_data(old_value)
                    pass
        with open(database_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(local_database_rows)
    else:
        # TODO: implement with pandas
        df = database
        for column in df.columns[1:]:
            if is_integer_dtype(df[column]):
                df[column] = df[column].apply(lambda x : generalize_numeric_data(x))
            else:
                # TODO: implement
                # df[column] = df[column].apply(lambda x : generalize_categorical_data(x))
                pass
        df.to_csv(database_path, sep=',', index=False)
    print(colored("    >> Database generalized","green"))


def generalize_numeric_data(number):
    number_str = str(number)
    if len(number_str) >= 5:
        num_digits = len(number_str)
        generalize_count = num_digits // 2 if num_digits % 2 == 0 else (num_digits // 2) + 1
        generalize_indices = range(num_digits - generalize_count, num_digits)
        generalized_number = ""
        for i, digit in enumerate(number_str):
            if i in generalize_indices:
                generalized_number += "*"
            else:
                generalized_number += digit
        return generalized_number
    else:
        if number < 10:
            return f"0-10"
        lower_bound = (number // 10) * 10
        upper_bound = lower_bound + 10
        return f"[{lower_bound}-{upper_bound}]"


def generalize_categorical_data(value):
    # TODO: implement
    pass


# Get master key to decrypt or encrypt pseudonyms file
def get_master_key():
    if not(os.path.isfile("masterkey.key")):
        MASTER_KEY =  os.urandom(32)
        nonce = os.urandom(12)
        key = {"master": MASTER_KEY, "nonce": nonce}
        with open("masterkey.key", "wb") as archivo:
            archivo.write(bson.dumps(key))
    else:
        with open("masterkey.key", "rb") as archivo:
            file = bson.loads(archivo.read())
            MASTER_KEY = file["master"]
            nonce = file["nonce"]
    return MASTER_KEY, nonce
# This function pseudonym database.
## TO DO OTHER DATABASE, use columns parameter
def pseudonym_database(database, database_path, use_local_database):
    print(colored("    >> Pseudonymizing database","green"))
    pseudonyms ={}
    if use_local_database:
        local_database_rows = database
        for row in local_database_rows[1:]:
            old_value = row[1]
            row[1] = create_pseudonym(old_value,pseudonyms)
        with open(database_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(local_database_rows)
    else:
        # TODO: implement with pandas
        pass
    print(colored("    >> Database pseudonymized","green"))
    if "pseudonyms" in args and args.pseudonyms == "secure":
        key, nonce = get_master_key()
        cipher = Cipher(algorithm=algorithms.AES256(key), mode=modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        with open(database_path[0:len(database_path)-4]+"_pseudonyms.json", 'wb') as f:
            f.write(encryptor.update(json.dumps(pseudonyms).encode('utf-8')))        
    print(colored("    >> Created pseudonym dictionary file","green"))

# Generar un pseudónimo para un nombre
def create_pseudonym(name,pseudonyms):
    pseudonym = fake.first_name()
    while pseudonym ==name or  pseudonym[0] != name[0]:
        pseudonym = fake.first_name()
    pseudonyms[pseudonym] = name
    return pseudonym

def get_secured_id_from_pseudonym(database_path, pseudonym):
    key, nonce = get_master_key()
    cipher = Cipher(algorithm=algorithms.AES256(key), mode=modes.GCM(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    with open(database_path[0:len(database_path)-4]+"_pseudonyms.json", 'rb') as f:
        decrypted = decryptor.update(f.read()).decode('utf-8')   
        pseudonyms = json.loads(decrypted)
    return pseudonyms[pseudonym]

def is_k_anonymous(group, k):
    return len(group) >= k

def kanonymization(database_path:str, use_local_database:bool):
    if use_local_database:
        data = pd.read_csv(database_path, sep=",")
        # List of sensitive columns to be anonymized
        sensitive_attributes = ['Age', 'Gender']

        k = 2
        grouped_data = data.groupby(sensitive_attributes)

        # Data anonymization
        anon_data = pd.DataFrame(columns=data.columns)
        for group_name, group in grouped_data:
            if is_k_anonymous(group, k):
                anon_group = pd.DataFrame(columns=data.columns)
                for column in group.columns:
                    if column in sensitive_attributes:
                        anon_group[column] = generalize(group[column], 1)
                    else:
                        anon_group[column] = group[column]
                anon_data = pd.concat([anon_data, anon_group])
            else:
                anon_group = pd.DataFrame(columns=data.columns)
                for column in group.columns:
                    anon_group[column] = suppress(group[column])
                anon_data = pd.concat([anon_data, anon_group])

        # pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        print(anon_data)

    else:
        print("...")

@app.route('/')
def index():
    return render_template('index.html')


def perturb_database(database_path:str, use_local_database:bool):
    if use_local_database:
        numeric_columns = [4]
        # TODO: implement
        pass
    else:
        numeric_columns = ["duration", "amount", "age"]
        df = pd.read_csv(database_path, sep=",")
        for column in numeric_columns:
            df = add_noise(df=df, column=column)
            df = permutate_column(df=df, column=column)
        df.to_csv(database_path, sep=',', index=False)


def add_noise(df:pd.DataFrame, column:str, std_percentage:float=0.3, round_decimals:int=2) -> pd.DataFrame:
    # first get standard deviation for this column
    std = df[column].std()
    # only use a certain percentage of standard deviation
    std *= std_percentage
    # then use this as the interval to add the random noise
    if is_integer_dtype(df[column]):
        df[column] = df[column].map(lambda x : x + random.randint(-round(std), round(std)))
    elif is_float_dtype(df[column]):
        df[column] = df[column].map(lambda x : round(x + random.uniform(-std, std), round_decimals))
    else:
        raise ValueError(f"dtype {df[column].dtype} not supported")
    return df

def permutate_column(df:pd.DataFrame, column:str, perm_percentage:float=0.3):
    series = df[column]
    # Get the number of values to swap
    n = int(len(series) * perm_percentage)
    # Generate random indices to swap
    swap_indices = np.random.choice(len(series), size=n, replace=False)
    # Shuffle the values at the swap indices
    swapped_values = series.iloc[swap_indices].sample(frac=1).values
    # Create a copy of the original series
    new_series = series.copy()
    # Swap the values at the swap indices
    new_series.iloc[swap_indices] = swapped_values
    df[column] = new_series
    return df


def list_current_databases(use_local_database, databases_folder):
    if os.path.isdir(databases_folder):
        databases = os.scandir(databases_folder)
        if databases:
            print(colored(f"{'Local' if use_local_database else 'External'} databases:","yellow"))
            for file in databases:
                if file.name.endswith(".csv"):
                    print(colored(f"- {file.name}", "yellow"))

def _use_local_database(database_type) -> bool:
    if database_type == 'l' or database_type == 'local':
        return True
    elif database_type == 'e' or database_type == 'external':
        return False
    else:
        raise ValueError(f"Unknown database type: {database_type}")

def _get_databases_folder(use_local_database):
    return "local-databases" if use_local_database else "external-databases"

def _list_databases_and_read_new_database(use_local_database, databases_folder):
    # List current databases
    list_current_databases(use_local_database, databases_folder)
    database_name = input(colored("Introduce a database to be anonymized\n", color="yellow"))
    database_path = f"{databases_folder}/{database_name}"
    database = read_database(database_path, use_local_database)
    return database_path, database

def main():
    if args.mode == "cli":
        # Get database type
        database_type = input(colored("Do you want to use a local or external database? (l/e)\n", color='yellow'))
        use_local_database = _use_local_database(database_type)
        databases_folder = _get_databases_folder(use_local_database)
        print(colored(f"Using {'local' if use_local_database else 'external'} database", "yellow"))
        # Create new database?
        create_new = input(colored("Do you want to create a new database? (y/n)\n", color='yellow'))
        if create_new == "y" or create_new == "yes":
            new_database_name = input(colored("Please, introduce the name of the new database\n", color='yellow'))
            create_own_database.create_database(new_database_name, use_local_database)
        
        database_path, database = _list_databases_and_read_new_database(use_local_database, databases_folder)
            
        while True:
            option = input(colored(
                """
                Introduce an option to proceed with the anonymization:
                1. Pseudonymize the database
                2. Get ID from pseudonym (after option 1)
                3. Generalize database.
                4. Perturb the database.
                5. K anonymize the database.
                6. Change database
                7. Change to web interface
                8. To exit the app, introduce either 'exit' or 6
                """,
                "yellow"))
            if option == "1":
                pseudonym_database(database, database_path=database_path, use_local_database=use_local_database)
            elif option == "2":
                pseudonym = input(colored("Introduce a pseudonym to translate\n","yellow"))
                print(colored(f"The ID associated with pseudonym {pseudonym} is: {get_secured_id_from_pseudonym(database_path, pseudonym)}","blue"))
            elif option == "3":
                generalize_database(database, database_path=database_path, columns=None, use_local_database=use_local_database)
            elif option == "4":
                perturb_database(database_path=database_path, use_local_database=use_local_database)
            elif option == "5":
                kanonymization(database_path=database_path, use_local_database=use_local_database)
            elif option == "6":
                database_path, database = _list_databases_and_read_new_database(use_local_database, databases_folder)
            elif option == "7":
                app.run()
            elif option == "8" or option == "exit":
                print(colored("Leaving the app. See you soon :)","magenta"))
                break
            else:
                print(colored("Invalid option","red"))
            print(colored('*'*100, "blue"))
    else:
        app.run()

if __name__ == '__main__':
    main()
