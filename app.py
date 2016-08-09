from flask import Flask, render_template, request, make_response, url_for
from RedisDBFacade import DatabaseFacade
import os
import re
import sys
import traceback
from ClientException import ClientException
import logging
from Species import Species

#<span class="glyphicon glyphicons-search"></span>
#TODO add log stmts to any new exceptions
#TODO add successmsg
#TODO check min,max params more thoroughly
#TODO fix species enum
app = Flask(__name__)
UNKOWN_ERROR_MSG = "An unexpected error occurred.  This error has been reported to our development team and will hopefully be handled soon."

# ====== HOME METHODS ======#

@app.route('/login', methods=['GET'])
@app.route('/home/login', methods=['GET'])
@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
def home_page():
    return handleGet(request, 'index.html', url_for("home_page_auth"), url_for("home_page_logout"))


@app.route('/login', methods=['POST'])
@app.route('/home/login', methods=['POST'])
def home_page_auth():
    return handleLogin(request, 'index.html', url_for("home_page_auth"), url_for("home_page_logout"))

@app.route('/logout', methods=['GET'])
@app.route('/home/logout', methods=['GET'])
def home_page_logout():
    return handleLogout(request, 'index.html', url_for("home_page_auth"))

# ====== DEVELOPER METHODS ======#

@app.route('/print', methods=['GET'])
def print_DB():
    db.printDB()
    return handleGet(request, 'index.html', url_for("home_page_auth"), url_for("home_page_logout"))

#TODO send popup when successful
@app.route('/reset', methods=['GET'])
def reset_DB():
    db.clearDatabase()
    return handleGet(request, 'index.html', url_for("home_page_auth"), url_for("home_page_logout"))

# ====== TRAINERS LIST METHODS ======#

@app.route('/trainers/login', methods=['GET'])
@app.route('/trainers', methods=['GET'])
def trainer_list_page():
    trainerName = request.args.get('trainer-search-name')
    trainers = None
    if trainerName:
        trainers = db.getTrainersByStrictNameMatch(trainerName)
    else:
        trainers = db.getAllTrainers()
    return handleGet(request, 'trainer_list.html', url_for("trainer_list_login"), url_for("trainer_list_logout"), trainers=trainers, trainersActive=True)

@app.route('/trainers/login', methods=['POST'])
def trainer_list_login():
    trainerName = request.args.get('trainer-search-name')
    trainers = None
    if trainerName:
        trainers = db.getTrainersByStrictNameMatch(trainerName)
    else:
        trainers = db.getAllTrainers()
    return handleLogin(request, 'trainer_list.html', url_for("trainer_list_login"), url_for("trainer_list_logout"),
                     trainers=trainers, trainersActive=True)

@app.route('/trainers/logout', methods=['GET'])
def trainer_list_logout():
    trainerName = request.args.get('trainer-search-name')
    trainers = None
    if trainerName:
        trainers = db.getTrainersByStrictNameMatch(trainerName)
    else:
        trainers = db.getAllTrainers()
    return handleLogout(request, 'trainer_list.html', url_for("trainer_list_login"),
                     trainers=trainers, trainersActive=True)

# ====== POKEMON LIST METHODS ======#

@app.route('/pokemon/login', methods=['GET'])
@app.route('/pokemon', methods=['GET'])
def pokemon_list_page():
    pokemon = getPokemonForPokemonList(request)
    return handleGet(request, 'pokemon_list.html', url_for("pokemon_list_login"), url_for("pokemon_list_logout"), pokemon=pokemon, pokemonActive=True, species=species.speciesList)

@app.route('/pokemon/login', methods=['POST'])
def pokemon_list_login():
    pokemon = getPokemonForPokemonList(request)
    return handleLogin(request, 'pokemon_list.html', url_for("pokemon_list_login"), url_for("pokemon_list_logout"), pokemon=pokemon, pokemonActive=True, species=species.speciesList)

@app.route('/pokemon/logout', methods=['GET'])
def pokemon_list_logout():
    pokemon = getPokemonForPokemonList(request)
    return handleLogout(request, 'pokemon_list.html', url_for("pokemon_list_login"), pokemon=pokemon, pokemonActive=True, species=species.speciesList)

# ====== TRAINER PROFILE METHODS ======#

