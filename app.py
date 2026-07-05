import base64
import datetime
import json
import os
import random
import re
import smtplib
from email.message import EmailMessage
from functools import wraps
from io import BytesIO
import qrcode 
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

BOOKINGS_FILE = "Railway_data.json"
USERS_FILE = "users.json"

TRAINS = [
        {
            "train_no":"T101",
            "name":"Express A",
            "from":"Delhi",
            "to":"Mumbai",
            "departure":"09:00",
            "arrival":"18:00",
            "seats":{"SL":10,"3A":8,"2A":5}
        },
        {
            "train_no":"T102",
            "name":"Rajdhni B",
            "from":"Delhi",
            "to":"kolkata",
            "departure":"10:00",
            "arrival":"20:00",
            "seats":{"SL":12,"3A":6,"2A":4}
        },
        {
            "train_no":"T103",
            "name":"Duronto c",
            "from":"Delhi",
            "to":"chennai",
            "departure":"7:00",
            "arrival":"22:00",
                "seats":{"SL":15,"3A":10,"2A":6}
        },
        {
            "train_no":"up101",
            "name":"Varanasi Shatabdi",
            "from":"varanasi",
            "to":"Delhi",
            "departure":"6:00",
            "arrival":"15:00",
            "seats":{"SL":18,"3A":12,"2A":6}
        },
        {
            "train_no":"up102",
            "name":"kanpur Intercity",
            "from":"kanpur",
            "to":"dehli",
            "departure":"5:00",
            "arrival":"14:00",
            "seats":{"SL":20,"3A":12,"2A":6}
        },
        {
            "train_no":"up103",
            "name":"Gorakhpur Express",
            "from":"Delhi",
            "to":"kolkata",
            "departure":"10:00",
            "arrival":"20:00",
            "seats":{"SL":12,"3A":6,"2A":4}
        },
        {
            "train_no":"up104",
            "name":"Prayagraj Express ",
            "from":"Prayagraj",
            "to":"Delhi",
            "departure":"21:30",
            "arrival":"07:00",
            "seats":{"SL":20,"3A":12,"2A":6}
        },
        {
            "train_no":"up105",
            "name":"lucknow Mail",
            "from":"Delhi",
            "to":"lucknow",
            "departure":"22:00",
            "arrival":"06:00",
            "seats":{"SL":25,"3A":10,"2A":9}
        },
        {
            "train_no":"Tup106",
            "name":"Agra Intercity",
            "from":"Agra",
            "to":"lucknow",
            "departure":"07:00",
            "arrival":"10:00",
            "seats":{"SL":14,"3A":8,"2A":4}
        },
        {
            "train_no":"T107",
            "name":"Meerut Express ",
            "from":"Delhi",
            "to":"Meerut",
            "departure":"08:30",
            "arrival":"10:30",
            "seats":{"SL":30,"3A":12,"2A":5}
        },
        {
            "train_no":"up108",
            "name":"Bareilly Mail",
            "from":"Bareilly",
            "to":"Delhi",
            "departure":"5:45",
            "arrival":"12:00",
            "seats":{"SL":18,"3A":8,"2A":4}
        },
        {
            "train_no":"up109",
            "name":"Noida Express",
            "from":"lucknow",
            "to":"Noida",
            "departure":"09:30",
            "arrival":"16:30",
            "seats":{"SL":21,"3A":11,"2A":6}
        },
        {
            "train_no":"up110",
            "name":"YogacExpress",
            "from":"jaipur",
            "to":"Delhi",
            "departure":"10:50",
            "arrival":"04:50",
            "seats":{"SL":32,"3A":8,"2A":10}
        }
]
FARE_SHART = {"SL":600,"3A":1000,"2A":1500}
app = Flask(__name__)
app.secret_key = "replace-rhis-with-a-secure-random-value"
EMAIL_USER = os.environ.get("RAILWAY_APP_EMAIL","gmansstar2314@gmail.com")
EMAIL_PASS = os.environ.get("RAILWAY_APP_EMAIL","vfzqshhzywfazjgf")
OTP_EXPIRAY_MINUTES = 5
OTP_STORE : dict[str,dict[str,datetime.datetime|str]] = {}
PENDING_REGISTRATION  = {}

