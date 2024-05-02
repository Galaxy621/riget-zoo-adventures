import string
import urllib.parse
from flask import Blueprint, render_template, request, session, redirect, url_for

from common import redirect_home, char_in_string
from connector import Connector

bp = Blueprint("account", __name__)

@bp.route("/account")
def account():
    connector = Connector()

    # Detect is user is logged in
    user = session.get("user")
    if user is None: return redirect(url_for("pages.index"))

    user = connector.get_user_by_id(user["userID"])
    bookings = connector.get_user_bookings(user)

    bookinginfo = []

    # Construct a useful object, combining both the hotel and its booking information
    for i in bookings:
        info = {
            "hotel": connector.get_hotel_by_id(i.roomID),
            "booking": i
        }

        bookinginfo.append(info)

    return render_template("account.html.j2", bookinfo = bookinginfo)

@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user"): return redirect_home()
        session["last_page"] = request.args.get("redirect", "")
        print(session)

        return render_template("login.html.j2")
    
    connector = Connector()

    email = request.form.get("email").lower()
    password = request.form.get("password")

    user = connector.get_user_by_email(email=email)
    if user is None:
        return {"success": False, "reason": "There is no account under this email."}
    
    successful = connector.compare_password(user, password)

    if successful:
        session["user"] = user

    reason = "" if successful else "Password is incorrect"

    return {"success": successful, "reason": reason}

@bp.route("/signup", methods=["GET", "POST"])
def signup():
    # User is just visiting page, show them the signup page
    if request.method == "GET":
        if session.get("user"): return redirect_home()
        return render_template("signup.html.j2")
    
    # User has sent a POST request, meaning they've pressed submit
    # Create their account
    connector = Connector()

    name = request.form.get("name")
    email = request.form.get("email").lower()
    dateOfBirth = request.form.get("dateOfBirth")
    password = request.form.get("password")

    if len(name) <= 0:
        return {"success": False, "reason": "Your name is required"}

    # Detect is email already exists in database
    if connector.get_user_by_email(email):
        return {"success": False, "reason": "An account already exists with this email"}
    
    # Password Checks
    if len(password) < 8:
        return {"success": False, "reason": "Your password should be at least 8 characters long"}
    
    hasNumber = char_in_string(password, string.digits)
    if not hasNumber: return {"success": False, "reason": "Your password should contain numbers"}

    hasLower = char_in_string(password, string.ascii_lowercase)
    if not hasLower: return {"success": False, "reason": "Your password should contain lower case characters"}

    hasCapital = char_in_string(password, string.ascii_uppercase)
    if not hasCapital: return {"success": False, "reason": "Your password should contain upper case characters"}

    hasPunctuation = char_in_string(password, string.punctuation)
    if not hasPunctuation: return {"success": False, "reason": "Your password should contain punctuation"}
    
    # Use the database connector to create an account
    user = connector.create_account(
        name, email, password, dateOfBirth
    )

    # Set the user's session with all of their information
    session["user"] = user

    return {"success": True, "reason": ""}

@bp.route("/logout", methods=["GET", "POST"])
def logout():
    destination = request.args.get("redirect", None)

    # Remove the user info from the connected session
    if session.get("user", None): session.pop("user")

    if destination:
        return redirect(urllib.parse.unquote(destination))
    else:
        return redirect(url_for("pages.index"))