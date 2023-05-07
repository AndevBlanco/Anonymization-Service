import os
import csv
import shutil
from faker import Faker
import random
from termcolor import colored
import pandas as pd

possible_jobs = ["manager", "director", "supervisor", "executive", "team lead", "department head", "project manager", "general manager", "chief executive officer (CEO)",
                 "sales representative", "account executive", "business development manager", "sales manager", "sales director", "account manager", "account representative", "inside sales representative", "outside sales representative", "sales consultant"
                 "customer service representative", "customer support specialist", "technical support representative", "call center representative", "customer service manager", "customer experience specialist", "customer success manager",
                 "software engineer", "mechanical engineer", "electrical engineer", "civil engineer", "chemical engineer", "systems engineer", "quality engineer", "process engineer", "design engineer", "data engineer", "machine learning engineer", "network engineer",
                 "marketing manager", "marketing coordinator", "public relations specialist", "communications specialist", "content marketing specialist", "social media manager", "digital marketing manager", "marketing director", "brand manager", "product marketing manager",
                 "accountant", "financial analyst", "financial advisor", "investment banker", "tax accountant", "budget analyst", "financial manager", "financial planner", "credit analyst", "loan officer", "actuary",
                 "nurse", "physician", "pharmacist", "physical therapist", "occupational therapist", "speech therapist", "medical assistant", "dental assistant", "radiologic technologist", "ultrasound technician", "nurse practitioner", "physician assistant",
                 "teacher", "professor", "school counselor", "librarian", "instructional designer", "education consultant", "curriculum developer", "educational psychologist", "tutor", "academic advisor", "enrollment counselor",
                 "lawyer", "paralegal", "legal secretary", "judge", "court reporter", "legal consultant", "law clerk", "law librarian", "law professor", "mediator",
                 "artist", "graphic designer", "illustrator", "photographer", "videographer", "film director", "editor", "producer", "creative director", "musician", "composer", "writer", "copywriter", "editorial assistant", "art director",
                 "agricultural scientist", "horticulturist", "forester", "soil scientist", "fish and game warden", "natural resources manager", "environmental scientist", "wildlife biologist", "botanist",
                 "research scientist", "data scientist", "material scientist", "biomedical scientist", "environmental scientist", "geologist", "physicist", "astrophysicist", "mathematician", "statistician",
                 "civil servant", "military officer", "diplomat", "government analyst", "policy advisor", "political scientist", "public administrator", "intelligence analyst", "customs officer", "border patrol agent",
                 "physical therapist", "occupational therapist", "speech therapist", "music therapist", "art therapist", "behavioral therapist", "psychologist", "psychiatrist", "marriage and family therapist", "mental health counselor", "play therapist", "dance therapist", "drama therapist", "equine therapist",
                 "sports", "sport", "coach", "trainer", "athlete", "fitness",
                 "chef", "cook", "waiter", "waitress", "bartender",
                 "human resources", "recruiter", "talent acquisition", "trainer",
                 "operations", "logistics", "supply chain", "warehouse",
                 "construction", "contractor", "carpenter", "electrician", "plumber", "maintenance",
                 "transportation", "driver", "pilot", "conductor", "shipper",
                 "military", "soldier", "navy", "air force", "marine", "coast guard",
                 "fashion", "beauty", "cosmetics", "hair stylist", "makeup artist",
                 "technology", "IT", "network", "security", "QA", "web",
                 "real estate", "realtor", "appraiser", "broker",
                 "media", "broadcasting", "tv", "radio",
                 "religion", "minister", "pastor", "clergy", "theology",
                 "social work", "counselor", "social worker", "case manager",
                 "environment", "sustainability", "green", "recycling", "conservation",
                 "automotive", "mechanic", "technician", "repair", "maintenance",
                 "insurance", "underwriter", "adjuster", "actuary",
                 "aviation", "pilot", "airline", "aircraft",
                 "hospitality", "hotel", "resort", "cruise",
                 "manufacturing", "production", "fabrication", "assembly", "quality control", "maintenance", "mechanic",
                 "transportation", "driver", "pilot", "airline", "logistics", "dispatcher",
                 "construction", "contractor", "builder", "carpenter", "electrician", "plumber", "welder", "painter",
                 "information technology", "IT", "computer", "network", "security", "administrator", "support",
                 "human resources", "recruiter", "talent", "training", "development",
                 "fashion", "designer", "stylist", "model", "seamstress", "tailor", "retail",
                 "real estate", "agent", "broker", "appraiser", "property", "manager", "leasing",
                 "religion", "minister", "pastor", "clergy", "chaplain", "missionary",
                 "environmental", "conservation", "sustainability", "renewable", "recycling",
                 "military", "soldier", "veteran", "officer", "navy", "army", "air force", "marine",
                 "media", "journalism", "reporter", "broadcast", "radio", "television",
                 "science", "research", "biologist", "biotech",
                ]

civil_statuses = ['single', 'married', 'divorced', 'widowed']

def get_random_job():
    return random.choice(possible_jobs)



def create_database(database_name: str, use_local_database: bool):
    if use_local_database:
        create_local_database(database_name)
    else:
        create_external_database(database_name)
    
def create_external_database(database_name: str):
    external_databases_folder = "external-databases"
    os.makedirs(name=external_databases_folder, exist_ok=True)
    external_database = f"external-databases/german.data"
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
    shutil.copyfile(f"{external_databases_folder}/{database_name}", f"{external_databases_folder}/{database_name}_original")
    print(colored(f"External database created with {len(data.columns)} columns: {data.columns}", "green"))


def create_local_database(database_name: str):
    local_databases_folder = "local-databases"
    os.makedirs(name=local_databases_folder, exist_ok=True)
    dataset_length = 500
    rows = []
    print(colored("Creating own database", "green"))
    with open(f"{local_databases_folder}/{database_name}", 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        columns = ['id', 'name', 'job','gender', 'age','civil status','country' ,'email', 'mobile phone number', 'zipcode', 'salary', 'security identifier']
        writer.writerow(columns)
        fake = Faker()
        for i in range(1, dataset_length):
            row = [
                    i,
                    fake.name(),
                    get_random_job(),
                    fake.random_element(elements=('Male', 'Female')),
                    random.randint(20,60),
                    random.choice(civil_statuses),
                    fake.country(),
                    fake.email(),
                    str(random.randint(600000000, 999999999)),
                    fake.postcode(),
                    random.randint(13000, 100000),
                    fake.ssn(),
                ]
            rows.append(row)
        # Guardar los datos en un archivo CSV
        writer = csv.writer(f)
        writer.writerows(rows)
    
    shutil.copyfile(f"{local_databases_folder}/{database_name}", f"{local_databases_folder}/{database_name}_original")
    print(colored(f"Local database created with {len(columns)} columns: {columns}", "green"))


if __name__ == '__main__':
    # database_name = "db.csv"
    # database_type = "local"
    database_name = "db.csv"
    database_type = "external"
    create_database(database_name, database_type)