def load_json (filename):
    if os.path.exists(filename):
        with open(filename,"r",encoding = "utf-8") as f :
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return{}
    return{}

def save_json(filename,data):
    with open(filename,"w",encoding="utf-8") as f :
        json.dump(data , f, indent = 4)

def send_email(subject,body,to_email,attachments=None):
    if not EMAIL_USER or not EMAIL_PASS:
        raise RuntimeError("Email credentials are not configured.")
    msg = EmailMessage()
    msg["subject"] = subject
    msg["From"] = EMAIL_USER
    msg["TO"] = to_email
    msg.set_content(body)
    attachments = attachments or []
    for attachment in attachments:
        filename, mime_type , data = attachment
        maintype , subtype = mime_type.split("/") 
        msg.add_attachment(data,maintype = maintype,subtype = subtype,filename = filename)
    with smtplib.SMTP_SSL("smtp.gmail.com",465) as smtp:
        smtp.login(EMAIL_USER,EMAIL_PASS)
        smtp.send_message(msg)

def generate_otp():
    return str(random.randint(100000,999999))

def send_otp_email(email):
    otp = generate_otp()
    OTP_STORE[email] = {
        "otp": otp,
        "expire_at": datetime.datetime.utcnow() + datetime.timedelta(minutes=OTP_EXPIRAY_MINUTES),
    } 
    body = (
        "Indian Railway Booking System\n\n"
        f"your One Time Password (OTP) is:{otp}\n"
        f"This code is valid for {OTP_EXPIRAY_MINUTES} minutes.\n\n"
        "If you did not request this , please ignore this email." 
    )
    send_email("Your OTP for Railway Booking",body,email)

def verify_otp(email, entered_otp):
    record = OTP_STORE.get(email)
    if not record:
        return False
    if record["expire_at"] < datetime.datetime.utcnow():
        del OTP_STORE[email]
        return False
    if record["otp"] != entered_otp:
        return False
    del OTP_STORE[email]
    return True

def send_ticket_email(to_email,ticket,qr_bytes):
    jorney_details = (
        f"PNR : {ticket['PNR']}\n"
        f"Train : {ticket['Train']} ({ticket['Train No']})\n"
        f"Route : {ticket['From']} -> {ticket['To']}\n"
        f"Class : {ticket['Class']}\n"
        f"Journey Date: {ticket['Journey Date']}\n"
        f"Departure: {ticket['Departure']}\n"
        f"Arrivel: {ticket['Fare']}\n"
        f"Fare:₹{ticket['Fare']}\n"
        f"Status: {ticket['Status']}\n"
    )
    body = (
        "Thank you for booking with Indian Railway Booking System.\n\n"
        "your ticket details aare below:\n\n"
        f"{jorney_details}\n"
        "Scan the attached QR code at the station for quick access to your ticket.\n\n"
        "Have a safe journey!"
    )
    attachments = []
    if qr_bytes:
        attachments.append(("ticket_qr.png","image/png", qr_bytes))
    send_email("Yor Railway E-Ticket", body , to_email,attachments=attachments)

def get_users():
    return load_json(USERS_FILE)

def save_users(users):
    save_json(USERS_FILE,users)

def get_booking():
    return load_json(BOOKINGS_FILE)

def save_bookings(bookings):
    save_json(BOOKINGS_FILE,bookings)

def generate_pnr():
    return str(random.randint(1000000000,9999999999))

def validate_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern,email) is not None

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1,box_size=10,border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black",back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

def qr_to_base64(data = None, buffer = None):
    if buffer is None:
        if data is None:
            raise ValueError("Enter data or buffer must be provided for QR conversion.")
        buffer = generate_qr_code(data)
    else:
        buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

def valid_journey_date(date_str):
    try:
        journey_date = datetime.datetime.strptime(date_str,"%Y-%m-%d").date()
    except ValueError:
        return False
    today = datetime.date.today()
    delta = (journey_date - today).days
    return 0 <= delta <= 60

