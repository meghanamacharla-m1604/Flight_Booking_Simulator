# 🛫 Flight Booking Simulator – Backend (FastAPI + SQLite)

This project implements the **backend API** for a flight booking simulator, built using **FastAPI** and **SQLite**.  
It handles all backend logic — from user authentication, flight search, and booking transactions to PDF ticket generation, refund receipts, and dynamic pricing.

---

## 🌟 Project Overview

This backend is designed to simulate the core functionality of a modern airline reservation system.  
It provides RESTful endpoints for user registration, flight browsing, bookings, payments, and cancellations — all powered by a secure, transactional database layer.

### 🔹 Major Features
- ✅ **FastAPI-based REST API**
- 💰 **Dynamic flight pricing** based on seat availability and demand
- 🧾 **Automatic PDF ticket & cancellation receipt generation**
- 🔁 **Background scheduler** that updates demand factors every few minutes
- 🤖 **Gemini AI chatbot** integration (optional, if API key configured)
- 🧠 **Secure user authentication** (password hashing)
- 💾 **SQLite database** with schema for flights, users, bookings, and cancellations

---

## ⚙️ Technology Stack

| Component | Technology | Purpose |
| :-- | :-- | :-- |
| **Backend Framework** | FastAPI | Handles routing, API logic, and data models. |
| **Database** | SQLite | Lightweight SQL database for flight and booking data. |
| **Background Tasks** | APScheduler | Simulates periodic demand changes. |
| **PDF Generator** | ReportLab | Generates e-ticket and refund PDF documents. |
| **AI Assistant** | Google Gemini API | Provides chatbot interaction (optional). |

---

## 🧩 Key Functional Modules

| Module | Description |
| :-- | :-- |
| **User Management** | Register, login, and secure password hashing. |
| **Flights API** | Search, filter, and view dynamically priced flights. |
| **Bookings API** | Create, confirm, cancel, and view bookings. |
| **Tickets & Receipts** | Generate and download PDFs for tickets and cancellations. |
| **Demand Simulation** | Periodically adjusts demand factors automatically. |
| **Chatbot (Optional)** | Gemini-based AI travel assistant. |

---

## 🚀 How to Run the Project Locally

### 🧱 Prerequisites
Make sure you have:
- Python **3.3**
- `pip` package manager

---

Step 1️⃣ — Clone the Repository
git clone https://github.com/YourUsername/flight-booking-backend.git
cd flight-booking-backend

Step 2️⃣ — Create a Virtual Environment
python -m venv venv
# Activate it
# macOS/Linux
source venv/bin/activate
# Windows PowerShell
.\venv\Scripts\activate

Step 3️⃣ — Install Dependencies
pip install -r requirements.txt

Step 4️⃣ — Initialize the Database
Run your database setup or schema initialization file (if you have one), e.g.:
python initialize_db.py
Ensure that db.sqlite exists in the project directory.

Step 5️⃣ — Run the FastAPI Server
uvicorn main:app --reload


By default, your backend runs at:
 http://127.0.0.1:8000
You can view the interactive API docs here:
📘 Swagger UI → http://127.0.0.1:8000/docs
