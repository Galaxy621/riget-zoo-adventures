from datetime import date, datetime
from math import floor
from flask import Blueprint, render_template, request, session, redirect, url_for

from common import get_boolean_js
from connector import Connector

bp = Blueprint("hotel", __name__)

@bp.route("/hotels")
def hotels():
    connector = Connector()
    data = connector.get_hotels()
    return render_template("hotels.html.j2", hotels = data)

@bp.route("/hotels/<id>")
def hotel(id: int):
    connector = Connector()
    data = connector.get_hotel_by_id(id)

    if data is None: return "That hotel doesn't exist :("
    thumbnails = []

    return render_template("hotelpage.html.j2", hotel = data, thumbnails = thumbnails, thumbinfo = url_for('static', filename=f"hotels/{data.roomID}/info.json"))

@bp.route("/cancel/<booking_id>")
def cancel_booking(booking_id: int):
    user = session.get("user")
    if not user: return "No user"

    connector = Connector()
    booking = connector.get_booking_by_id(booking_id)
    if not booking: return "No booking"

    if user["userID"] != booking.userID:
        return "Not their booking"
    
    if booking.startDate < datetime.now():
        return "Too late to cancel"
    
    connector.query("DELETE FROM `bookings` WHERE BookingID = %s", (booking_id, ), True)
    return redirect(url_for("account.account"))

@bp.route("/available", methods=["POST"])
def available():
    connector = Connector()
    
    hotel = request.form.get("hotel")
    if hotel is None: return {"success": False, "reason": "A hotel hasn't been provided"}
    hotel = connector.get_hotel_by_id(hotel)
    if hotel is None: return {"success": False, "reason": "An invalid hotel has been provided"}

    startDate = request.form.get("startDate")
    print(f"{startDate = }")
    if startDate == "NaN" or startDate == "": return {"success": False, "reason": "A start date hasn't been provided"}
    startDate = date.fromtimestamp(int(startDate) / 1000)
    if startDate < datetime.now().date(): return {"success": False, "reason": "The provided start date is before today"}

    endDate = request.form.get("endDate")
    if endDate == "NaN" or endDate == "": return {"success": False,"reason": "An end date hasn't been provided"}
    endDate = date.fromtimestamp(int(endDate) / 1000)
    if endDate <= startDate: return {"success": False, "reason": "Please select a date after the start date"}

    return {"success": True, "value": not hotel.check_occupied(startDate, endDate)}


@bp.route("/book/<hotel_id>", methods=["GET", "POST"])
def book(hotel_id):
    connector = Connector()
    data = connector.get_hotel_by_id(hotel_id)

    if request.method == "GET":        
        return render_template("book.html.j2", hotel = data)

    if data is None:
        return {"success": False, "reason": "This is not a valid hotel"}

    # Date Checks

    startDate = request.form.get("startDate")
    if startDate == "NaN": return {"success": False, "type": "dates", "reason": "A start date hasn't been provided"}
    startDate = date.fromtimestamp(int(startDate) / 1000)
    if startDate < datetime.now().date(): return {"success": False, "type": "dates", "reason": "The provided start date is before now"}

    endDate = request.form.get("endDate")
    if endDate == "NaN": return {"success": False, "type": "dates", "reason": "An end date hasn't been provided"}
    endDate = date.fromtimestamp(int(endDate) / 1000)
    if endDate <= startDate: return {"success": False, "type": "dates", "reason": "Please select a date after the start date"}

    if (endDate - startDate).days / 7 > 1:
        return {"success": False, "type": "dates", "reason": "You can only book up to one week in advance"}

    if data.check_occupied(startDate, endDate):
        return {"success": False, "type": "dates", "reason": "This hotel is already booked during this period"}

    # Occupant checks

    occupantCount = request.form.get("occupantCount")
    occupantCount = int(occupantCount)

    if occupantCount <= 0:
        return {
            "success": False,
            "type": "occupants",
            "reason": "You must have at least 1 occupant"
        }
    
    if occupantCount > data.maxOccupants:
        return {
            "success": False,
            "type": "occupants",
            "reason": f"There is a maximum of {data.maxOccupants} occupants."
        }

    maxAge = 0

    occupantInfo = []
    for i in range(occupantCount):
        occupant = {
            "name": request.form.get(f"occupants[{i}][name]"),
            "dob": request.form.get(f"occupants[{i}][dob]"),
            "student": get_boolean_js(request.form.get(f"occupants[{i}][student]")),
            "carer": get_boolean_js(request.form.get(f"occupants[{i}][carer]")),
        }


        if occupant["name"] == "":
            return {
                "success": False,
                "type": f"occupant-{i + 1}",
                "reason": "Please provide a name"
            }

        dob = date.fromisoformat(occupant["dob"])
        
        if dob < date(1900, 1, 1) or dob > date.today():
            return {
                "success": False,
                "type": f"occupant-{i + 1}",
                "reason": "Please provide a valid date of birth"
            }

        ageDelta = date.today() - dob
        age = floor(ageDelta.days / 365)
        maxAge = max(maxAge, age)

        occupant["age"] = age
        occupantInfo.append(occupant)

    if maxAge < 18:
        return {
            "success": False,
            "type": "occupants",
            "reason": f"There must be at least one adult"
        }

    user = session.get("user")

    # Price calculation

    price = 0

    for occupant in occupantInfo:
        if occupant["age"] <= 4: continue # Four and ender get free entry
        if occupant["age"] >= 65: continue # 65 and over get free entry
        if occupant["carer"]: continue # Carers get free entry

        mult = 1
        
        if occupant["age"] <= 12: mult *= 0.8 # Under 12s get 20% off
        if occupant["student"]: mult *= 0.8 # Students get 20% off

        price += data.priceInPennies * mult

    price = round(price)

    if not user: return {"success": False, "reason": "You need to be logged in"}

    finalBookingInfo = connector.create_booking(
        data,
        connector.get_user_by_id(user["userID"]),
        startDate,
        endDate,
        price,
        occupantCount
    )

    return {"success": True, "reason": "", "data": finalBookingInfo}