#TODO if trainer doesn't exist, rdr to home page and send them a msg that the user that they are attempting to view has been deleted
@app.route('/trainers/<trainerProfileID>/login', methods=['GET'])
@app.route('/trainers/<trainerProfileID>', methods=['GET'])
def trainer_profile_page(trainerProfileID):
    trainerName = db.getTrainerName(trainerProfileID)
    pokemon = db.getPokemonForTrainer(trainerProfileID)
    return handleGet(request, 'trainer_profile.html', url_for("trainer_profile_login",trainerProfileID=trainerProfileID), url_for("trainer_profile_logout",trainerProfileID=trainerProfileID), pokemon=pokemon, trainerProfileID=trainerProfileID, trainerProfileName=trainerName)

@app.route('/trainers/<trainerProfileID>/login', methods=['POST'])
def trainer_profile_login(trainerProfileID):
    trainerName = db.getTrainerName(trainerProfileID)
    pokemon = db.getPokemonForTrainer(trainerProfileID)
    return handleLogin(request, 'trainer_profile.html', url_for("trainer_profile_login",trainerProfileID=trainerProfileID), url_for("trainer_profile_logout",trainerProfileID=trainerProfileID), pokemon=pokemon, trainerProfileID=trainerProfileID, trainerProfileName=trainerName)

@app.route('/trainers/<trainerProfileID>/logout', methods=['GET'])
def trainer_profile_logout(trainerProfileID):
    trainerName = db.getTrainerName(trainerProfileID)
    pokemon = db.getPokemonForTrainer(trainerProfileID)
    return handleLogout(request, 'trainer_profile.html', url_for("trainer_profile_login",trainerProfileID=trainerProfileID), pokemon=pokemon, trainerProfileID=trainerProfileID, trainerProfileName=trainerName)

# ====== REGISTER METHODS ======#

# TODO consider refactoring to combine with Home
@app.route('/register', methods=['GET'])
def register_page():
    try:
        cookie = request.cookies['cookie']
        email = request.cookies['email']
        try:
            rslts = db.validateCookie(cookie, email)
            trainerID = rslts[0]
            date = rslts[1]
            db.deleteCookie(trainerID, cookie, date)
            cookieToReturn = db.getNewCookie(trainerID)
            displayName = db.getTrainerName(trainerID)
            msg = "You must be logged out in order to register as a new user."
            resp = make_response(
                render_template('index.html', authID=trainerID,
                                authName=displayName, msg = msg, logout=url_for("home_page_logout")))
            resp.set_cookie('cookie', cookieToReturn)
            resp.set_cookie('email', email)
            return resp
        except ClientException as e:
            msg = str(e)
        except:
            logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
            logging.critical(traceback.print_exc())
            msg = UNKOWN_ERROR_MSG
        resp = make_response(
                render_template('index.html', msg=msg, login=url_for("home_page_auth")))
        resp.set_cookie('cookie', '', expires=0)
        resp.set_cookie('email', '', expires=0)
        return resp
    except:
        return render_template('register.html', register=True, login = url_for("home_page_auth"))

@app.route('/register', methods=['POST'])
def register_page_submit():
    #TODO put in a not a robot box and maybe generate a temp session id
    #TODO have more strict name or password checks?  could a rogue client break my password hasher?
    msg = None
    try:
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        checkEmail(email)
        if not name or not password:
            raise ClientException('no password or display name was supplied')
        db.registerTrainer(name,email,password)
        msg = "Congratulations!  You have been successfully registered!  Now you need to log in."
        return render_template('index.html', msg = msg, login = url_for("home_page_auth"))
    except ClientException as e:
        msg = str(e)
    except:
        logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        logging.critical(traceback.print_exc())
        msg = UNKOWN_ERROR_MSG
    return render_template('register.html', register=True, msg = msg, login = url_for("home_page_auth"))

# ====== GENERAL HANDLERS AND UTIL METHODS ======#

