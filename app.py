from dotenv import load_dotenv
from flask import Flask, render_template
from argparse import ArgumentParser
from faker import Faker
import csv, json, os,bson
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

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

master_key = None

def readDatabase(database):
    print("    >> Reading database")
    try:
        with open(database, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                if database == 'database.csv':
                    rowsOwnDatabase.append(row)
                else:
                    rows.append(row)
        return True
    except:
        print("    >> Error reading database")
        return False


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
## TO DO OTHER DATABASE
def pseudonymDatabase(database, columns):
    print("    >> Pseudonymizing database")
    pseudonyms ={}
    if database == 'database.csv':
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
    print("    >> Database pseudonymized")
    if "pseudonyms" in args and args["pseudonyms"] == "secure":
        key, nonce = getMasterKey()
        cipher = Cipher(algorithm=algorithms.AES256(key), mode=modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        with open(database+"_pseudonyms.json", 'wb') as f:
                f.write(encryptor.update(json.dumps(pseudonyms).encode('utf-8')))        
    print("    >> Created pseudonym dictionary file")

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
    with open(database+"_pseudonyms.json", 'rb') as f:
        decrypted = decryptor.update(f.read()).decode('utf-8')   
        pseudonyms = json.loads(decrypted)
    return pseudonyms[pseudonym]

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    if args["mode"] == "cli":
        database= input("Introduce a database to be anonymized\n")
        read = readDatabase(database)
        while not read:
            database = input("Introduce a database to be anonymized\n")
            read = readDatabase(database)
        while True:   
            option = input("Introduce an option to proceed with the anonymization: \n 1. Pseudonymize the database\n 2. Get ID from pseudonym (after option 1)\n 3. Change database\n 4. Change to web interface \n 5. To exit the app, introduce either 'exit' or 5\n")
            if option == "1":
                pseudonymDatabase(database, None)
            elif option == "2":
                pseudonym = input("Introduce a pseudonym to translate\n")
                print(f"The ID associated with pseudonym {pseudonym} is: {get_secured_id_from_pseudonym(database, pseudonym)}")
            elif option == "3":
                database = input("Introduce a database\n")
                read = readDatabase(database)
                while not read:
                    database = input("Introduce a database\n")
                    read = readDatabase(database)
            elif option == "4":
                app.run()
            elif option == "5" or option == "exit":
                print("Leaving the app. See you soon :)")
                break
            else:
                print("Invalid option")
            print('*'*100)
    else:
        app.run()