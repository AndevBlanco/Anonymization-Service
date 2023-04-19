#### **Create the virtual environment**
`py -m venv env`

#### **Install libraries**
`pip install -r requirements.txt`

#### **Set environment variables**
`set FLASK_APP=app.py`
`set FLASK_ENV=env`

### ** Create own database **
To create your own database, you need to execute the following command:

`py create-own-database.py`

This will create your own database in your local directory with the name `database.csv`

#### **Run server**
The app has different arguments to run the server that they are:

`py app.py -ps {random, secure} -m {cli, web}`

**-ps will indicate if the pseudonym is either random or secure and reversible**
**-m will indicate if the user wants to use the CLI or the WEB interface**