def handleGet(request, templateToRender, loginUrl, logoutURL, pokemonActive=False, trainersActive=False, pokemon=[], trainers=[], trainerProfileID=None, trainerProfileName=None, species=None):
    msg = None
    try:
        cookie = request.cookies['cookie']
        email = request.cookies['email']
        try:
            rslts = db.validateCookie(cookie, email)
            trainerID = rslts[0]
            date = rslts[1]
            db.deleteCookie(trainerID, cookie, date)
            cookieToReturn = db.getNewCookie(trainerID)
            displayName = db.getTrainerName(trainerID)
            resp = make_response(
                render_template(templateToRender, pokemonActive=pokemonActive, trainersActive=trainersActive,
                                authID=trainerID, authName=displayName, logout=logoutURL, pokemon=pokemon, trainers=trainers, trainerProfileID=trainerProfileID,trainerProfileName=trainerProfileName, species=species))
            resp.set_cookie('cookie', cookieToReturn)
            resp.set_cookie('email', email)
            return resp
        except ClientException as e:
            logging.warning(str(sys.exc_info()[1]) + ":" + request.remote_addr)
            msg = str(e)
        except:
            logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
            logging.critical(traceback.print_exc())
            msg = UNKOWN_ERROR_MSG
        resp = make_response(
            render_template(templateToRender, pokemonActive=pokemonActive, trainersActive=trainersActive, msg=msg, login=loginUrl, pokemon=pokemon, trainers=trainers, trainerProfileID=trainerProfileID,trainerProfileName=trainerProfileName, species=species))
        resp.set_cookie('cookie', '', expires=0)
        resp.set_cookie('email', '', expires=0)
        return resp
    except:
        return render_template(templateToRender, pokemonActive=pokemonActive, trainersActive=trainersActive,
                               login=loginUrl, pokemon=pokemon, trainers=trainers, trainerProfileID=trainerProfileID,trainerProfileName=trainerProfileName, species=species)

def handleLogin(request, templateToRender, login, logout,  pokemonActive=False, trainersActive=False, pokemon=[], trainers=[], trainerProfileID=None, trainerProfileName=None, species=None):
    msg = None
    try:
        rslts = authUser(request)
        trainerID = rslts[0]
        email = rslts[1]
        cookie = rslts[2]
        displayName = db.getTrainerName(trainerID)
        resp = make_response(
            render_template(templateToRender, pokemonActive=pokemonActive, trainersActive=trainersActive,
                            authID=trainerID, authName=displayName, logout=logout, pokemon=pokemon, trainers=trainers, trainerProfileID=trainerProfileID,trainerProfileName=trainerProfileName, species=species))
        resp.set_cookie('cookie', cookie)
        resp.set_cookie('email', email)
        return resp
    except ClientException as e:
        logging.warning(str(sys.exc_info()[1]) + ":" + request.remote_addr)
        msg = str(e)
    except:
        logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        logging.critical(traceback.print_exc())
        msg = UNKOWN_ERROR_MSG
    return render_template(templateToRender, pokemonActive=pokemonActive, trainersActive=trainersActive, msg=msg,
                           login=login, pokemon=pokemon, trainers=trainers, trainerProfileID=trainerProfileID,trainerProfileName=trainerProfileName, species=species)


def handleLogout(request, templateToRender, loginUrl,  pokemonActive=False, trainersActive=False, pokemon=None, trainers=None, trainerProfileID=None, trainerProfileName=None, species=None):
    msg = None
    try:
        cookie = request.cookies['cookie']
        email = request.cookies['email']
        try:
            rslts = db.validateCookie(cookie, email)
            trainerID = rslts[0]
            date = rslts[1]
            db.deleteCookie(trainerID, cookie, date)
            msg = "You have been successfully logged out."
        except ClientException as e:
            msg = str(e)
        except:
            logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
            logging.critical(traceback.print_exc())
            msg = UNKOWN_ERROR_MSG
        resp = make_response(
            render_template(templateToRender, pokemonActive=pokemonActive, trainersActive=trainersActive, msg=msg,
                            login=loginUrl, pokemon=pokemon, trainers=trainers, trainerProfileID=trainerProfileID,trainerProfileName=trainerProfileName, species=species))
        resp.set_cookie('cookie', '', expires=0)
        resp.set_cookie('email', '', expires=0)
        return resp
    except:
        return render_template(templateToRender, pokemonActive=pokemonActive, trainersActive=trainersActive,
                               login=loginUrl, pokemon=pokemon, trainers=trainers, trainerProfileID=trainerProfileID,trainerProfileName=trainerProfileName, species=species)

def authUser(request):
    email = request.form['email']
    givenPassword = request.form['password']
    if not givenPassword:
        raise ClientException("No password was given")
    checkEmail(email)
    trainerID = db.validateUser(email, givenPassword)
    db.deleteCookieForTrainerIfExists(trainerID)
    cookie = db.getNewCookie(trainerID)
    return (trainerID, email, cookie)

def checkEmail(email):
    if not re.match(r"^[A-Za-z0-9\.\+_-]+@[A-Za-z0-9\._-]+\.[a-zA-Z]{2,63}$", email):
        raise ClientException("improperly formatted email address")
    return

def checkIsInt(*args):
    for i in args:
        if not isinstance(i, int) and not isinstance(int(i),int):
            raise ValueError("illegal value:"+str(i)+";")

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

