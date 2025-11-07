"""
Flight Booking Simulator Backend (FastAPI + SQLite)
-----------------------------------------------------
A complete backend implementation using:
- FastAPI (API Framework)
- SQLite (Database)
- APScheduler (Demand Simulation)
- ReportLab (PDF Ticket/Receipt)
- Gemini API (Chatbot)
"""

import sqlite3
import uuid
import hashlib
import secrets
import random
import atexit
import os
from datetime import datetime, timedelta
from typing import List, Optional

# --- AI Chatbot Integration ---
import google.generativeai as genai
from pydantic import BaseModel as PydanticBaseModel  # Avoid conflict with FastAPI BaseModel

# --- PDF Generation ---
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- FastAPI & Scheduler ---
from fastapi import FastAPI, HTTPException, status, Query, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler

# --- Configuration ---
DATABASE_NAME = "db.sqlite"
app = FastAPI(title="Flight Booking Simulator API", version="1.0")

# --- Gemini API Setup ---
try:
    GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel("gemini-2.5-flash")
    print("Gemini API configured successfully.")
except KeyError:
    print(" GEMINI_API_KEY not found. Chatbot disabled.")
    gemini_model = None


# ======================================================
#  Database Utility
# ======================================================
def get_db_connection():
    conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    db = get_db_connection()
    try:
        yield db
    finally:
        db.close()


# ======================================================
#  Pydantic Models
# ======================================================

class UserAuth(BaseModel):
    username: str
    password: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None


class Passenger(BaseModel):
    first_name: str
    last_name: str
    age: int
    phone: int


class BookingRequest(BaseModel):
    flight_number: str
    passenger: Passenger
    travel_date: str
    seat_preference: Optional[str] = "Any"
    user_id: int


class FlightDisplay(BaseModel):
    id: int
    flight_number: str
    airline: str
    from_city_country: str
    to_city_country: str
    base_price: float
    total_seats: int
    seats_remaining: int
    final_price: float
    demand_factor: float


class ChatMessage(PydanticBaseModel):
    role: str
    parts: str


class ChatRequest(PydanticBaseModel):
    history: List[ChatMessage]
    prompt: str


# ======================================================
# Utility Functions
# ======================================================
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def calculate_dynamic_price(base_price: float, seats_remaining: int, total_seats: int, demand_factor: float) -> float:
    remaining_pct = seats_remaining / total_seats
    if remaining_pct > 0.75:
        seat_factor = -0.05
    elif remaining_pct > 0.5:
        seat_factor = 0.0
    elif remaining_pct > 0.25:
        seat_factor = 0.15
    else:
        seat_factor = 0.3
    final_price = base_price * (1 + seat_factor + 0.05) * demand_factor
    return round(final_price, 2)


# ======================================================
#  PDF Generation
# ======================================================
def generate_ticket_pdf(pnr: str, booking: dict) -> str:
    file_path = f"ticket_{pnr}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=0.5*inch, rightMargin=0.5*inch)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterBold", fontSize=14, alignment=1, fontName="Helvetica-Bold"))

    story = [
        Paragraph("✈️ E-TICKET / BOARDING PASS", styles["Title"]),
        Paragraph(f"PNR: {pnr}", styles["h2"]),
        Spacer(1, 0.2 * inch),
    ]

    seat = f"{random.randint(1, 30)}{random.choice(['A','B','C','D','E','F'])}"
    gate = f"G{random.randint(10, 50)}"
    board_time = (datetime.now() + timedelta(hours=2)).strftime("%I:%M %p")

    data = [
        ["Passenger", booking["passenger_name"]],
        ["Flight", f"{booking['flight_number']} ({booking['airline']})"],
        ["Route", f"{booking['from_city_country']} ➜ {booking['to_city_country']}"],
        ["Date", booking["booking_date"].split(" ")[0]],
        ["Gate", gate],
        ["Seat", seat],
        ["Boarding Time", board_time],
    ]
    table = Table(data, colWidths=[2.5*inch, 3*inch])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.whitesmoke),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))
    story += [table, Spacer(1, 0.3*inch)]
    story.append(Paragraph(f"BARCODE: {pnr}", styles["CenterBold"]))
    story.append(Paragraph("Please carry this e-ticket and valid ID at the gate.", styles["Italic"]))

    doc.build(story)
    return file_path


