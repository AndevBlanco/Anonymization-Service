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
parser.add_argument("-i", "--import", dest="import", required=False, help="Import the database")
parser.add_argument("-a", "--anonymization", dest="anonymization", required=False, help="Anonymization")
parser.add_argument("-ps", "--pseudonyms",choices=['random', 'secure'], dest="pseudonyms", default='secure', required=False, help="This attribuye will indicate if the pseudonyms are randoms or reversable and secure")
parser.add_argument("-m", "--mode",choices=['cli', 'web'], dest="mode", default='cli', required=False, help="This attribuye will indicate if the user wants to use the CLI or the WEB interface")


fake = Faker()

args = vars(parser.parse_args())
print(args)

rows = []
rowsOwnDatabase = []
ownDatabaseName = "database.csv"

master_key = None

def readDatabase(database):
    print(colored("    >> Reading database","green"))
    try:
        with open(database, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if database == ownDatabaseName:
                    rowsOwnDatabase.append(row)
                else:
                    rows.append(row)
        return True
    except:
        print(colored("    >> Error reading database","red"))
        return False
    
def generalizeDatabase(database, columns):
    if database == ownDatabaseName:
        columns = [4,7, 8]
        for row in rowsOwnDatabase[1:]:
            for i in columns:
                oldValue = row[i]
                try:
                    oldValue = int(oldValue)
                    row[i] = generalizeNumericData(oldValue)
                except ValueError:
                    row[i] = generalizeCategoricalData(oldValue)
        with open(database, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rowsOwnDatabase)
    else:
        for row in rows:
            for i in columns:
                oldValue = row[i]
                try:
                    oldValue = int(oldValue)
                    row[i] = generalizeNumericData(oldValue)
                except ValueError:
                    row[i] = generalizeCategoricalData(oldValue)
        with open(database, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
    print(colored("    >> Database generalized","green"))


def generalizeNumericData(number):
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


def generalizeCategoricalData(value):
    print(value)


# Get master key to decrypt or encrypt pseudonyms file
def getMasterKey():
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
def pseudonymDatabase(database, columns):
    print(colored("    >> Pseudonymizing database","green"))
    pseudonyms ={}
    if database == ownDatabaseName:
        for row in rowsOwnDatabase[1:]:
            oldValue = row[1]
            row[1] = create_pseudonym(oldValue,pseudonyms)
        with open(database, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rowsOwnDatabase)
    else:
        for row in rows:
            oldValue = row[1]
            row[1] = create_pseudonym(oldValue,pseudonyms)
        with open(database, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerows(rows)
    print(colored("    >> Database pseudonymized","green"))
    if "pseudonyms" in args and args["pseudonyms"] == "secure":
        key, nonce = getMasterKey()
        cipher = Cipher(algorithm=algorithms.AES256(key), mode=modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        with open(database[0:len(database)-4]+"_pseudonyms.json", 'wb') as f:
                f.write(encryptor.update(json.dumps(pseudonyms).encode('utf-8')))        
    print(colored("    >> Created pseudonym dictionary file","green"))
# Generar un pseudónimo para un nombre
def create_pseudonym(name,pseudonyms):
    pseudonym = fake.first_name()
    while pseudonym ==name or  pseudonym[0] != name[0]:
        pseudonym = fake.first_name()
    pseudonyms[pseudonym] = name
    return pseudonym

def get_secured_id_from_pseudonym(database, pseudonym):
    key, nonce = getMasterKey()
    cipher = Cipher(algorithm=algorithms.AES256(key), mode=modes.GCM(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    with open(database[0:len(database)-4]+"_pseudonyms.json", 'rb') as f:
        decrypted = decryptor.update(f.read()).decode('utf-8')   
        pseudonyms = json.loads(decrypted)
    return pseudonyms[pseudonym]

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    if args["mode"] == "cli":
        new = input(colored("Do you want to create a new database? (y/n)\n", color='yellow'))
        if new.lower() == "y" or new.lower == "yes":
            ownDatabaseName = input(colored("Please, introduce the name of your database. Remember, this database name needs to finish with the extension .csv\n", color='yellow'))
            create_own_database.create_database(ownDatabaseName)
        database= input(colored("Introduce a database to be anonymized\n", color="yellow"))
        read = readDatabase(database)
        while not read:
            database = input(colored("Introduce a database to be anonymized\n","yellow"))
            read = readDatabase(database)
        while True:  
            option = input(colored("Introduce an option to proceed with the anonymization: \n 1. Pseudonymize the database\n 2. Get ID from pseudonym (after option 1)\n 3. Generalize database.\n 4. Change database \n 5. Change to web interface \n 6. To exit the app, introduce either 'exit' or 6\n","yellow"))
            if option == "1":
                pseudonymDatabase(database, None)
            elif option == "2":
                pseudonym = input(colored("Introduce a pseudonym to translate\n","yellow"))
                print(colored(f"The ID associated with pseudonym {pseudonym} is: {get_secured_id_from_pseudonym(database, pseudonym)}","blue"))
            elif option == "3":
                generalizeDatabase(database, None)
            elif option == "4":
                database = input(colored("Introduce a database\n","yellow"))
                read = readDatabase(database)
                while not read:
                    database = input(colored("Introduce a database\n","yellow"))
                    read = readDatabase(database)
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