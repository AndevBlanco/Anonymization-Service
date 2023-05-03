import pandas as pd
import numpy as np
import csv, json, os, bson, random
from pandas.api.types import is_numeric_dtype, is_integer_dtype, is_float_dtype
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
args = parser.parse_args()
print(args)

fake = Faker()

master_key = None

local_db_identifiers = ["name", "email", "Mobile phone number", "national identifier", "security identifier"]

def read_database(database_path):
    print(colored("    >> Reading database","green"))
    df = pd.read_csv(database_path, sep=",")
    return df

def write_database(df, database_path):
    df.to_csv(database_path, sep=',', index=False)


def remove_identifiers_local_db(database_path, use_local_database):
    if not use_local_database:
        print(colored("External database does not contain any identifiers.", "red"))
        return
    df = read_database(database_path)
    columns_without_identifiers = [x for x in df.columns if x not in local_db_identifiers]
    df = df[columns_without_identifiers]
    write_database(df, database_path)

    
def generalize_database(database_path):
    df = read_database(database_path)
    for column in df.columns[1:]:
        if is_integer_dtype(df[column]):
            df[column] = df[column].apply(lambda x : generalize_numeric_data(x))
        else:
            # TODO: implement
            # df[column] = df[column].apply(lambda x : generalize_categorical_data(x))
            pass
    write_database(df, database_path)
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

def _input_identifier_columns(database_path: str, anonymize_data):
    df = read_database(database_path)
    # Get remaining identifier columns
    remaining_identifier_columns = [x for x in local_db_identifiers if x in df.columns]
    if not remaining_identifier_columns:
        print(colored("There are no remaining identifiers in the database", "blue"))
        return None, None, None
    # Choose the columns to be anonymized
    if anonymize_data:
        print(colored("""Choose the identifier columns that should be (de)anonymized. Please input numbers seperated by spaces ("0 2 3"):""", "yellow"))
        for index, identifier_column in enumerate(remaining_identifier_columns):
            print(colored(f"{index}. {identifier_column}", "yellow"))
        identifier_input = input()
        selected_identifier_column_indices = sorted([int(x) for x in identifier_input.split(" ")])
    else:
        # Deanonymize a single pseudonym
        print(colored("""Choose the identifier column that should be deanonymized. Please input a single number:""", "yellow"))
        for index, identifier_column in enumerate(remaining_identifier_columns):
            print(colored(f"{index}. {identifier_column}", "yellow"))
        identifier_input = input()
        selected_identifier_column_indices = [int(identifier_input)]
    unknown_indices = list(set(selected_identifier_column_indices).difference(range(len(remaining_identifier_columns))))
    if unknown_indices:
        print(colored("You selected a number outside the range of options. Please try again.", "red"))
        return None, None, None
    selected_identifier_columns = [remaining_identifier_columns[x] for x in selected_identifier_column_indices]
    return df, remaining_identifier_columns, selected_identifier_columns

