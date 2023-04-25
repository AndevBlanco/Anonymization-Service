from dotenv import load_dotenv
from flask import Flask, render_template
from argparse import ArgumentParser
from faker import Faker
import csv, json, os,bson, random
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import create_own_database
from termcolor import colored

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

rows = []
rows_own_database = []
own_database_name = "database.csv"

master_key = None

def read_database(database_name, database_path):
    print(colored("    >> Reading database","green"))
    try:
        with open(database_path, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if database_name == own_database_name:
                    rows_own_database.append(row)
                else:
                    rows.append(row)
        return True
    except Exception as e:
        print(colored("    >> Error reading database","red"))
        print(e)

        return False
    
def generalize_database(database_name, database_path, columns):
    if database_name == own_database_name:
        columns = [4,7, 8]
        for row in rows_own_database[1:]:
            for i in columns:
                old_value = row[i]
                try:
                    old_value = int(old_value)
                    row[i] = generalize_numeric_data(old_value)
                except ValueError:
                    row[i] = generalize_categorical_data(old_value)
        with open(database_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows_own_database)
    else:
        for row in rows:
            for i in columns:
                old_value = row[i]
                try:
                    old_value = int(old_value)
                    row[i] = generalize_numeric_data(old_value)
                except ValueError:
                    row[i] = generalize_categorical_data(old_value)
        with open(database_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
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
    print(value)


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
def pseudonym_database(database_name, database_path, columns):
    print(colored("    >> Pseudonymizing database","green"))
    pseudonyms ={}
    if database_name == own_database_name:
        for row in rows_own_database[1:]:
            old_value = row[1]
            row[1] = create_pseudonym(old_value,pseudonyms)
        with open(database_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows_own_database)
    else:
        for row in rows:
            old_value = row[1]
            row[1] = create_pseudonym(old_value,pseudonyms)
        with open(database_path, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
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

@app.route('/')
def index():
    return render_template('index.html')

def list_current_databases(use_local_database, database_path):
    if os.path.isdir(database_path):
        databases = os.scandir(database_path)
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
        read = read_database(database_name, database_path)
        return database_name, database_path, read

if __name__ == '__main__':
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
            create_own_database.create_database(new_database_name, database_type)
        
        database_name, database_path, read = _list_databases_and_read_new_database(use_local_database, databases_folder)
        while not read:
            database_name, database_path, read = _list_databases_and_read_new_database(use_local_database, databases_folder)
            
        while True:  
            option = input(colored("Introduce an option to proceed with the anonymization: \n 1. Pseudonymize the database\n 2. Get ID from pseudonym (after option 1)\n 3. Generalize database.\n 4. Change database \n 5. Change to web interface \n 6. To exit the app, introduce either 'exit' or 6\n","yellow"))
            if option == "1":
                pseudonym_database(database_name, database_path, None)
            elif option == "2":
                pseudonym = input(colored("Introduce a pseudonym to translate\n","yellow"))
                print(colored(f"The ID associated with pseudonym {pseudonym} is: {get_secured_id_from_pseudonym(database_path, pseudonym)}","blue"))
            elif option == "3":
                generalize_database(database_name, database_path, None)
            elif option == "4":
                database_name, database_path, read = _list_databases_and_read_new_database(use_local_database, databases_folder)
                while not read:
                    database_name, database_path, read = _list_databases_and_read_new_database(use_local_database, databases_folder)
            elif option == "5":
                app.run()
            elif option == "6" or option == "exit":
                print(colored("Leaving the app. See you soon :)","magenta"))
                break
            else:
                print(colored("Invalid option","red"))
            print(colored('*'*100, "blue"))
    else:
        app.run()