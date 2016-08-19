from flask import Flask, render_template, request, make_response, url_for
from RedisDBFacade import DatabaseFacade
import os
import re
import sys
import traceback
from ClientException import ClientException
import logging
from Species import Species

#TODO get cache actually working
#TODO implement status codes everywhere
#TODO get log stmts where possible rogue client/attacks could be occuring
#TODO check min,max params more thoroughly
#TODO fix species enum
#TODO convert objs to JSON
#TODO handle exceptions appropriately in every api and such request
app = Flask(__name__)
species = Species()
UNKOWN_ERROR_MSG = "An unexpected error occurred.  This error has been reported to our development team and will hopefully be handled soon."
cache = {}

# ====== HOME METHODS ======#

@app.route('/', methods=['GET'])
def home_page():
    page = cache.get('home')
    if page is None:
        page = render_template('index.html', species = species.getAllSpecies())
        cache['page'] = page
        print("home page was regenerated")
    return page

# ====== DEVELOPER METHODS ======#

#TODO status codes
#TODO authenticate first
@app.route('/print', methods=['GET'])
def print_DB():
    db.printDB()
    return make_response()

#TODO status codes
#TODO authenticate first
@app.route('/reset', methods=['GET'])
def reset_DB():
    db.clearDatabase()
    return make_response()

# ====== API QUERY METHODS ======#

#TODO status codes
@app.route('/trainers', methods=['GET'])
def trainer_list():
    trainerName = request.args.get('trainer-search-name')
    trainers = None
    if trainerName:
        trainers = db.getTrainersByStrictNameMatch(trainerName)
    else:
        trainers = db.getAllTrainers()
    return trainers

#TODO status codes
@app.route('/pokemon', methods=['GET'])
def pokemon_list():
    pokemon = getPokemonForPokemonList(request)
    return pokemon

#TODO status codes
#TODO if trainer doesn't exist, send them a msg that the user that they are attempting to view has been deleted
@app.route('/trainers/<trainerProfileID>', methods=['GET'])
def trainer_profile(trainerProfileID):
    trainerName = db.getTrainerName(trainerProfileID)
    pokemon = db.getPokemonForTrainer(trainerProfileID)
    return [trainerName, pokemon]

# ====== API ADD/DELETE METHODS ======#

#TODO implement this:  retrieve the values from the request and check their validity, then call the DB method.
@app.route('/trainers/<trainerID>/pokemon', methods=['POST'])
def add_pokemon_to_trainer(trainerID):
    msg = None
    cookie = None
    statusCode = 200
    try:
        trainerAuthID = authCookie(request)
        cookie = db.generateNewCookieForTrainer(trainerAuthID)
        if not trainerID == trainerAuthID:
            raise ClientException("You do not have permission to add a pokemon to this account.")
        #db.addPokemonToTrainer()
        msg = "your pokemon has been added"
    except ClientException as e:
        msg = str(e)
        statusCode = 400
    except:
        logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        logging.critical(traceback.print_exc())
        msg = UNKOWN_ERROR_MSG
        statusCode = 500
    resp = make_response(msg, statusCode)
    if cookie is not None:
        resp.set_cookie('cookie', cookie)
    return resp

@app.route('/trainers/<trainerID>/pokemon/<pokemonID>', methods=['DELETE'])
def delete_pokemon_from_trainer(trainerID, pokemonID):
    msg = None
    cookie = None
    statusCode = 200
    try:
        trainerAuthID = authCookie(request)
        cookie = db.generateNewCookieForTrainer(trainerAuthID)
        if not trainerID == trainerAuthID:
            raise ClientException("You do not have permission to delete this pokemon.")
        db.deleteSpecificPokemon(pokemonID, trainerAuthID)
        msg = "your pokemon has been deleted"
    except ClientException as e:
        msg = str(e)
        statusCode = 400
    except:
        logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        logging.critical(traceback.print_exc())
        msg = UNKOWN_ERROR_MSG
        statusCode = 500
    resp = make_response(msg, statusCode)
    if cookie is not None:
        resp.set_cookie('cookie', cookie)
    return resp

@app.route('/trainers/<trainerID>', methods=['DELETE'])
def delete_trainer(trainerID):
    msg = None
    statusCode = 200
    try:
        trainerAuthID = authCookie(request)
        if not trainerID == trainerAuthID:
            raise ClientException("You do not have permission to delete this account.")
        db.removeTrainer(trainerAuthID)
        msg = "your account has been deleted"
    except ClientException as e:
        msg = str(e)
        statusCode = 400
    except:
        logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        logging.critical(traceback.print_exc())
        msg = UNKOWN_ERROR_MSG
        statusCode = 500
    resp = make_response(msg, statusCode)
    resp.set_cookie('cookie', '', expires=0)
    resp.set_cookie('email', '', expires=0)
    resp.set_cookie('displayName', '', expires=0)
    resp.set_cookie('trainerID', '', expires=0)
    return resp