def login_required(view):
    @wraps(view)
    def wrapper_view(*args, **kwargs):
        if "user_email" not in session:
            flash("Please login in to continue.","warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapper_view 
    
def get_train(train_no):
    return next((train for train in TRAINS if train["train_no"] == train_no), None)

@app.context_processor
def inject_globals():
    return {
        "logged_in": 'user_email' in session,
        "current_user": session.get("user_email"),
        "datetime":datetime,
    }

@app.template_filter("datetimeformat")
def datetimeformat(value, fmt="%Y-%m-%d"):
    if not value:
       return ""
    try:
        parsed = datetime.datetime.strptime(value, "%d-%m-%Y")
        return parsed.strftime(fmt)
    except ValueError:
        return value
    
@app.route("/")
def home():
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    bookings = get_booking()
    user_bookings = [
        bookings[pnr]
        for pnr in get_users().get(session['user_email'], {}).get("bookings", [])
        if pnr in bookings
    ]
    return render_template("dashboard.html", bookings=user_bookings, trains=TRAINS)

@app.route("/register", methods=["GET", "POST"])
def register():
    form_data = {}
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        password = request.form.get("password","")
        confirm_password = request.form.get("confirm_password","")
        otp = request.form.get("otp","").strip()
        form_data = {"email": email}
        user = get_users()
        errors = []
        if not email or not password:
            errors.append("Email and password are required.")
        elif not validate_email(email):
            errors.append("Invalid email address.")
        elif email in user:
            errors.append("Account already exists. please login.")
        elif password != confirm_password:
            errors.append("Passwords do not match.")
        elif len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if"send_otp" in request.form:
            if errors:
                for error in errors:
                    flash(error, "danger")
            else:
                try:
                    send_otp_email(email)
                    PENDING_REGISTRATION[email] = password
                    flash("OTP sent to your email address.","success")
                except RuntimeError as e:
                    flash(str(exc), "danger")
                except Exception as exc:
                    app.logger.exception(f"Failed to send registration OTP",exc_info=exc)
                    flash("Unable to send OTP right now. Please try again later.","danger")
        elif "register" in request.form:
            if errors:
                for error in errors:
                    flash(error, "danger")
            elif not otp:
                flash("Please enter the OTP sent to your email address.", "danger")
            elif email not in PENDING_REGISTRATION:
                flash("Please request a new OTP before registering.", "warning")
            elif not verify_otp(email, otp):
                flash("Invalid or expired OTP. Please request a new one.", "danger")
            else:
                user[email] = {"password": password, "bookings": []}
                save_users(user)
                PENDING_REGISTRATION.pop(email,None)
                flash("Registration successful please log in.", "success")
                return redirect(url_for("login"))
    return render_template("register.html", form_data=form_data)

@app.route("/login", methods=["GET", "POST"])
def login():
    form_data = {}
    if request.method == "POST":
        email = request.form.get("email","").strip().lower()
        otp = request.form.get("otp","").strip()
        form_data = {"email": email}
        user = get_users()
        if "send_otp" in request.form:
            if not email:
                flash("Please enter your registered email.", "danger")
            elif email not in user:
                flash("No account found with this email. Please register first.", "warning")
            else:
                try:
                    send_otp_email(email)
                    session["pending_login"] = email
                    flash("OTP sent to your email address.","success")
                except RuntimeError as exc:
                    flash(str(exc),"danger")
                except Exception as exc:
                    app.logger.exception("Failed to send login OTP", exc_info=exc)
                    flash("Unable to send OTP right now. Please try again later.", "danger")
            
        elif "verify_otp" in request.form:
            if not email or email != session.get("pending_login"):
                flash("Please request an OTP for this email first.", "warning")
            elif not otp:
                flash("Please enter the OTP sent to your email address.", "danger")
            elif not verify_otp(email, otp):
                flash("Invalid or expired OTP. Please request a new one.", "danger")
            else:
                session.pop("pending_login", None)
                session["user_email"] = email
                flash("Login successful.", "success")
                return redirect(url_for("dashboard"))
    return render_template("login.html", form_data=form_data)

@app.route("/logout")
def logout():
    session.pop("user_email",None)
    session.pop("Pending_login",None)
    flash("Logged out successfully.","info")
    return redirect(url_for("login"))

@app.route("/book",methods = ["GET","POST"])
@login_required
def book_ticket():
    if request.method == "POST":
        name = request.form.get("name","").strip()
        age = request.form.get("age","")
        mobile = request.form.get("mobile","").strip()
        nationality = request.form.get("nationality","Indian").strip()
        address = request.form.get("address","").strip()
        from_station = request.form.get("from_station","").strip()
        to_station = request.form.get("to_station","").strip()
        journey_date = request.form.get("journey_date","")
        train_no = request.form.get("train_no","")
        travel_Class = request.form.get("Class","")
        train = get_train(train_no) if train_no else None
        if not all([name,age,mobile,from_station,to_station,journey_date,train_no,travel_Class]):
            flash("Please fill out all required fields.", "danger")
        elif not valid_journey_date(journey_date):
            flash("Journey date must be within 60 days from today.", "danger")
        else:
            try: 
                age = int(age)
            except (TypeError, ValueError):
                flash("Please enter a valid age.", "danger")
                return render_template("book_ticket.html", trains=TRAINS)
            if age < 1 or age > 120:
                flash("Please enter a valid age between 1 and 120.", "danger")
                return render_template("book_ticket.html", trains=TRAINS)
            if train ["seats"].get(travel_Class, 0) <= 0:
                flash(f"No seats available in {travel_Class} class.", "danger")
            else:
                train["seats"][travel_Class] -= 1
                bookings = get_booking()
                pnr = generate_pnr()
                fare = FARE_SHART.get(travel_Class)
                booking_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
                ticket = {
                    "PNR": pnr,
                    "user":session["user_email"],
                    "Name": name,
                    "From": from_station,
                    "To": to_station,
                    "Mobile": mobile,
                    "Age": age,
                    "Nationality": nationality,
                    "Address": address,
                    "journey date": datetime.datetime.strptime(journey_date,"%Y-%m-%d").strftime("%d-%m-%Y"),
                    "Train": train["name"],
                    "Train_no": train["train_no"],
                    "Class": travel_Class,
                    "Fare": fare,
                    "Departure": train["departure"],
                    "Arrival": train["arrival"],
                    "Booking_time": booking_time,
                    "Status": "Confirmed"
                }
                bookings[pnr] = ticket
                save_bookings(bookings)
                users = get_users()
                users[session["user_email"]]["bookings"].append(pnr)
                save_users(users)
                qr_payload = {
                    f"PNR: {pnr}\n",
                    f"Name: {name}\n",
                    f"Train: {train['name']} ({train['train_no']})\n",
                    f"From: {from_station} to {to_station}\n",
                    f"Class: {travel_Class}\n",
                    f"Fare: Rs.{fare}\n"
                    f"Journey Date: {ticket['journey date']}\n",
                    f"Status: {ticket['Status']}\n"
                }
                qr_buffer = generate_qr_code(qr_payload)
                qr_bytes = qr_buffer.getvalue()
                qr_image = qr_to_base64(buffer = BytesIO(qr_bytes))
                try:
                    send_ticket_email(session["user_email"], ticket, qr_bytes)
                except RuntimeError as exc:
                    flash("ticket booked successfully, but email delivery is not configured:{exc}","warning")
                except Exception as exc:
                    app.logger.exception("Failed to send ticket email", exc_info=exc)
                    flash("Ticket booked, but failed to send confirmation email. Please check your bookings.", "warning")
                else:
                    flash("Ticket booked successfully! A confirmation email has been sent.", "success")
                return render_template("ticket_confirmation.html", ticket=ticket, qr_image=qr_image)
        return render_template("book_ticket.html", trains=TRAINS)
    
@app.route("/bookings")
@login_required
def view_booking():
    bookings = get_booking()
    users = get_users()
    user_booking_ids = users.get(session["user_email"],{}).get("bookinhs",[])
    user_ticket = [bookings[pnr] for pnr in user_booking_ids if pnr in bookings]
    return render_template("booking.html",ticket=user_ticket)
    
@app.route("/book_ticket", methods=["GET", "POST"])
@login_required
def cancel_booking(pnr):
    booking = get_booking()
    ticket = booking.get(pnr)
    if not ticket or ticket["user"] != session["user_email"]:
        flash("Booking not found.", "danger")
        return redirect(url_for("view_bookings"))
    if ticket["Status"] == "Cancelled":
        flash("Only confirmed bookings can be cancelled.", "warning")
        return redirect(url_for("view_bookings"))    
    ticket["Status"] = "Cancelled"
    booking[pnr] = ticket
    save_bookings(booking)
    flash(f"Ticket cancelled. Refund amount: rs.{ticket['fare'] * 0.8:0f}",'info')
    return redirect(url_for("view_bookings"))

@app.route("/booking/<pnr>/edit", methods=["GET", "POST"])
@login_required
def edit_booking(pnr):
    booking = get_booking()
    ticket = booking.get(pnr)
    if not ticket or ticket["user"] != session["user_email"]:
        flash("Booking not found.", "danger")
        return redirect(url_for("view_bookings"))
    if request.method == "POST":
        name = request.form.get("name","").strip()
        age = request.form.get("age","")
        nationality = request.form.get("nationality","").strip()
        address = request.form.get("address","").strip()
        journey_date = request.form.get("journey_date","")
        travel_class = request.form.get("class","")
        train = get_train(ticket["Train_no"])
        if not all([name, age, nationality, address, journey_date, travel_class]):
            flash("Please fill out all required fields.", "danger")
        elif not valid_journey_date(journey_date):
            flash("Journey date must be within 60 days from today.", "danger")
        else:
            try:
                age = int(age)
            except (TypeError, ValueError):
                flash("Please enter a valid age.", "danger")
                return render_template("edit_booking.html", ticket=ticket)
            if age < 1 or age > 120:
                flash("Please enter a valid age between 1 and 120.", "danger")
                return render_template("edit_booking.html", ticket=ticket,trains=TRAINS)
            if travel_class != ticket["Class"]:
                if train["seats"].get(travel_class, 0) <= 0:
                    flash(f"No seats available in {travel_class} class.", "danger")
                    return render_template("edit_booking.html", ticket=ticket,trains=TRAINS)
                    train["seats"][ticket["class"]] += 1
                    train["seats"][travel_class] -= 1
            ticket["Name"] = name
            ticket["Age"] = age
            ticket["Nationality"] = nationality
            ticket["Address"] = address
            ticket["class"] = travel_class
            ticket["journey date"] = datetime.datetime.strptime(journey_date,"%Y-%m-%d").strftime("%d-%m-%Y")
            ticket["Fare"] = FARE_SHART.get(travel_class)
            ticket["Booking_time"] = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
            booking[pnr] = ticket
            save_bookings(booking)
            flash("Booking updated successfully.", "success")
            return redirect(url_for("view_bookings"))
    return render_template("edit_booking.html", ticket=ticket,trains=TRAINS)

@app.route("/pnr", methods=["GET", "POST"])
def track_pnr():
    ticket = None
    if request.method == "POST":
        pnr = request.form.get("pnr","").strip()
        if not pnr:
            flash("Please enter  a pnr number.", "danger")
        else:
            booking = get_booking()
            ticket = booking.get(pnr)
            if not ticket:
                flash("PNR not found.", "danger")
            else:
                qr_payload = {
                    f"PNR: {ticket['PNR']}\n",
                    f"Name: {ticket['Name']}\n",
                    f"Train: {ticket['Train']} ({ticket['Train_no']})\n",
                    f"From: {ticket['From']} to {ticket['To']}\n",
                    f"Class: {ticket['class']}\n",
                    f"Fare: Rs.{ticket['Fare']}\n"
                    f"Journey Date: {ticket['journey date']}\n"
                    f"Status: {ticket['Status']}\n"
                }
                ticket["qr_image"] = qr_to_base64(data=qr_payload)
    return render_template("track_pnr.html", ticket=ticket)

@app.route("/bookings/clear", methods=["POST"])
@login_required
def clear_bookings():
    users = get_users()
    bookings = get_booking()
    users_bookings_ids = users.get(session["user_email"], {}).get("bookings", [])
    for pnr in users_bookings_ids:
        bookings.pop(pnr, None)
    users[session["user_email"]]["booking"] = []
    save_bookings(bookings)
    save_users(users)
    flash("All booking cleared successfully.", "info")
    return redirect(url_for("view_dashboard"))

if __name__ == "__main__":
    app.run(debug=True)