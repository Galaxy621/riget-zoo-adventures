import base64
import hashlib
import os

import mysql.connector as mysql

from dataclasses import dataclass
from datetime import date, datetime

# Custom singleton type, allows for only one object to be created
# When called, the object gives a reference instead of creating a new one
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if not cls in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

# Helper class for user
# Database info is dumped inside
@dataclass
class User:
    userID: int
    name: str
    email: str
    dateOfBirth: date
    admin: bool
    isStudent: bool
    isCarer: bool
    passwordHash: bytes
    passwordSalt: str

# Helper class for posts
# Database info is dumped inside
# There's also a helper for use inside the webpage, and a sorting dunder method
@dataclass
class Post:
    postID: int
    authorID: int
    creationTime: datetime
    title: str
    contents: str
    unlisted: bool = False

    def get_author(self):
        connector = Connector()
        return connector.get_user_by_id(self.authorID)
    
    def __lt__(self, other):
        return self.postID < other.postID

# Helper class for hotels
# Helpers inside talk with the database to retrieve extra information
@dataclass
class Hotel:
    roomID: int
    name: str
    description: str
    maxOccupants: int
    priceInPennies: int

    allowOverlap: bool = False

    def strip_user(self):
        ...

    def get_occupant(self) -> User | None:
        conn = Connector()
        bookings = conn.query("""

        SELECT bookings.UserID FROM bookings
        INNER JOIN hotels ON bookings.RoomID = hotels.RoomID
        WHERE bookings.RoomID = %s
                                
        """, (self.roomID, ))
        if len(bookings) == 0: return None
        return conn.get_user_by_id(bookings[0][0])

    def formatted_price(self) -> str:
        return "£" + "{:.2f}".format(self.priceInPennies / 100) #£{{"{:.2f}".format()}}

    def check_occupied(self, startDate: datetime, endDate: datetime) -> bool:
        conn = Connector()
        all_bookings = conn.get_all_bookings(self)

        startDateTime = datetime(startDate.year, startDate.month, startDate.day, 9, 0, 0, 0)
        endDateTime = datetime(endDate.year, endDate.month, endDate.day, 9, 0, 0, 0)

        for book in all_bookings:
            if conn.date_range_overlaps_booking(startDateTime, endDateTime, book): return True
        
        return False

# Placeholder Safari information
# This allows the safari experience to be stored in the hotels system
SAFARI = Hotel(
    -1,
    "Safari Experience",
    "Safari Experience",
    100,
    1500,
    True # Allow booking dates to overlap
)

@dataclass
class Booking:
    bookingID: int
    userID: int
    roomID: int
    occupants: int
    cost: int
    purchaseDate: int
    startDate: int
    endDate: int

    def is_old(self):
        return self.startDate < datetime.now()