# ====== REGISTER and AUTH METHODS ======#


@app.route('/register', methods=['POST'])
def register_page_submit():
    #TODO put in a not a robot box and maybe generate a temp session id
    #TODO have more strict name or password checks?  could a rogue client break my password hasher?
    msg = None
    statusCode = 200
    try:
        name = None
        email = None
        password = None
        try:
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
        except:
            raise ClientException("Not all fields included in form.")
        checkEmail(email)
        if not name or not password:
            raise ClientException('no password or display name was supplied')
        db.registerTrainer(name,email,password)
        msg = "Congratulations!  You have been successfully registered!  Now you need to log in."
    except ClientException as e:
        msg = str(e)
        statusCode = 400
    except:
        logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        logging.critical(traceback.print_exc())
        msg = UNKOWN_ERROR_MSG
        statusCode = 500
    return msg, statusCode

@app.route('/login', methods=['POST'])
def handleLogin():
    msg = None
    statusCode = 200
    try:
        rslts = authUser(request)
        trainerID = rslts[0]
        email = rslts[1]
        cookie = rslts[2]
        displayName = db.getTrainerName(trainerID)
        resp = make_response("Success")
        resp.set_cookie('cookie', cookie)
        resp.set_cookie('email', email)
        resp.set_cookie('displayName', displayName)
        resp.set_cookie('trainerID', trainerID)
        return resp
    except ClientException as e:
        logging.warning(str(sys.exc_info()[1]) + ":" + request.remote_addr)
        msg = str(e)
        statusCode = 400
    except:
        logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        logging.critical(traceback.print_exc())
        msg = UNKOWN_ERROR_MSG
        statusCode = 500
    return msg, statusCode

@app.route('/logout', methods=['GET'])
def handleLogout():
    msg = None
    statusCode = 200
    try:
        authCookie(request)
        msg = "You have been successfully logged out."
    except ClientException as e:
        msg = str(e)
        statusCode = 400
    except:
        logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        logging.critical(traceback.print_exc())
        msg = UNKOWN_ERROR_MSG
        statusCode = 500
    resp = make_response(msg, statusCode)
    resp.set_cookie('cookie', '', expires=0)
    resp.set_cookie('email', '', expires=0)
    resp.set_cookie('displayName', '', expires=0)
    resp.set_cookie('trainerID', '', expires=0)
    return resp

def authUser(request):
    email = None
    givenPassword = None
    try:
        email = request.form['email']
        givenPassword = request.form['password']
    except:
        raise ClientException("Not all form fields included")
    if not givenPassword:
        raise ClientException("No password was given")
    checkEmail(email)
    trainerID = db.validateUser(email, givenPassword)
    db.deleteCookieForTrainerIfExists(trainerID)
    cookie = db.generateNewCookieForTrainer(trainerID)
    return (trainerID, email, cookie)

def authCookie(request):
    cookie = None
    email = None
    try:
        cookie = request.cookies['cookie']
        email = request.cookies['email']
    except:
        raise ClientException("You did not supply a cookie.  Your request could not be processed.  You will need to log in again or something.")
    trainerID = db.validateCookie(cookie, email)
    db.deleteCookieForTrainerIfExists(trainerID)
    return trainerID



    # ====== GENERAL HANDLERS AND UTIL METHODS ======#

def checkEmail(email):
    if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]{2,63}$", email):
        raise ClientException("improperly formatted email address")
    return

def checkIsInt(*args):
    for i in args:
        if not isinstance(i, int) and not isinstance(int(i),int):
            raise ValueError("illegal value:"+str(i)+";")
    return

#TODO handle exceptions from the second try method?
def getPokemonForPokemonList(request):
    min = request.args.get('min')
    max = request.args.get('max')
    start = request.args.get('start')
    num = request.args.get('num')
    species = request.args.get('species')
    try:
        checkIsInt(min,max,start,num)
        return db.getGeneralPokemon(min=min, max=max, start=start, num=num)
    except:
        return db.getGeneralPokemon()


# ====== MAIN/CONFIG METHODS ======#

@app.before_first_request
def configure():
    logging.basicConfig(filename='app.log', level=logging.WARNING)
    db.clearDatabase()
    trainerID = db.registerTrainer("Dudeguy","acdavidson@sbcglobal.net","abc123")

    for i in range(0, 500):
        db.addPokemonToTrainer(trainerID, "Pika Pika"+str(i), "Pikachu", i+5)
    db.addPokemonToTrainer(trainerID,"charm","Charizard",406)
    db.addPokemonToTrainer(trainerID, "Bubbles", "Squirtle", 123)
    db.addPokemonToTrainer(trainerID, "Ivy", "Ivysaur", 555)
    return

if __name__ == '__main__':
    context = ('poke_cert.pem', 'poke_key.pem')
    db = DatabaseFacade()
    species = Species()
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True, ssl_context=context)
