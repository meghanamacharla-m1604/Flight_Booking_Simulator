# backend_api.py
# FastAPI app implementing the required endpoints and a dynamic pricing engine.
# Save this file in the same folder as flight_booking.db (created by your setup_database.py).

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List, Generator
from datetime import datetime, timedelta
import asyncio
import random

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# ---------- Configuration ----------
DATABASE_URL = "sqlite:///./flight_booking.db"

# SQLAlchemy setup
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
# standard sessionmaker signature
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ---------- DB MODELS ----------
class Flight(Base):
    __tablename__ = "flights"
    id = Column(Integer, primary_key=True, index=True)
    flight_no = Column(String, unique=True, index=True)
    origin = Column(String, index=True)
    destination = Column(String, index=True)
    departure = Column(DateTime)
    arrival = Column(DateTime)
    base_fare = Column(Float)
    total_seats = Column(Integer)
    seats_available = Column(Integer)
    airline_name = Column(String)

class FareHistory(Base):
    __tablename__ = "fare_history"
    id = Column(Integer, primary_key=True, index=True)
    flight_no = Column(String, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    price = Column(Float)

class DemandIndex(Base):
    __tablename__ = "demand_index"
    id = Column(Integer, primary_key=True, index=True)
    flight_no = Column(String, unique=True, index=True)
    demand = Column(Float)  # 0..1 scale

# create tables if not exist
Base.metadata.create_all(bind=engine)

# ---------- Pydantic Schemas ----------
class FlightOut(BaseModel):
    id: int
    flight_no: str
    origin: str
    destination: str
    departure: datetime
    arrival: datetime
    base_fare: float
    seats_available: int
    total_seats: int
    airline_name: str
    dynamic_price: float

    class Config:
        orm_mode = True

class SearchParams(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    sort_by: Optional[str] = Field(None, regex="^(price|duration)$")  # price or duration
    ascending: Optional[bool] = True
    limit: Optional[int] = 50

# ---------- App ----------
app = FastAPI(title="Flight Booking Simulator API (Dynamic Pricing)")

# ---------- Helpers ----------
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def minutes_between(dt1: datetime, dt2: datetime) -> int:
    return int((dt2 - dt1).total_seconds() / 60)

def get_time_to_departure_minutes(departure_dt: datetime) -> int:
    now = datetime.utcnow()
    # If departure_dt is naive (no tz), comparing to utcnow is fine (both naive).
    return max(0, minutes_between(now, departure_dt))

def clamp(x: float, a: float, b: float) -> float:
    return max(a, min(b, x))

def calculate_dynamic_price(base_fare: float,
                            seats_available: int,
                            total_seats: int,
                            departure_dt: datetime,
                            demand_factor: float,
                            airline_tier: int = 1) -> float:
    """
    Pricing model components:
    - seat_factor: increases as seats_available / total_seats decreases
    - time_factor: increases as time-to-departure shortens
    - demand_factor: simulated (0..1), higher => higher prices
    - airline_tier: optional multiplier for premium airlines (1 = base)
    final price = base_fare * (1 + seat_factor + time_factor + demand_factor * 0.4) * tier_multiplier
    """
    if total_seats is None or total_seats <= 0:
        return round(base_fare, 2)

    seat_fill_ratio = 1 - (seats_available / total_seats) if seats_available is not None else 0.0
    seat_factor = seat_fill_ratio * 0.6  # up to +60% depending on fill

    minutes_to_dep = get_time_to_departure_minutes(departure_dt)
    if minutes_to_dep <= 0:
        time_factor = 1.0
    else:
        days = minutes_to_dep / (60 * 24)
        if days <= 1:
            time_factor = 0.5
        elif days <= 7:
            time_factor = 0.2
        elif days <= 30:
            time_factor = 0.0
        else:
            time_factor = -0.08  # early-bird discount

    demand_component = (demand_factor if demand_factor is not None else 0.2) * 0.4
    tier_multiplier = 1.0 + (airline_tier - 1) * 0.05

    total_multiplier = 1 + seat_factor + time_factor + demand_component
    total_multiplier = clamp(total_multiplier, 0.5, 3.5)

    price = base_fare * total_multiplier * tier_multiplier
    return round(price, 2)

# ---------- Populate demand rows for flights that exist ----------
def ensure_demand_index_for_all(db):
    flights = db.query(Flight).all()
    for f in flights:
        exists = db.query(DemandIndex).filter(DemandIndex.flight_no == f.flight_no).first()
        if not exists:
            di = DemandIndex(flight_no=f.flight_no, demand=random.uniform(0.1, 0.5))
            db.add(di)
    db.commit()

# ---------- API Endpoints ----------

@app.on_event("startup")
async def startup_tasks():
    # ensure demand rows exist and start the background simulator
    db = SessionLocal()
    try:
        ensure_demand_index_for_all(db)
    finally:
        db.close()
    # start background simulator (runs in same process; for production prefer separate worker)
    asyncio.create_task(market_simulator_loop(interval_seconds=60))

@app.get("/flights", response_model=List[FlightOut])
def list_all_flights(limit: int = Query(50, ge=1, le=200)):
    """
    Retrieve all flights; dynamic prices are computed at request-time.
    """
    db = SessionLocal()
    try:
        flights = db.query(Flight).limit(limit).all()
        results = []
        for f in flights:
            di = db.query(DemandIndex).filter(DemandIndex.flight_no == f.flight_no).first()
            demand = di.demand if di else random.uniform(0.1, 0.4)
            price = calculate_dynamic_price(
                base_fare=f.base_fare,
                seats_available=f.seats_available,
                total_seats=f.total_seats,
                departure_dt=f.departure,
                demand_factor=demand,
                airline_tier=1
            )
            results.append(FlightOut(
                id=f.id,
                flight_no=f.flight_no,
                origin=f.origin,
                destination=f.destination,
                departure=f.departure,
                arrival=f.arrival,
                base_fare=f.base_fare,
                seats_available=f.seats_available,
                total_seats=f.total_seats,
                airline_name=f.airline_name,
                dynamic_price=price
            ))
        return results
    finally:
        db.close()

@app.get("/search", response_model=List[FlightOut])
def search_flights(
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    date: Optional[str] = None,  # accepts YYYY-MM-DD
    sort_by: Optional[str] = Query(None, regex="^(price|duration)$"),
    ascending: bool = True,
    limit: int = Query(50, ge=1, le=200)
):
    """
    Search flights by origin/destination/date. Sorting by 'price' or 'duration' is allowed.
    Date filters by departure date (UTC day).
    """
    db = SessionLocal()
    try:
        q = db.query(Flight)
        if origin:
            q = q.filter(Flight.origin.ilike(f"%{origin}%"))
        if destination:
            q = q.filter(Flight.destination.ilike(f"%{destination}%"))
        if date:
            try:
                day = datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
            day_start = datetime(day.year, day.month, day.day)
            day_end = day_start + timedelta(days=1)
            q = q.filter(Flight.departure >= day_start, Flight.departure < day_end)

        flights = q.all()

        enriched = []
        for f in flights:
            di = db.query(DemandIndex).filter(DemandIndex.flight_no == f.flight_no).first()
            demand = di.demand if di else random.uniform(0.1, 0.4)
            dynamic_price = calculate_dynamic_price(
                base_fare=f.base_fare,
                seats_available=f.seats_available,
                total_seats=f.total_seats,
                departure_dt=f.departure,
                demand_factor=demand
            )
            # compute duration safely
            try:
                duration_minutes = minutes_between(f.departure, f.arrival)
            except Exception:
                duration_minutes = 0
            enriched.append({
                "flight": f,
                "dynamic_price": dynamic_price,
                "duration_minutes": duration_minutes
            })

        # sorting
        if sort_by == "price":
            enriched.sort(key=lambda x: x["dynamic_price"], reverse=not ascending)
        elif sort_by == "duration":
            enriched.sort(key=lambda x: x["duration_minutes"], reverse=not ascending)

        results = []
        for item in enriched[:limit]:
            f = item["flight"]
            results.append(FlightOut(
                id=f.id,
                flight_no=f.flight_no,
                origin=f.origin,
                destination=f.destination,
                departure=f.departure,
                arrival=f.arrival,
                base_fare=f.base_fare,
                seats_available=f.seats_available,
                total_seats=f.total_seats,
                airline_name=f.airline_name,
                dynamic_price=item["dynamic_price"]
            ))
        return results
    finally:
        db.close()

@app.get("/dynamic_price/{flight_no}")
def get_dynamic_price(flight_no: str):
    """
    Return current dynamic price for a single flight and record a fare history row.
    """
    db = SessionLocal()
    try:
        flight = db.query(Flight).filter(Flight.flight_no == flight_no).first()
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")
        di = db.query(DemandIndex).filter(DemandIndex.flight_no == flight_no).first()
        demand = di.demand if di else 0.2
        price = calculate_dynamic_price(
            base_fare=flight.base_fare,
            seats_available=flight.seats_available,
            total_seats=flight.total_seats,
            departure_dt=flight.departure,
            demand_factor=demand
        )
        # record fare history (best-effort)
        try:
            fh = FareHistory(flight_no=flight_no, price=price, timestamp=datetime.utcnow())
            db.add(fh)
            db.commit()
        except Exception:
            db.rollback()
        return {"flight_no": flight_no, "dynamic_price": price, "base_fare": flight.base_fare, "demand": demand}
    finally:
        db.close()

# Simulated external airline schedule API — returns some random schedule items (useful for integration tests)
@app.get("/external/airline_schedule")
def external_airline_schedule(origin: str, destination: str, date: Optional[str] = None):
    date_obj = None
    if date:
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except Exception:
            raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD")
    base_departure = (date_obj.replace(hour=6, minute=0) if date_obj else datetime.utcnow())
    schedules = []
    choices = [
        ("6E", "IndiGo"),
        ("AI", "Air India"),
        ("SG", "SpiceJet")
    ]
    for _ in range(random.randint(1, 3)):
        code, airline = random.choice(choices)
        dep = base_departure + timedelta(hours=random.randint(1, 12))
        arr = dep + timedelta(minutes=random.randint(60, 200))
        schedules.append({
            "external_flight_no": f"{code}{random.randint(100,999)}",
            "airline": airline,
            "origin": origin,
            "destination": destination,
            "departure": dep.isoformat(),
            "arrival": arr.isoformat(),
            "estimated_fare": round(random.uniform(3000, 10000), 2)
        })
    return {"schedules": schedules}

# ---------- Background simulator ----------
async def simulate_market_step():
    """
    One simulation tick:
    - randomly pick some flights
    - nudge seats_available (simulate bookings/cancellations)
    - adjust demand index randomly a bit
    - optionally record fare history entries
    """
    db = SessionLocal()
    try:
        flights = db.query(Flight).all()
        if not flights:
            return
        to_change = random.sample(flights, k=min(len(flights), random.randint(1, 3)))
        for f in to_change:
            # small random booking (1..5 seats) or cancellation (-3..-1)
            delta = random.choice([-3, -2, -1, 0, 1, 1, 2])  # bias slightly to bookings
            new_avail = clamp((f.seats_available - delta) if f.seats_available is not None else f.total_seats, 0, f.total_seats if f.total_seats else 9999)
            f.seats_available = new_avail

            di = db.query(DemandIndex).filter(DemandIndex.flight_no == f.flight_no).first()
            if di:
                di.demand = clamp(di.demand + random.uniform(-0.05, 0.07), 0.0, 1.0)
            else:
                di = DemandIndex(flight_no=f.flight_no, demand=random.uniform(0.1, 0.6))
                db.add(di)

            price = calculate_dynamic_price(
                base_fare=f.base_fare if f.base_fare else 0.0,
                seats_available=f.seats_available,
                total_seats=f.total_seats if f.total_seats else 1,
                departure_dt=f.departure if f.departure else datetime.utcnow(),
                demand_factor=di.demand if di else 0.2
            )
            fh = FareHistory(flight_no=f.flight_no, price=price, timestamp=datetime.utcnow())
            db.add(fh)

        db.commit()
    except Exception as e:
        db.rollback()
        print("Simulator error:", e)
    finally:
        db.close()

async def market_simulator_loop(interval_seconds: int = 60):
    """
    Continuously run the simulator at given interval.
    Use a small interval during dev (e.g. 60s). In production use a worker/cron or longer interval.
    """
    while True:
        await simulate_market_step()
        await asyncio.sleep(interval_seconds)

# ---------- Fare history endpoint ----------
@app.get("/fare_history/{flight_no}")
def fare_history(flight_no: str, limit: int = Query(50, ge=1, le=500)):
    db = SessionLocal()
    try:
        rows = db.query(FareHistory).filter(FareHistory.flight_no == flight_no).order_by(FareHistory.timestamp.desc()).limit(limit).all()
        result = [{"timestamp": r.timestamp.isoformat(), "price": r.price} for r in rows]
        return {"flight_no": flight_no, "history": result}
    finally:
        db.close()
