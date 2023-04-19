from dotenv import load_dotenv
from flask import Flask, render_template
from argparse import ArgumentParser

load_dotenv()

app = Flask(__name__)

parser = ArgumentParser()
parser.add_argument("-i", "--import", dest="import", required=False, help="Import the database")
parser.add_argument("-a", "--anonymization", dest="anonymization", required=False, help="Anonymization")

args = vars(parser.parse_args())
print(args)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
   app.run()