# Create a singleton (one copy, used everywhere) that stores all database information
# Use this class to query the database, using helper functions to make the job easier
# This allows for easy access in code to menial things, such as getting a user by their ID
class Connector(metaclass=Singleton):
    def __init__(self, hostname: str = "127.0.0.1", username: str = "root", password: str = "password", database: str = None):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.database = database

    def query(self, query: str = None, data: tuple = None, commit: bool = False, multi: bool = False):
        results = []

        try:
            cnx = mysql.connect(
                user = self.username,
                password = self.password,
                host = self.hostname,
                database = self.database
            )

            cursor = cnx.cursor()
            cursor.execute(query, data, multi=multi)

            if commit is not False:
                cnx.commit()

            for i in cursor:
                results.append(i)

        except Exception as err:
            print(f"An error occured: {err}")
        else:
            cnx.close()

        return results

    def archive_post(self, id: int):
        self.query("UPDATE `posts` SET Unlisted = 1 WHERE PostID = %s", (id, ), True)

    def unarchive_post(self, id: int):
        self.query("UPDATE `posts` SET Unlisted = 0 WHERE PostID = %s", (id, ), True)

    def create_post(self, user: User, title: str, contents: str):
        self.query("""
            INSERT INTO `posts`(`AuthorID`, `Title`, `Contents`, `Unlisted`)
            VALUES (%s,%s,%s,%s)
            """,
            (user.userID, title, contents, False),
            True
        )

    def update_post(self, id: int, user: User, title: str, contents: str):
        self.query("""
            UPDATE `posts`
            SET AuthorID = %s, Title = %s, Contents = %s
            WHERE PostID = %s
            """,
            (user.userID, title, contents, id),
            True
        )

    def get_post_by_id(self, id: int):
        posts = self.query("SELECT * FROM `posts` WHERE PostID = %s", (id, ))
        if len(posts) == 0: return None

        post = Post(*posts[0])
        return post

    def get_user_by_email(self, email: str):
        users = self.query("SELECT * FROM `users` WHERE Email = %s", (email,))
        if len(users) == 0: return None
        
        user = User(*users[0])
        return user
    
    def get_user_by_id(self, id: int):
        users = self.query("SELECT * FROM `users` WHERE UserID = %s", (id,))
        if len(users) == 0: return None
        
        user = User(*users[0])
        return user

    def compare_password(self, user: User, password: str) -> bool:
        checkPassword, salt = self.create_password(password, user.passwordSalt)
        return user.passwordHash == checkPassword

    @staticmethod
    def create_password(password, salt: str = None) -> tuple[str]:
        # 16 character salt 
        if salt is None:
            salt = os.urandom(12)
            salt = base64.b64encode(salt).decode('utf-8')

        fullPassword = password + salt

        h = hashlib.new("sha256")
        h.update(fullPassword.encode('utf-8'))
        saltHashPassword = h.hexdigest()

        return (saltHashPassword, salt)

    def set_user_password(self, user: User, password: str):
        saltHashPassword, salt = self.create_password(password)
        data = (saltHashPassword, salt, user.userID)
        self.query("UPDATE `users` SET `PasswordHash`=%s, `PasswordSalt`=%s WHERE `UserID` = %s", data, True)

    def create_account(self, name: str, email: str, password: str, dateOfBirth: date, isStudent: bool = False, isCarer: bool = False) -> User:
        saltHashPassword, salt = self.create_password(password)
    
        data = (name, email, dateOfBirth, isStudent, isCarer, saltHashPassword, salt)
        self.query("INSERT INTO `users`(`Name`, `Email`, `DateOfBirth`, `IsStudent`, `IsCarer`, `PasswordHash`, `PasswordSalt`) VALUES (%s, %s, %s, %s, %s, %s, %s)", data, True)

        user = self.get_user_by_email(email)
        return user
    
    def get_unoccupied_hotels(self):
        # rooms = self.query("SELECT * FROM `hotels` WHERE OccupantID IS NULL")
        rooms = self.query("""
            SELECT *
            FROM hotels
            WHERE NOT EXISTS
                (
                    SELECT 1
                    FROM bookings
                    WHERE bookings.RoomID = hotels.RoomID
                )
        """)
        data = [Hotel(*room) for room in rooms] # Convert raw data into classes
        return data
    
    def get_hotels(self):
        rooms = self.query("SELECT * FROM hotels where 1")
        data = [Hotel(*room) for room in rooms] # Convert raw data into classes
        return data


    def get_hotel_by_id(self, id: int):
        if id == "safari" or id == "-1": return SAFARI

        rooms = self.query("SELECT * FROM `hotels` WHERE RoomID = %s", (id,))
        if len(rooms) == 0: return None
        
        room = Hotel(*rooms[0])
        return room

    def get_booking_by_id(self, id: int):
        books = self.query("SELECT * FROM `bookings` WHERE BookingID = %s", (id,))
        if len(books) == 0: return None

        booking = Booking(*books[0])
        return booking

    def get_all_bookings(self, room: Hotel):
        bookings = self.query("SELECT * FROM `bookings` WHERE RoomID = %s", (room.roomID,))
        return [Booking(*book) for book in bookings]
    
    def get_user_bookings(self, user: User):
        bookings = self.query("SELECT * FROM `bookings` WHERE UserID = %s", (user.userID,))
        return [Booking(*book) for book in bookings]

    def create_booking(self, room: Hotel, user: User, startDate: date, endDate: date, costPerDay: int, occupants: int):

        days = (endDate - startDate).days
        fullPrice = costPerDay * days

        startDateTime = datetime(startDate.year, startDate.month, startDate.day, 9, 0, 0, 0)
        endDateTime = datetime(endDate.year, endDate.month, endDate.day, 9, 0, 0, 0)

        booking = self.query("""

INSERT INTO bookings (UserID, RoomID, Occupants, Cost, StartDate, EndDate)
VALUES (%s, %s, %s, %s, %s, %s)
                             
""", (user.userID, room.roomID, occupants, fullPrice, startDateTime, endDateTime), commit=True)
        print(booking)
        
        return {"days": days, "price": fullPrice, "start": startDateTime, "end": endDateTime}
        
    def date_range_overlaps_booking(self, startDate: datetime, endDate: datetime, booking: Booking):

        if booking.roomID == -1: return False

        # Starts During a stay
        if startDate >= booking.startDate and startDate <= booking.endDate: return True     
        
        # Ends During a stay   
        if endDate >= booking.startDate and endDate <= booking.endDate: return True

        # Starts before and ends after a stay
        if startDate < booking.startDate and endDate > booking.endDate: return True

        return False
    
# Initialise the connector with connection information
# This is hidden from the user, so they cannot access the database
CONNECTOR_INST = Connector(
    "192.168.82.243",
    "tlevel2",
    "Bentley1",
    "tlevel2"
) 