def generate_cancellation_receipt(pnr: str, details: dict) -> str:
    file_path = f"receipt_{pnr}.pdf"
    doc = SimpleDocTemplate(file_path, pagesize=letter, leftMargin=inch, rightMargin=inch)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("CANCELLATION & REFUND RECEIPT", styles["Title"]),
        Spacer(1, 0.3 * inch),
        Paragraph(f"PNR: {pnr}", styles["h3"]),
        Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["h4"]),
        Spacer(1, 0.2 * inch),
    ]

    table_data = [
        ["Description", "Amount ($)"],
        [f"Original Fare ({details['flight_number']})", f"{details['price_paid']:.2f}"],
        ["Cancellation Fee (20%)", f"{details['price_paid']*0.2:.2f}"],
        [f"Refund (80%)", f"{details['refund_amount']:.2f}"],
    ]
    table = Table(table_data, colWidths=[3.5*inch, 2*inch])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ]))
    story += [table, Spacer(1, 0.3*inch)]
    story.append(Paragraph("Refund will be processed within 5–7 business days.", styles["Italic"]))
    doc.build(story)
    return file_path


# ======================================================
#  Demand Simulation
# ======================================================
def update_demand_factor():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM flight")
    for row in cur.fetchall():
        new_factor = round(random.uniform(0.9, 1.1), 2)
        cur.execute("UPDATE flight SET demand_factor = ? WHERE id = ?", (new_factor, row["id"]))
    conn.commit()
    conn.close()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Demand factors updated.")


scheduler = BackgroundScheduler()
scheduler.add_job(update_demand_factor, "interval", minutes=5)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


# ======================================================
#  API ROUTES
# ======================================================

@app.get("/")
def root():
    return {"message": "Welcome to the Flight Booking Simulator API"}


