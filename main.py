import json
import random
import datetime
import os
import re
import qrcode 
from io import BytesIO
import smtplib
from email.message import EmailMessage
import streamlit as st
BOOKINGS_FILE = "Railway_data.json"
USER_FILE = "Users.json"
def load_json(filename):
    if os.path.exists(filename):
        with open(filename,"r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return{}
    return{}
def save_json(filename,data):
    with open(filename,"w") as f:
        json.dump(data,f,indent=4)

if "bookings" not in st.session_state:
    st.session_state.bookings = load_json(BOOKINGS_FILE)
if "users" not in st.session_state:
    st.session_state.users = load_json(USER_FILE)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "otp_store" not in st.session_state:
    st.session_state.otp_store = {}
if "trains" not in st.session_state:
    st.session_state.trains = [
        {
            "train_no":"T101",
            "name":"Express A",
            "from":"Delfi",
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
            "from":"Dlile",
            "to":"chennai",
            "departure":"7:00",
            "arrival":"22:00",
                "seats":{"SL":15,"3A":10,"2A":6}
        },
        {
            "train_no":"up101",
            "name":"Varanasi Sharabdi",
            "from":"varanasi",
            "to":"Delhi",
            "departure":"6:00",
            "arrival":"15:00",
            "seats":{"SL":18,"3A":12,"2A":6}
        },
        {
            "train_no":"up102",
            "name":"kanpur Intersity",
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
fare_chart = {"SL":600,"3A":1000,"2A":1500}
def generate_pnr():
    return str(random.randint(100000000000,999999999999)) 

def validata_email(email):
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def send_otp_email(to_email):
    otp = str(random.randint(100000,999999))
    st.session_state.otp_store[to_email] = otp
    msg = EmailMessage()
    msg['Subject'] = "your otp for Railway booking"
    msg['From'] = "your_email@gamil.com"
    msg['To'] = to_email
    msg.set_content(f"your otp is:{otp}")
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com',465) as smtp:
            smtp.login("Ayushbro779@gmail.com","okaupcpqfgudzygc")
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send otp:{e}")
        return False
    
def verify_otp(email,entered_otp):
    return st.session_state.otp_store.get(email) == entered_otp

def valid_journey_date(journey_date):
    today = datetime.date.today()
    delta = (journey_date-today).days
    return 0 <= delta <= 60

def generate_qr_code(data):
    qr = qrcode.QRCode(version=1,box_size=10,border = 5)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black",back_color="white")
    buffer = BytesIO()
    img.save(buffer,format="PNG")
    buffer.seek(0)
    return buffer

def display_ticket(ticket):
    st.markdown("---")
    st.subheader("INDIAN RAILWAYS E-TICKET")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("PNR Number",ticket["PNR"])
    with col2:
        st.metric("Booking Time", ticket["Booking iTme"])
    with col3:
        st.metric("Status", ticket["Status"])
    st.markdown("---")

    st.write("Passenger Details")
    col1 , col2 = st.columns(2)
    with col1:
        st.write(f"Name : {ticket['Name']}")
        st.write(f"Age:{ticket['Age']}")
        st.write(f"Mobile:{ticket['Mobile']}")
    with col2:
        st.write(f"Nationality:{ticket['Nationality']}")
        st.write(f"Address:{ticket['Address']}")
    st.markdown("---")

    st.write("Train Details")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Train Name: {ticket['Train']}")
        st.write(f"Train Number: {ticket['Train No']}")
    with col2:
        st.write(f"Class: {ticket['Class']}")
        
    st.markdown("---")

    st.write("Journey Details")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"Form: {ticket['From']}")
        st.write(f"To: {ticket['To']}")
        st.write(f"Journey Date: {ticket['Journey Date']}")
    with col2:
        st.write(f"Departure: {ticket['Departure']}")
        st.write(f"Arrival: {ticket['Arrival']}")
    st.markdown("---")

    st.write("Payment Details")
    st.write(f"Total Fare: Rs.{ticket['Fare']}")
    st.markdown("---")

def register_page():
    st.title("Register New Account")
    email = st.text_input("Email Address", key="register_email").strip().lower()
    password = st.text_input("Password",type="password")
    confirm_password = st.text_input("confirm password", type="password")
    if st.button("Send OTP"):
        if not validata_email(email):
            st.error("Invalid email format!")
        elif email in st.session_state.users:
            st.error("Account already exists. please login.")
        elif password != confirm_password:
            st.error("passwords do not match!")
        elif len(password) < 6:
            st.error("password must be at least 6 characters!")
        else:
            if send_otp_email(email):
                st.success("OTP sent to your email!")
                st.session_state.pending_register = {"email": email, "password" : password}
    if "pending_register" in st.session_state:
        otp_input = st.text_input("Enetr OTP sent to your email")
        if st.button("verify OTP"):
            if verify_otp(st.session_state.pending_register["email"],otp_input):
                email = st.session_state.pending_register["email"]
                st.session_state.users[email] = {"password":st.session_state.pending_register["password"],"bookings":[]}
                save_json(USER_FILE,st.session_state.users)
                st.success("Registration successful! please login now.")
                del st.session_state.pending_register
            else:
                st.error("Invalid OTP. Try again.")

def login_page():
    st.title("Login to our Account")
    email = st.text_input("Email Address", key = "login_email").strip().lower()
    if st.button("Send OTP for login"):
        if email not in st.session_state.users:
            st.error("No account found. please register first.")
        else:
            if send_otp_email(email):
                st.success("OTP send to your email!")
                st.session_state.pending_login = email
    if "pending_login" in st.session_state:
        otp_input = st.text_input("Enter OTP sent to your email")
        if st.button("Verify OTP login"):
            if verify_otp(st.session_state.pending_login,otp_input):
                st.session_state.logged_in = True
                st.session_state.current_user = st.session_state.pending_login
                st.success(f"Login successful! Welcome, {st.session_state.current_user}")
                del st.session_state.pending_login
                st.rerun()
            else:
                st.error("Invalid OTP. Try again.")

def booking_page():
    st.title("Book your Train Ticket")
    with st.form("booking+from"):
        st.subheader("Passenger Information")
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            age = st.number_input("Age", min_value = 1, max_value = 120, value = 25)
            mobile = st.text_input("Mobile Number")
        with col2:
            nationality = st.text_input("Nationality", value = "Indian")
            address = st.text_area("Address")
        st.subheader("Journey Details")
        col3 , col4 = st.columns(2)
        with col3:
            from_station = st.text_input("From Station")
        with col4:
            to_station = st.text_input("To Station")

        max_date = datetime.date.today() + datetime.timedelta(days=60)
        journey_date = st.date_input(
            "Journey Date",
            min_value = datetime.date.today(),
            max_value = max_date,
            help = "Booking allowed only up to 60 days in advance"
        )
        st.subheader("Trains selection")
        trains_options = []
        for i, t in enumerate(st.session_state.trains):
            seats_info = f"SL:{t['seats']['SL']} | 3A:{t['seats']['3A']} |  2A:{t['seats']['2A']}"
            trains_options.append(
                f"{t['name']} ({t['train_no']}) - {t['from']} to {t['to']} | "
                f"Dep: {t['departure']} Arr: {t['arrival']} | Seats: {seats_info}"
            )
        selected_train_idx = st.selectbox(
            "Select Train",
            range(len(st.session_state.trains)),
            format_func=lambda x: trains_options[x]      
        )
        selected_train = st.session_state.trains[selected_train_idx]
        available_classes = []
        for cls in ["SL","3A","2A"]:
            if selected_train["seats"][cls] > 0:
                available_classes.append(f"{cls} (Rs.{fare_chart[cls]}) - {selected_train["seats"][cls]}seats")
            else:
                available_classes.append(f"{cls}(Rs.{fare_chart[cls]}) - SOLD OUT")
        cls_display = st.selectbox("select class",available_classes)
        cls = cls_display.split()[0]
        submit = st.form_submit_button("Book Ticket", use_container_width=True)
        if submit:
            if not all([name,mobile,from_station,to_station]):
                st.error("please fill all requires fields!")
            elif not valid_journey_date(journey_date):
                st.error("Booking allowed only up to 60 days in advanci!")
            elif selected_train["seats"][cls] <= 0:
                st.error(f"No seats available in {cls} class. please choose another class or train.")
            else:
                train = selected_train
                fare = fare_chart[cls]
                pnr = generate_pnr()
                st.session_state.trains[selected_train_idx]["seats"][cls] -= 1

                ticket = {
                    "PNR": pnr,
                    "User": st.session_state.current_user,
                    "Name": name,
                    "From": from_station,
                    "To": to_station,
                    "Mobile": mobile,
                    "Age": age,
                    "Nationality": nationality,
                    "Address": address,
                    "Journey Date": journey_date.strftime("%d-%m-%Y"),
                    "Train": train["name"],
                    "Train No": train["train_no"],
                    "Class": cls,
                    "Fare": fare,
                    "Departure": train["departure"],
                    "Arrival": train["arrival"],
                    "Booking Time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M"),
                    "Status": "CONFIRMED"
                }
                st.session_state.bookings[pnr] = ticket
                save_json(BOOKINGS_FILE,st.session_state.bookings)
                st.session_state.users[st.session_state.current_users]["bookings"].append(pnr)
                save_json(USER_FILE,st.session_state.users)
                st.success("Ticket Booked Successfully!")
                qr_data = (
                    f"PNR: {pnr}\nName: {name}\Train: {train['name']} ({train['train_no']})\n"
                    f"From: {from_station} to {to_station}\nclass: {cls}\nFare: Rs.{fare}\n"
                    f"Journey Date: {journey_date.strftime("%d-%m-%y")}\nStatus: CONFIRMED"
                )
                qr_img = generate_qr_code(qr_data)
                col1 , col2 = st.columns([3,1])
                with col1:
                    display_ticket(ticket)
                with col2:
                    st.write("QR code=")
                    st.image(qr_img, caption = "Scan to view tricket" , use_container_width=True )
def view_booking_page():
    st.title("My Bookings")
    user_booking = st.session_state.users[st.session_state.current_users].get("bookings",[])
    if not user_booking:
        st.info("No booking found. Book your first ticket!")
        return
    st.success(f"Total Bookings: {len(user_booking)}")
    st.write("")
    for idx, pnr in enumerate(user_booking,1):
        ticket = st.session_state.bookings.get(pnr)
        if ticket:
            with st.expander(
                f"Booking #{idx} - PNR: {pnr} | {ticket['Train']} | "
                f"{ticket['From']} to {ticket['To']} | Status: {ticket['Status']}",
                expanded=(idx==1)
            ):
                col1 , col2 = st.columns([3,1])
                with col1:
                    st.write(f"Train: {ticket['Train']} ({ticket['Train No']})")
                    st.write(f"Routa: {ticket['From']} to {ticket['To']}")
                    st.write(f"Class: {ticket['Class']} | Fare: Rs.{ticket['Fare']}")
                    st.write(f"Booking Date: {ticket['Booking Time']} | Journey Date: {ticket['Journey Date']}")
                    st.write(f"Status: {ticket['Status']}")
                    st.markdown("---")
                    if st.checkbox("Show Full Ticket Datails",key = f"full_{pnr}"):
                        display_ticket(ticket)
                with col2:
                    st.write('QR code')
                    qr_data = (
                        f"PNR: {pnr}\nName: {ticket['Name']}\nTrain: {ticket['Train']} ({ticket['Train No ']})\n"
                        f"From: {ticket['From']} to {ticket["To"]}\nClass: {ticket['Class']}\n"
                        f"Fares: Rs.{ticket['Fare']}\nJourney Date: {ticket['Journey Date']}\nStatus: {ticket['Status']}"
                    )
                    qr_img = generate_qr_code(qr_data)
                    st.image(qr_img, use_container_width=True)
                    st.write("")
                    if ticket["Status"] == "CONFIRMED":
                        if st.button(f"Cancel", key=f"cancel_{pnr}",use_container_width=True):
                            ticket["Status"] = "CANCELLED"
                            refund = ticket["Fare"] * 0.8
                            st.session_state.bookings[pnr] = ticket
                            save_json(BOOKINGS_FILE,st.session_state.bookings)
                            st.success(f"Ticket cancelled. Refund: Rs.{refund}")
                            st.rerun()
def edit_booking():
    st.subheader("Edit your Booking")
    pnr_input = st.text_input("Enter your pnr number to edit your booking")
    if pnr_input:
        if pnr_input in st.session_state.bookings:
            ticket = st.session_state.bookings[pnr_input]
            st.success("booking found! you can now edit your details below.")
            with st.form("edit_booking_from"):
                name = st.text_input("Passenger Name",value=ticket["Name"])
                age = st.number_input("Age",min_value=1,max_value=120,value=int(ticket["Age"]))
                nationality = st.text_input("Nationality",value=ticket["Nationality"])
                address = st.text_area("Address",value=ticket["Address"])
                current_class = ticket["Class"]
                train_class = st.selectbox(
                    "Class",
                    options=["SL","3A","2A"],
                    index = ["SL","3A","2A"].index(current_class)
                )
                journey_data = st.date_input(
                    "journey Data",
                    value = datetime.datetime.strptime(ticket["Journey Date"], "%d-%m-%Y").date()
                )
                submit_changes = st.form_submit_button("UPdate Booking")
                if submit_changes:
                    if not valid_journey_date(journey_data):
                        st.error("Journey data must be within 60 days from today.")
                        return
                    train_no = ticket["Train No"]
                    train = next((t for t in st.session_state.trains if t["train_no"] == train_no),None)
                    if train_class != ticket["Class"] and train["seats"][train_class] <=0:
                        st.error(f" No seats available in {train_class} class.")
                        return
                    if train_class != ticket["Class"]:
                        train["seats"][ticket["class"]] += 1
                        train["seats"][train_class] -= 1
                    ticket["Name"] = name
                    ticket["Age"] = age
                    ticket["Nationality"] = nationality
                    ticket["Address"] = address
                    ticket["Class"] = train_class
                    ticket["Journey Date"] = journey_data.strftime("%d-%m-%y")
                    ticket["Fare"] = fare_chart[train_class]
                    ticket["Booking Time"] = datetime.datetime.now().strftime("%d-%m-%y %H:%M")
                    st.session_state.bookings[pnr_input] = ticket
                    save_json(BOOKINGS_FILE, st.session_state.bookings)
                    st.success("Booking updated successfully!")
                    qr_date = f"pnr: {ticket["PNR"]}\nName: {ticket["Name"]}\nTrain: {ticket["Train"]} ({ticket["Train No"]})\nFrom: {ticket["From"]} -> {ticket["To"]}\nClass: {ticket["Class"]}\nJourney Date: {ticket["Journey Date"]}\nStatus :{ticket["Status"]}"
                    qr_img = generate_qr_code(qr_date)
                    st.image(qr_img,caption="update E-ticket QR code",use_column_width=False)
                    display_ticket(ticket)
        else:
            st.warning(" PNR not found. please check your number.")
def track_pnr_page():
    st.title("Track your PNR")
    col1 ,col2 = st.columns([3,1])
    with col1:
        pnr = st.text_input("Enter PNR Number",placeholder="Enter 13 digit PNR")
    with col2:
        st.write("")
        st.write("")
        track_btn = st.button("Track", use_container_width=True)
    if track_btn and pnr:
        if pnr in st.session_state.bookings:
            ticket = st.session_state.bookings[pnr]
            col1 , col2 = st.columns([3,1])
            with col1:
                display_ticket(ticket)
            with col2:
                st.write("QR Code")
                qr_data = (
                    f"pnr: {pnr}\nName: {ticket["Name"]}\nTrain: {ticket["Train"]} ({ticket["Train No"]})\n"
                    f"From:{ticket["From"]} to {ticket["To"]}\nClass: {ticket["Class"]}\n "
                    f"Fare: Rs.{ticket["Fare"]}\nJourney Date: {ticket["Journey Date"]}\nStatus: {ticket["Status"]}"                               
                )
                qr_img = generate_qr_code(qr_data)
                st.image(qr_img,use_container_width=True)
        else:
            st.error("PNR not found! please check the PNR number.")
def clear_booking_page():
    st.title("Clear All Boolking")
    user_bookings = st.session_state.users[st.session_state.current_users].get("bookings",[])
    if not user_bookings:
        st.info("No bookings to clear.")
        return
    st.warning(f"You have {len(user_bookings)} booking(s).")
    st.write("This action will permanently delete all your booking.")
    col1, col2, col3 = st.columns([1,1,2])
    with col1:
        if st.button("Clear All",use_container_width=True):
            st.session_state.confirm_clear = True
    if st.session_state.get("confirm_clear",False):
        st.error("Are you sure! This cannot be undone!")
        col1 , col2 = st.columns(2)
        with col1:
            if st.button("Yes, Delete all",use_container_width=True):
                for pnr in st.session_state.users[st.session_state.current_users].get("bookings",[]):
                    st.session_state.bookings.pop(pnr,None)
                    st.session_state.user[st.session_state.current_users]["bookings"].clear()
                    save_json(BOOKINGS_FILE,st.session_state.bookings)
                    save_json(USER_FILE,st.session_state.users)
                    st.session_state.confirm_clear = False
                    st.success("All bookings cleared successfully!")
                    st.rerun()
        with col2:
            if st.button("Cancle",use_container_width=True):
                st.session_state.confirm_clear = False
                st.rerun()
def main():
    st.set_page_config(
        page_title="Indian Railways Booking",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    st.title("Indian Railway Booking system")
    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login","register"])
        with tab1:
            login_page()
        with tab2:
            register_page()
    else:
        with st.sidebar:
            st.success("Logged in as:")
            st.info(st.session_state.current_user)
            st.divider()
            menu = st.radio(
                "Navigation",
                ["Book Ticket","My Booking","Edit Booking","Track PNR","Clear Booking"],
                label_visibility="collapsed"
            )
            st.divider()
            if st.button("Logout",use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.current_user = None
                st.rerun()
        if menu == "Book Ticket":
            booking_page()
        elif menu == "My Booking":
            view_booking_page()
        elif menu == "Edit Booking":
            edit_booking()
        elif menu == "Track PNR":
            track_pnr_page()
        elif menu == "Clear Booking":
            clear_booking_page()
if __name__=="__main__":
    main()