# This function pseudonym database.
def pseudonym_database(database_path, use_local_database):
    if not use_local_database:
        print(colored("For external database, there are no identifiers", "blue"))
        return
    
    df, remaining_identifier_columns, selected_identifier_columns = _input_identifier_columns(database_path, anonymize_data=True)
    if not remaining_identifier_columns:
        return
    
    pseudonymize_method = input(colored("""Type in the method to pseudonymize the data:
        1. Hash function
        2. Document-randomized pseudonymisation\n""", "yellow"))
    if pseudonymize_method != '1' and pseudonymize_method != '2':
        print(colored("Please select one of the pseudonymization method options", "red"))
        return
    
    print(colored("    >> Pseudonymizing database","green"))
    pseudonyms = {}
    for column in selected_identifier_columns:
        column_pseudonyms = {}
        df[column] = df[column].apply(lambda x : create_pseudonym(x, column_pseudonyms, column, pseudonymize_method))
        pseudonyms[column] = column_pseudonyms
    
    write_database(df, database_path)
    print(colored("    >> Database pseudonymized","green"))
    if "pseudonyms" in args and args.pseudonyms == "secure":
        key, nonce = get_master_key()
        cipher = Cipher(algorithm=algorithms.AES256(key), mode=modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        with open(database_path[0:len(database_path)-4]+"_pseudonyms.json", 'wb') as f:
            f.write(encryptor.update(json.dumps(pseudonyms).encode('utf-8')))        
    print(colored("    >> Created pseudonym dictionary file","green"))


def reverse_pseudonym_database(database_path, use_local_database):
    if not use_local_database:
        print(colored("For external database, there are no identifiers", "green"))
        return
    if not os.path.isfile(database_path[0:len(database_path)-4]+"_pseudonyms.json"):
        print(colored(f"There is no dictionary of pseudonyms for local database '{database_path.split('/')[1]}'. Please pseudonymize your database before.",
                      "red"))
        return
    
    _, remaining_identifier_columns, selected_identifier_columns = _input_identifier_columns(database_path, anonymize_data=False)
    if not remaining_identifier_columns:
        return
    
    id_column = selected_identifier_columns[0]

    pseudonym = input(colored(f"You selected column {id_column}. Introduce a pseudonym to translate:\n","yellow"))
    secured_id = get_secured_id_from_pseudonym(database_path, pseudonym, id_column)
    if secured_id:
        print(colored(f"The ID associated with pseudonym {pseudonym} is: {secured_id}","blue"))
    else:
        print(colored(f"There is no ID associated with pseudonym {pseudonym}.","red"))

# Generar un pseudónimo para un nombre
def create_pseudonym(to_be_pseudonymized_data, pseudonyms, column_name, pseudonymize_method):
    if pseudonymize_method == '1':
        # hash
        pseudonym = hash(to_be_pseudonymized_data)
    elif pseudonymize_method == '2':
        # document randomized
        if column_name == "name":
            pseudonym = fake.unique.first_name()
        elif column_name == "email":
            pseudonym = fake.unique.email()
        elif column_name == "Mobile phone number":
            pseudonym = fake.unique.phone_number()
        elif column_name == "email":
            pseudonym = fake.unique.email()
        elif column_name == "national identifier":
            pseudonym = fake.unique.ssn()
        elif column_name == "security identifier":
            pseudonym = fake.unique.uuid4()
        else:
            raise ValueError(f"column name '{column_name}' is not viable here.")
    else:
        raise ValueError(f"Unknown pseudonymization method '{pseudonymize_method}'")

    pseudonyms[pseudonym] = to_be_pseudonymized_data
    return pseudonym

def get_secured_id_from_pseudonym(database_path, pseudonym, id_column):
    key, nonce = get_master_key()
    cipher = Cipher(algorithm=algorithms.AES256(key), mode=modes.GCM(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    with open(database_path[0:len(database_path)-4]+"_pseudonyms.json", 'rb') as f:
        decrypted = decryptor.update(f.read()).decode('utf-8')   
        pseudonyms = json.loads(decrypted)
    return pseudonyms.get(id_column).get(pseudonym)

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
        anon_data.to_csv("database_kanomymized.csv", index=False)

    else:
        print(colored("For external database, there are no k anonymity", "blue"))

@app.route('/')
def index():
    files = []
    if os.path.isdir('./local-databases'):
        files = [f for f in os.listdir('./local-databases') if not f.startswith('original_')]
    if os.path.isdir('./external-databases'):
        files += [f for f in os.listdir('./external-databases') if not f.startswith('original_')]
    
    df = pd.read_csv('./original_database.csv')
    html_table = df.to_html(classes="table table-striped")
    return render_template('index.html', table=html_table, files=files)


def perturb_database(database_path:str):
    read_database(database_path)
    numeric_columns = [column_name for column_name in df.columns if is_numeric_dtype(df[column_name]) and column_name != "id"]
    print(numeric_columns)
    for column in numeric_columns:
        df = add_noise(df=df, column=column)
        df = permutate_column(df=df, column=column)
    write_database(df, database_path)


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
    database_selected = False
    while not database_selected:
        list_current_databases(use_local_database, databases_folder)
        database_name = input(colored("Introduce a database to be anonymized\n", color="yellow"))
        database_path = f"{databases_folder}/{database_name}"
        database_path_original = f"{databases_folder}/original_{database_name}"
        if os.path.isfile(database_path):
            database_selected = True
        else:
            print(colored(f"Could not find database with name '{database_name}'", "red"))
    return database_path, database_path_original

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
        
        database_path, database_path_original = _list_databases_and_read_new_database(use_local_database, databases_folder)
            
        while True:
            option = input(colored(
                """
                Introduce an option to proceed with the anonymization:
                1. Pseudonymize the database
                2. Get ID from pseudonym (after option 1)
                3. Remove identifiers (local database only)
                4. Generalize database.
                5. Perturb the database.
                6. K anonymize the database.
                7. Change database
                8. Change to web interface
                9. To exit the app, introduce either 'exit' or 9
                """,
                "yellow"))
            if option == "1":
                pseudonym_database(database_path, use_local_database=use_local_database)
            elif option == "2":
                reverse_pseudonym_database(database_path, use_local_database)
            elif option == "3":
                remove_identifiers_local_db(database_path, use_local_database)
            elif option == "4":
                generalize_database(database_path)
            elif option == "5":
                database_path, database_path_original = _list_databases_and_read_new_database(use_local_database, databases_folder)
                perturb_database(database_path)
            elif option == "6":
                kanonymization(database_path=database_path, use_local_database=use_local_database)
            elif option == "7":
                database_path, database_path_original = _list_databases_and_read_new_database(use_local_database, databases_folder)
            elif option == "8":
                app.run()
            elif option == "9" or option == "exit":
                print(colored("Leaving the app. See you soon :)","magenta"))
                break
            else:
                print(colored("Invalid option","red"))
            print(colored('*'*100, "blue"))
    else:
        app.run()

if __name__ == '__main__':
    main()