# --- Authentication ---
@app.post("/register")
def register_user(user: UserAuth, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id FROM user WHERE username=?", (user.username,))
    if cur.fetchone():
        raise HTTPException(400, "Username already exists.")
    cur.execute(
        "INSERT INTO user (username, password_hash, full_name, phone, country) VALUES (?, ?, ?, ?, ?)",
        (user.username, hash_password(user.password), user.full_name, user.phone, user.country),
    )
    db.commit()
    return {"message": "User registered successfully"}


@app.post("/login")
def login_user(user: UserAuth, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id, password_hash FROM user WHERE username=?", (user.username,))
    data = cur.fetchone()
    if not data or hash_password(user.password) != data["password_hash"]:
        raise HTTPException(401, "Invalid credentials.")
    return {"message": "Login successful", "user_id": data["id"], "token": secrets.token_urlsafe(16)}


# --- Flights ---
@app.get("/flights", response_model=List[FlightDisplay])
def get_flights(
    origin: Optional[str] = Query(None),
    destination: Optional[str] = Query(None),
    db: sqlite3.Connection = Depends(get_db),
):
    cur = db.cursor()
    query = "SELECT * FROM flight WHERE 1=1"
    params = []
    if origin:
        query += " AND from_city_country=?"
        params.append(origin.strip())
    if destination:
        query += " AND to_city_country=?"
        params.append(destination.strip())
    flights = cur.execute(query, params).fetchall()
    if not flights:
        raise HTTPException(404, "No flights found.")
    results = []
    for row in flights:
        f = dict(row)
        f["final_price"] = calculate_dynamic_price(f["base_price"], f["seats_remaining"], f["total_seats"], f["demand_factor"])
        results.append(f)
    return results


# --- Bookings ---
@app.post("/bookings", status_code=201)
def create_booking(request: BookingRequest, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    passenger_name = f"{request.passenger.first_name} {request.passenger.last_name}"

    cur.execute("SELECT id, base_price, seats_remaining, total_seats, demand_factor FROM flight WHERE flight_number=?",
                (request.flight_number,))
    flight = cur.fetchone()
    if not flight:
        raise HTTPException(404, "Flight not found.")
    if flight["seats_remaining"] <= 0:
        raise HTTPException(400, "No seats available.")

    price = calculate_dynamic_price(flight["base_price"], flight["seats_remaining"], flight["total_seats"], flight["demand_factor"])
    pnr = "PNR" + uuid.uuid4().hex[:7].upper()

    cur.execute("""
        INSERT INTO booking (user_id, flight_id, pnr, price_paid, booking_date, passenger_full_name)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
    """, (request.user_id, flight["id"], pnr, price, passenger_name))
    db.commit()

    return {"message": "Booking created successfully", "pnr": pnr, "price": price, "status": "PENDING_PAYMENT"}


@app.post("/bookings/pay/{pnr}")
def confirm_payment(pnr: str, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id, flight_id FROM booking WHERE pnr=?", (pnr,))
    booking = cur.fetchone()
    if not booking:
        raise HTTPException(404, "Booking not found.")
    cur.execute("SELECT seats_remaining FROM flight WHERE id=?", (booking["flight_id"],))
    flight = cur.fetchone()
    if flight["seats_remaining"] <= 0:
        raise HTTPException(400, "Seat unavailable.")
    cur.execute("UPDATE flight SET seats_remaining=seats_remaining-1 WHERE id=?", (booking["flight_id"],))
    cur.execute("UPDATE booking SET status='CONFIRMED' WHERE pnr=?", (pnr,))
    db.commit()
    return {"message": f"Booking {pnr} confirmed."}


@app.get("/bookings/history/{user_id}")
def booking_history(user_id: int, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT b.pnr, b.price_paid, b.booking_date, f.flight_number, f.airline,
               f.from_city_country, f.to_city_country, b.status, b.passenger_full_name
        FROM booking b JOIN flight f ON b.flight_id=f.id
        WHERE b.user_id=? ORDER BY b.booking_date DESC
    """, (user_id,))
    data = [dict(row) for row in cur.fetchall()]
    return {"user_id": user_id, "bookings": data}


@app.delete("/bookings/{pnr}")
def cancel_booking(pnr: str, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("SELECT id, flight_id, user_id, price_paid, passenger_full_name FROM booking WHERE pnr=? AND status='CONFIRMED'", (pnr,))
    b = cur.fetchone()
    if not b:
        raise HTTPException(404, "Confirmed booking not found.")
    refund = round(b["price_paid"] * 0.8, 2)
    cur.execute("""
        INSERT INTO cancelled_booking (pnr, user_id, flight_id, price_paid, refund_amount, passenger_full_name)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (pnr, b["user_id"], b["flight_id"], b["price_paid"], refund, b["passenger_full_name"]))
    cur.execute("DELETE FROM booking WHERE id=?", (b["id"],))
    cur.execute("UPDATE flight SET seats_remaining=seats_remaining+1 WHERE id=?", (b["flight_id"],))
    db.commit()
    return {"message": f"Booking {pnr} cancelled successfully.", "refund_amount": refund}


# --- PDF Endpoints ---
@app.get("/tickets/{pnr}")
def get_ticket(pnr: str, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT b.*, f.flight_number, f.airline, f.from_city_country, f.to_city_country
        FROM booking b JOIN flight f ON b.flight_id=f.id WHERE b.pnr=?
    """, (pnr,))
    b = cur.fetchone()
    if not b:
        raise HTTPException(404, "Booking not found.")
    pdf = generate_ticket_pdf(pnr, dict(b))
    return FileResponse(pdf, media_type="application/pdf", filename=f"ticket_{pnr}.pdf")


@app.get("/receipts/{pnr}")
def get_receipt(pnr: str, db: sqlite3.Connection = Depends(get_db)):
    cur = db.cursor()
    cur.execute("""
        SELECT c.*, f.flight_number, f.airline FROM cancelled_booking c
        JOIN flight f ON c.flight_id=f.id WHERE c.pnr=?
    """, (pnr,))
    c = cur.fetchone()
    if not c:
        raise HTTPException(404, "No cancellation found.")
    pdf = generate_cancellation_receipt(pnr, dict(c))
    return FileResponse(pdf, media_type="application/pdf", filename=f"receipt_{pnr}.pdf")
