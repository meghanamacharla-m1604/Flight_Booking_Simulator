🛫 Flight Reservation System (FastAPI + Streamlit + SQLite)

A complete **Python-based flight booking simulator** featuring a FastAPI backend, a Streamlit frontend, and an SQLite database.  
This project replicates the flow of a real-world flight booking platform — from searching and dynamic pricing to booking confirmation and ticket generation.

---
 🌟 Project Overview

This simulator was built as part of a multi-stage internship project.  
Each milestone focuses on different aspects of full-stack development — database design, REST API creation, pricing logic, transactional safety, and frontend integration.

 🔹 Milestone Breakdown

- **Milestone 1 – Database Setup:**  
  Designed a normalized SQL schema and inserted initial datasets for flights, users, and bookings.

- **Milestone 2 – Dynamic REST API & Pricing:**  
  Created a FastAPI-based backend with endpoints for flight search, filtering, and demand-driven pricing logic.

- **Milestone 3 – Booking Workflow:**  
  Implemented concurrency-safe transactions to ensure atomic seat booking, PNR generation, and e-ticket creation.

- **Milestone 4 – Frontend Integration:**  
  Developed a fully functional Streamlit interface to connect with backend APIs for a complete booking experience.

---

 ⚙️ Technology Stack

| Component | Technology | Purpose |
| :-- | :-- | :-- |
| **Backend Framework** | FastAPI | Handles all API routes and dynamic logic. |
| **Frontend Framework** | Streamlit | Builds an interactive and modern web interface. |
| **Database** | SQLite | Stores flight, user, and booking details locally. |
| **Background Scheduler** | APScheduler | Simulates changing demand and pricing in the background. |
| **PDF Generator** | ReportLab | Creates structured e-ticket PDFs. |

---

 🧱 Implementation Summary

| Milestone | Description | Status | Implementation Details |
| :-- | :-- | :-- | :-- |
| **M1 – Database Schema** | Designed and populated flight, user, and booking tables. | ✅ Complete | Defined in `db.sql` with essential constraints and sample entries. |
| **M2 – REST API + Dynamic Pricing** | Built endpoints for flight search, validation, and price updates. | ✅ Complete | Implemented in `main.py` using `calculate_dynamic_price()` function. |
| **M2 – Background Jobs** | Simulated market demand to affect prices dynamically. | ✅ Complete | Scheduled using APScheduler’s `update_demand_factor()` job. |
| **M3 – Transactional Booking Engine** | Added PNR generation, seat locking, and booking cancellation. | ✅ Complete | SQLite transactions ensure concurrency-safe seat allocation. |
| **M4 – UI & Integration** | Integrated backend with a responsive Streamlit frontend. | ✅ Complete | Built in `frontend.py`, connecting all `/flights` and `/bookings` routes. |

---
🚀 Getting Started

### 🔧 Prerequisites
Make sure you have the following installed:
- Python **3.8 or higher**
- Git *(optional but recommended)*

---
 Step 1: Clone the Repository
git clone https://github.com/YourUsername/flight-booking-simulator.git
cd flight-booking-simulator

Step 2: Set Up Virtual Environment
python -m venv venv

# Activate the environment
# For macOS/Linux
source venv/bin/activate
# For Windows (PowerShell)
.\venv\Scripts\activate

Step 3: Install Dependencies
pip install -r requirements.txt

Step 4: Initialize the Database
Create and populate the SQLite database with sample flight data:
python initialize_db.py

Step 5: Run the FastAPI Backend
This will launch the API server that manages flights, bookings, and pricing.
uvicorn main:app --reload
By default, it runs on http://127.0.0.1:8000

Step 6: Start the Streamlit Frontend
Open a new terminal window and start the Streamlit client:
streamlit run frontend.py
The application will open in your browser — usually at http://localhost:8501
