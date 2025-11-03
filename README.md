Flight Booking Simulator With Dynamic Pricing:

-Flight Booking Simulator with Dynamic Pricing is a learning-based airline booking system that simulates real-world fare variation. Users can search flights, check seat availability, and book tickets, while the system applies automated price adjustments based on demand, booking time, and seat availability. The project demonstrates backend API development using FastAPI, SQL-based storage, and simple frontend integration. Built as part of an internship learning module focused on real-time pricing systems and airline booking workflows.
Features:

Search flights by origin, destination, and travel date

Dynamic price updates based on demand and travel date proximity

Real-time seat availability tracking

Ticket booking with unique booking ID

Frontend and backend connection using REST APIs

Database operations for flights and bookings

Error handling and input validation

Dynamic Pricing Behavior:

Low seats remaining: price increases

Travel date close: price increases

Off-peak booking periods: price may decrease

Normal demand: base fare applies

-Tech Stack:

Frontend: HTML, CSS, JavaScript
Backend: Python (FastAPI)
Database: SQLite or PostgreSQL
ORM: SQLAlchemy
Development Tools: Visual Studio Code, Postman

-Project Structure:

flight-booking-simulator
backend
setup_database.py
backend_api.py
requirements.txt
frontend
index.html
search.js
styles.css
screenshots
README.md

-How To Run:

Install Python 3.9 or higher.

Clone the project repository.

Navigate to the backend folder.

Install dependencies using "pip install -r requirements.txt".

Run "python setup_database.py" to initialize the database.

Start the API server using "uvicorn backend_api:app --reload".

Access the API at http://127.0.0.1:8000


Open the frontend files to interact with the system.

-API Endpoints:

GET /flights/search – search for available flights
POST /book – book seats on a flight
GET /flights/{id} – get details of a specific flight
GET /health – API server check

-Sample booking request body:

{
"flight_id": 1,
"passenger_name": "Test User",
"no_of_seats": 2
}

-System Architecture:

User interacts with the frontend
Frontend communicates with the FastAPI backend
Backend processes requests and retrieves/stores data in the database

-Database Entities:

Flights table: flight details including available seats and base price
Bookings table: passenger bookings linked to flights and payment details
One flight can have multiple bookings

-Future Improvements:

Login and authentication feature
Seat selection system
Ticket cancellation and refund workflow
Email ticket confirmation
Admin dashboard to manage flights
Machine learning based price prediction


-License:
Project released under MIT License.
