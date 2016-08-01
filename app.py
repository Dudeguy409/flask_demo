from flask import Flask, render_template, request, make_response, url_for
from RedisDBFacade import DatabaseFacade
import os
import re
import sys
import traceback
from ClientException import ClientException
import logging

# TODO encrypt passwords and check fields using js client-side
# TODO if not authed, send a salt for password?
app = Flask(__name__)
ACTIVE = "Active"
INACTIVE = ""
UNKOWN_ERROR_MSG = "An unexpected error occurred.  This error has been reported to our development team and will hopefully be handled soon."

@app.route('/', methods=['GET'])
@app.route('/home', methods=['GET'])
@app.route('/index', methods=['GET'])
@app.route('/login', methods=['GET'])
@app.route('/home/login', methods=['GET'])
@app.route('/index/login', methods=['GET'])
def home_page():
    return handleGet(request, 'index.html', url_for("home_page_auth"), url_for("home_page_logout"), INACTIVE, INACTIVE)

@app.route('/login', methods=['POST'])
@app.route('/home/login', methods=['POST'])
@app.route('/index/login', methods=['POST'])
def home_page_auth():
    return handleLogin('index.html', url_for("home_page_auth"), url_for("home_page_logout"), INACTIVE, INACTIVE)

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
                render_template('index.html', pokemonActive=INACTIVE, trainersActive=INACTIVE, trainerID=trainerID,
                                displayName=displayName, msg = msg, logout=url_for("home_page_logout")))
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
                render_template('index.html', msg=msg, pokemonActive=INACTIVE, trainersActive=INACTIVE, login=url_for("home_page_auth")))
        resp.set_cookie('cookie', '', expires=0)
        resp.set_cookie('email', '', expires=0)
        return resp
    except:
        return render_template('register.html', pokemonActive=INACTIVE, trainersActive=INACTIVE, register=True, login = url_for("home_page_auth"))

@app.route('/register', methods=['POST'])
def register_page_submit():
    #TODO put in a not a robot box and maybe generate a temp session id
    #TODO have more strict name or password checks?
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
        return render_template('index.html', pokemonActive=INACTIVE, trainersActive=INACTIVE, msg = msg, login = url_for("home_page_auth"))
    except ClientException as e:
        msg = str(e)
    except:
        logging.critical(str(sys.exc_info()[0]) + str(sys.exc_info()[1]))
        logging.critical(traceback.print_exc())
        msg = UNKOWN_ERROR_MSG
    return render_template('register.html', pokemonActive=INACTIVE, trainersActive=INACTIVE, register=True, msg = msg, login = url_for("home_page_auth"))

#if no cookie, return to index page.  If cookie and error, say cookie has expired.  If cookie and no error, say logged out, if cookie and unkown error, print
@app.route('/logout', methods=['GET'])
@app.route('/home/logout', methods=['GET'])
@app.route('/index/logout', methods=['GET'])
def home_page_logout():
    # TODO if not authed, send a salt for password?
    return handleLogout(request, 'index.html', url_for("home_page_auth"), INACTIVE, INACTIVE)

@app.route('/print', methods=['GET'])
def print_DB():
    db.printDB()
    return handleGet(request, 'index.html', url_for("home_page_auth"), url_for("home_page_logout"), INACTIVE, INACTIVE)

#TODO send popup when successful
@app.route('/reset', methods=['GET'])
def reset_DB():
    db.clearDatabase()
    return handleGet(request, 'index.html', url_for("home_page_auth"), url_for("home_page_logout"), INACTIVE, INACTIVE)



#below code does not have potential issues documented
@app.route('/trainers', methods=['GET'])
@app.route('/trainers.html', methods=['GET'])
def trainer_list_page():
    return render_template('trainer_list.html', pokemonActive=INACTIVE, trainersActive=ACTIVE)

@app.route('/pokemon', methods=['GET'])
@app.route('/pokemon.html', methods=['GET'])
def pokemon_list_page():
    return render_template('pokemon_list.html', pokemonActive=ACTIVE, trainersActive=INACTIVE)

@app.route('/profile', methods=['GET'])
@app.route('/profile.html', methods=['GET'])
def my_profile_page():
    return render_template('trainer_profile.html', pokemonActive=INACTIVE, trainersActive=INACTIVE, title="My ")

@app.route('/trainers/<trainerID>', methods=['GET'])
def trainer_profile_page(trainerID):
    return render_template('trainer_profile.html', trainerID = trainerID, pokemonActive=INACTIVE, trainersActive=INACTIVE, title="'s")

@app.route('/pokemon/<pokemonID>', methods=['GET'])
def pokemon_profile_page(pokemonID):
    return render_template('pokemon_profile.html', pokemonID = pokemonID, pokemonActive=INACTIVE, trainersActive=INACTIVE)




def handleLogin(templateToRender, login, logout, pokemonActive, trainersActive):
    msg = None
    try:
        rslts = authUser(request)
        trainerID = rslts[0]
        email = rslts[1]
        cookie = rslts[2]
        displayName = db.getTrainerName(trainerID)
        resp = make_response(
            render_template(templateToRender, pokemonActive=pokemonActive, trainersActive=trainersActive,
                            trainerID=trainerID, displayName=displayName, logout=logout))
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
                           login=login)


def handleGet(request, templateToRender, loginUrl, logoutURL, pokemonActive, trainersActive):
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
                                trainerID=trainerID, displayName=displayName, logout=logoutURL))
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
            render_template(templateToRender, pokemonActive=pokemonActive, trainersActive=trainersActive, msg=msg, login=loginUrl))
        resp.set_cookie('cookie', '', expires=0)
        resp.set_cookie('email', '', expires=0)
        return resp
    except:
        return render_template(templateToRender, pokemonActive=pokemonActive, trainersActive=trainersActive,
                               login=loginUrl)



def handleLogout(request, templateToRender, loginUrl, pokemonActive, trainersActive):
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
                            login=loginUrl))
        resp.set_cookie('cookie', '', expires=0)
        resp.set_cookie('email', '', expires=0)
        return resp
    except:
        return render_template(templateToRender, pokemonActive=pokemonActive, trainersActive=trainersActive,
                               login=loginUrl)

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

@app.before_first_request
def configure():
    logging.basicConfig(filename='app.log', level=logging.WARNING)
    return

if __name__ == '__main__':
    context = ('poke_cert.pem', 'poke_key.pem')
    db = DatabaseFacade()
    app.run(host='0.0.0.0', port=5000, threaded=True, debug=True, ssl_context=context)

