# backend_api.py
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import random, string

# ===============================
# Database connection
# ===============================
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:YOUR_PASSWORD@localhost/flight_booking"  # replace YOUR_PASSWORD
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

# ===============================
# Models
# ===============================
class Flight(Base):
    __tablename__ = "flights"
    id = Column(Integer, primary_key=True)
    flight_no = Column(String(10), unique=True)
    origin = Column(String(50))
    destination = Column(String(50))
    departure = Column(DateTime)
    arrival = Column(DateTime)
    base_fare = Column(Float)
    total_seats = Column(Integer)
    seats_available = Column(Integer)
    airline_name = Column(String(50))
    status = Column(String(20), default="active")

class Seat(Base):
    __tablename__ = "seats"
    seat_id = Column(Integer, primary_key=True)
    flight_id = Column(Integer, ForeignKey("flights.id"))
    seat_label = Column(String(10))
    seat_class = Column(String(20), default="Economy")
    price = Column(Float)
    status = Column(String(20), default="available")  # available / reserved / booked

class Booking(Base):
    __tablename__ = "bookings"
    booking_id = Column(Integer, primary_key=True)
    pnr = Column(String(10), unique=True)
    flight_id = Column(Integer, ForeignKey("flights.id"))
    seat_id = Column(Integer, ForeignKey("seats.seat_id"))
    total_price = Column(Float)
    status = Column(String(20), default="pending")  # pending / confirmed / cancelled / failed
    created_at = Column(DateTime, default=datetime.utcnow)

class Passenger(Base):
    __tablename__ = "passengers"
    passenger_id = Column(Integer, primary_key=True)
    booking_id = Column(Integer, ForeignKey("bookings.booking_id"))
    name = Column(String(50))
    age = Column(Integer)
    contact = Column(String(20))

# Create tables if not exist
Base.metadata.create_all(bind=engine)

# ===============================
# FastAPI app
# ===============================
app = FastAPI(title="Flight Booking API")

# ===============================
# Dependency to get DB session
# ===============================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ===============================
# Utility: Generate PNR
# ===============================
def generate_pnr():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

# ===============================
# Endpoint: Book a seat with simulated payment
# ===============================
@app.post("/book")
def book(flight_id: int, seat_id: int, passenger_name: str, passenger_contact: str, db: Session = Depends(get_db)):
    # Concurrency-safe seat selection
    seat = db.query(Seat).filter(Seat.seat_id == seat_id, Seat.flight_id == flight_id).with_for_update().first()
    if not seat or seat.status != "available":
        raise HTTPException(status_code=400, detail="Seat not available")
    
    seat.status = "reserved"
    db.commit()

    # Simulate payment (random success/fail)
    payment_success = random.choice([True, True, True, False])  # 75% chance success
    if not payment_success:
        seat.status = "available"  # release seat on failure
        db.commit()
        raise HTTPException(status_code=400, detail="Payment failed. Please try again.")

    # Generate PNR
    pnr = generate_pnr()
    
    # Create booking
    booking = Booking(flight_id=flight_id, seat_id=seat_id, total_price=seat.price, status="confirmed", pnr=pnr)
    db.add(booking)
    db.commit()
    db.refresh(booking)
    
    # Add passenger info
    passenger = Passenger(booking_id=booking.booking_id, name=passenger_name, contact=passenger_contact)
    db.add(passenger)
    db.commit()
    
    return {
        "message": "Booking successful",
        "pnr": pnr,
        "flight_id": flight_id,
        "seat_label": seat.seat_label,
        "passenger_name": passenger_name
    }

# ===============================
# Endpoint: Cancel a booking
# ===============================
@app.post("/cancel/{pnr}")
def cancel_booking(pnr: str, db: Session = Depends(get_db)):
    booking = db.query(Booking).filter(Booking.pnr == pnr).first()
    if not booking or booking.status != "confirmed":
        raise HTTPException(status_code=400, detail="Booking not found or already cancelled")
    
    booking.status = "cancelled"
    
    # Free the seat
    seat = db.query(Seat).filter(Seat.seat_id == booking.seat_id).first()
    seat.status = "available"
    
    db.commit()
    return {"message": f"Booking {pnr} cancelled successfully"}

# ===============================
# Endpoint: Retrieve booking history
# ===============================
@app.get("/history/{contact}")
def booking_history(contact: str, db: Session = Depends(get_db)):
    bookings = db.query(Booking, Passenger).join(Passenger, Passenger.booking_id == Booking.booking_id)\
        .filter(Passenger.contact == contact).all()
    
    result = []
    for b, p in bookings:
        result.append({
            "pnr": b.pnr,
            "flight_id": b.flight_id,
            "seat_id": b.seat_id,
            "passenger_name": p.name,
            "status": b.status,
            "booking_time": b.created_at
        })
    return result
