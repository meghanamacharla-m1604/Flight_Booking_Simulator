import React, { useEffect, useState } from "react";

// Flight Booking Simulator - Single-file React component
// Save this file as src/BookingApp.jsx in a create-react-app project.
// This component uses fetch to talk to a backend assumed to be running at the value of API_BASE.
// Expected backend endpoints (adjust if your backend differs):
// GET  /search?origin=...&dest=...&date=YYYY-MM-DD -> { flights: [ { id, airline, flight_no, depart, arrive, duration, seats, dynamic_price, price, fareClass } ] }
// POST /book  (body: { flight_id, passengers: [...], payment: {...} }) -> { booking_id, pnr, booking }
// GET  /pnr/:pnr  -> { booking }
// Note: This file is intentionally dependency-free (no external UI libs) so it works in plain CRA.

export default function BookingApp() {
  const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000"; // note: no trailing /api so endpoints below use full paths

  const [search, setSearch] = useState({ origin: "", dest: "", date: "" });
  const [loadingSearch, setLoadingSearch] = useState(false);
  const [flights, setFlights] = useState([]);
  const [selectedFlight, setSelectedFlight] = useState(null);
  const [bookingStep, setBookingStep] = useState(0); // 0 = none, 1 = passenger, 2 = payment, 3 = confirm
  const [passengers, setPassengers] = useState([{ name: "", age: "", type: "ADT" }]);
  const [payment, setPayment] = useState({ method: "card", cardNo: "", nameOnCard: "" });
  const [currentBooking, setCurrentBooking] = useState(null);
  const [pnrLookup, setPnrLookup] = useState("");
  const [pnrResult, setPnrResult] = useState(null);
  const [error, setError] = useState("");

  // helper: build endpoint URL
  const buildUrl = (path, params) => {
    const url = new URL(API_BASE + path);
    if (params) Object.keys(params).forEach(k => url.searchParams.append(k, params[k]));
    return url.toString();
  };

  // Search flights
  async function doSearch(e) {
    if (e) e.preventDefault();
    setError("");
    setFlights([]);
    if (!search.origin || !search.dest || !search.date) {
      setError("Please provide origin, destination and date.");
      return;
    }
    setLoadingSearch(true);
    try {
      const url = buildUrl('/search', { origin: search.origin, dest: search.dest, date: search.date });
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Search failed: ${res.status} ${res.statusText}`);
      const data = await res.json();
      setFlights(Array.isArray(data.flights) ? data.flights : (Array.isArray(data) ? data : []));
    } catch (err) {
      console.error(err);
      setError(err.message || "Search error");
    } finally {
      setLoadingSearch(false);
    }
  }

  function startBooking(flight) {
    setSelectedFlight(flight);
    setBookingStep(1);
    setPassengers([{ name: "", age: "", type: "ADT" }]);
    setPayment({ method: "card", cardNo: "", nameOnCard: "" });
    setCurrentBooking(null);
    setError("");
  }

  function updatePassenger(idx, field, value) {
    setPassengers(prev => prev.map((p, i) => i === idx ? { ...p, [field]: value } : p));
  }
  function addPassenger() { setPassengers(prev => [...prev, { name: "", age: "", type: "ADT" }]); }
  function removePassenger(i) { setPassengers(prev => prev.filter((_, idx) => idx !== i)); }

  // Submit booking to backend
  async function submitBooking() {
    setError("");
    if (!selectedFlight) { setError("No flight selected"); return; }
    if (passengers.some(p => !p.name || !p.age)) { setError("Please fill passenger details"); return; }

    const payload = { flight_id: selectedFlight.id, passengers, payment };
    try {
      const res = await fetch(API_BASE + '/book', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const txt = await res.text();
        throw new Error(`Booking failed: ${res.status} ${res.statusText} - ${txt}`);
      }
      const data = await res.json();
      // backend may return { booking_id, pnr, booking } or booking object directly
      const booking = data.booking || data;
      setCurrentBooking(booking);
      setBookingStep(0);
      setSelectedFlight(null);
      setPassengers([{ name: "", age: "", type: "ADT" }]);
    } catch (err) {
      console.error(err);
      setError(err.message || 'Booking error');
    }
  }

  // PNR lookup
  async function lookupPnr(e) {
    if (e) e.preventDefault();
    setPnrResult(null);
    setError("");
    if (!pnrLookup) { setError('Enter a PNR'); return; }
    try {
      const res = await fetch(`${API_BASE}/pnr/${encodeURIComponent(pnrLookup)}`);
      if (!res.ok) throw new Error(`PNR lookup failed: ${res.status} ${res.statusText}`);
      const data = await res.json();
      setPnrResult(data.booking || data);
    } catch (err) {
      console.error(err);
      setError(err.message || 'PNR lookup error');
    }
  }

  // Download JSON
  function downloadJSON(obj, filename = 'receipt.json') {
    const blob = new Blob([JSON.stringify(obj, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
  }

  // Download PDF using jspdf UMD loaded from CDN (simple textual receipt)
  async function downloadPDF(obj, filename = 'receipt.pdf') {
    try {
      if (!window.jspdf) {
        await new Promise((resolve, reject) => {
          const s = document.createElement('script');
          s.src = 'https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js';
          s.onload = () => resolve();
          s.onerror = () => reject(new Error('Failed to load jsPDF from CDN'));
          document.head.appendChild(s);
        });
      }

      const { jsPDF } = window.jspdf;
      const doc = new jsPDF();
      doc.setFontSize(14);
      doc.text('Booking Receipt', 105, 15, { align: 'center' });
      doc.setFontSize(10);

      const lines = JSON.stringify(obj, null, 2).split('
');
      let y = 25;
      const lineHeight = 6;
      lines.forEach(line => {
        if (y > 280) { doc.addPage(); y = 15; }
        doc.text(line, 10, y);
        y += lineHeight;
      });
      doc.save(filename);
    } catch (err) {
      console.error(err);
      setError('PDF generation failed: ' + (err.message || err));
    }
  }

  function fmtPrice(v) { return (typeof v === 'number') ? `₹${v.toFixed(2)}` : v ?? '—'; }

  return (
    <div style={{ fontFamily: 'Inter, system-ui, sans-serif', padding: 20, maxWidth: 1100, margin: '0 auto' }}>
      <style>{`
        .card{box-shadow:0 6px 18px rgba(20,20,30,0.06);padding:14px;border-radius:10px;margin-bottom:12px;background:#fff}
        .btn{padding:8px 12px;border-radius:8px;border:0;cursor:pointer}
        .btn-primary{background:#0b5cff;color:white}
        .btn-ghost{background:#f1f5f9}
        .muted{color:#6b7280}
        input,select{padding:8px;border:1px solid #e5e7eb;border-radius:8px}
      `}</style>

      <h1 style={{ fontSize: 22, marginBottom: 6 }}>Flight Booking Simulator — Frontend</h1>
      <p className="muted">Backend base: <code>{API_BASE}</code></p>

      {error && <div style={{ background: '#fee', border: '1px solid #fbb', padding: 10, borderRadius: 8, marginTop: 12 }}>{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: 18, marginTop: 18 }}>
        <div>
          <form className="card" onSubmit={doSearch}>
            <h2 style={{ marginTop: 0 }}>Search Flights</h2>
            <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
              <input placeholder="Origin (IATA or city)" value={search.origin} onChange={e => setSearch({ ...search, origin: e.target.value })} />
              <input placeholder="Destination" value={search.dest} onChange={e => setSearch({ ...search, dest: e.target.value })} />
              <input type="date" value={search.date} onChange={e => setSearch({ ...search, date: e.target.value })} />
              <button className="btn btn-primary" type="submit">{loadingSearch ? 'Searching...' : 'Search'}</button>
            </div>
            <div className="muted">Tip: Backend should return a <code>dynamic_price</code> field to show surge prices.</div>
          </form>

          <div>
            {flights.length === 0 && <div className="card muted">No search results yet — run a search.</div>}
            {flights.map(f => (
              <div key={f.id} className="card" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontWeight: 600 }}>{f.airline} • {f.flight_no}</div>
                  <div className="muted">{f.depart} → {f.arrive} • {f.duration}</div>
                  <div style={{ marginTop: 6 }}>Seats: {f.seats ?? '—'}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 18, fontWeight: 700 }}>{fmtPrice(f.dynamic_price ?? f.price ?? 0)}</div>
                  <div className="muted">{f.fareClass ?? 'Economy'}</div>
                  <div style={{ marginTop: 8 }}>
                    <button className="btn btn-primary" onClick={() => startBooking(f)}>Book</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <aside>
          <div className="card">
            <h3 style={{ marginTop: 0 }}>Booking Flow</h3>
            <div className="muted">Selected flight:</div>
            {selectedFlight ? (
              <div>
                <div style={{ fontWeight: 700 }}>{selectedFlight.airline} {selectedFlight.flight_no}</div>
                <div className="muted">{selectedFlight.depart} → {selectedFlight.arrive}</div>
                <div style={{ marginTop: 8 }}>
                  <div className="muted">Steps</div>
                  <ol>
                    <li>Passenger details</li>
                    <li>Payment</li>
                    <li>Confirm & Book</li>
                  </ol>
                </div>
                <div style={{ marginTop: 8 }}>
                  <button className="btn btn-ghost" onClick={() => setBookingStep(1)}>Go to passenger</button>
                </div>
              </div>
            ) : (
              <div className="muted">No flight selected.</div>
            )}
          </div>

          <div className="card">
            <h3 style={{ marginTop: 0 }}>PNR Lookup</h3>
            <form onSubmit={lookupPnr}>
              <input placeholder="Enter PNR" value={pnrLookup} onChange={e => setPnrLookup(e.target.value)} />
              <div style={{ marginTop: 8 }}>
                <button className="btn btn-primary" type="submit">Lookup</button>
              </div>
            </form>
            {pnrResult && (
              <div style={{ marginTop: 10 }}>
                <div style={{ fontWeight: 700 }}>PNR: {pnrResult.pnr ?? pnrLookup}</div>
                <div className="muted">Booking ID: {pnrResult.booking_id ?? '—'}</div>
                <div style={{ marginTop: 8 }}>
                  <button className="btn" onClick={() => downloadJSON(pnrResult, `pnr_${pnrResult.pnr || 'booking'}.json`)}>Download JSON</button>
                  <button className="btn" style={{ marginLeft: 8 }} onClick={() => downloadPDF(pnrResult, `pnr_${pnrResult.pnr || 'booking'}.pdf`)}>Download PDF</button>
                </div>
              </div>
            )}
          </div>

          <div className="card">
            <h3 style={{ marginTop: 0 }}>Latest Booking</h3>
            {currentBooking ? (
              <div>
                <div style={{ fontWeight: 700 }}>PNR: {currentBooking.pnr ?? currentBooking.booking_id}</div>
                <div className="muted">Passengers: {currentBooking.passengers?.length ?? '—'}</div>
                <div style={{ marginTop: 8 }}>
                  <button className="btn" onClick={() => downloadJSON(currentBooking, `booking_${currentBooking.booking_id || 'receipt'}.json`)}>Download JSON</button>
                  <button className="btn" style={{ marginLeft: 8 }} onClick={() => downloadPDF(currentBooking, `booking_${currentBooking.booking_id || 'receipt'}.pdf`)}>Download PDF</button>
                </div>
              </div>
            ) : (
              <div className="muted">No bookings yet.</div>
            )}
          </div>
        </aside>
      </div>

      {/* Booking modal / flow */}
      {bookingStep > 0 && selectedFlight && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(10,10,20,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ width: 720, maxWidth: '95%', background: '#fff', padding: 18, borderRadius: 12 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0 }}>Booking — {selectedFlight.airline} {selectedFlight.flight_no}</h3>
              <div>
                <button className="btn" onClick={() => { setBookingStep(0); setSelectedFlight(null); }}>Close</button>
              </div>
            </div>

            <div style={{ marginTop: 12 }}>
              <div className="muted">Price: <strong>{fmtPrice(selectedFlight.dynamic_price ?? selectedFlight.price ?? 0)}</strong></div>

              {bookingStep === 1 && (
                <div>
                  <h4>Passenger details</h4>
                  {passengers.map((p, i) => (
                    <div key={i} style={{ display: 'grid', gridTemplateColumns: '1fr 90px 100px 80px', gap: 8, alignItems: 'center', marginTop: 8 }}>
                      <input placeholder="Full name" value={p.name} onChange={e => updatePassenger(i, 'name', e.target.value)} />
                      <input placeholder="Age" value={p.age} onChange={e => updatePassenger(i, 'age', e.target.value)} />
                      <select value={p.type} onChange={e => updatePassenger(i, 'type', e.target.value)}>
                        <option value="ADT">ADT</option>
                        <option value="CHD">CHD</option>
                        <option value="INF">INF</option>
                      </select>
                      <div>
                        {i === 0 ? <button className="btn" onClick={addPassenger}>+ Add</button> : <button className="btn" onClick={() => removePassenger(i)}>Remove</button>}
                      </div>
                    </div>
                  ))}
                  <div style={{ marginTop: 12 }}>
                    <button className="btn btn-primary" onClick={() => setBookingStep(2)}>Proceed to Payment</button>
                  </div>
                </div>
              )}

              {bookingStep === 2 && (
                <div>
                  <h4>Payment (simulated)</h4>
                  <div style={{ display: 'grid', gap: 8 }}>
                    <select value={payment.method} onChange={e => setPayment({ ...payment, method: e.target.value })}>
                      <option value="card">Card</option>
                      <option value="upi">UPI</option>
                      <option value="netbanking">Netbanking</option>
                    </select>
                    {payment.method === 'card' && (
                      <>
                        <input placeholder="Card number" value={payment.cardNo} onChange={e => setPayment({ ...payment, cardNo: e.target.value })} />
                        <input placeholder="Name on card" value={payment.nameOnCard} onChange={e => setPayment({ ...payment, nameOnCard: e.target.value })} />
                      </>
                    )}
                  </div>

                  <div style={{ marginTop: 12 }}>
                    <button className="btn" onClick={() => setBookingStep(1)}>Back</button>
                    <button className="btn btn-primary" style={{ marginLeft: 8 }} onClick={() => setBookingStep(3)}>Confirm & Book</button>
                  </div>
                </div>
              )}

              {bookingStep === 3 && (
                <div>
                  <h4>Confirm</h4>
                  <div className="muted">Flight: {selectedFlight.airline} {selectedFlight.flight_no} • Price: {fmtPrice(selectedFlight.dynamic_price ?? selectedFlight.price ?? 0)}</div>
                  <div style={{ marginTop: 8 }}>
                    <div style={{ fontWeight: 700 }}>Passengers</div>
                    <ul>
                      {passengers.map((p, i) => <li key={i}>{p.name} — {p.age} — {p.type}</li>)}
                    </ul>
                  </div>
                  <div style={{ marginTop: 12 }}>
                    <button className="btn" onClick={() => setBookingStep(2)}>Back</button>
                    <button className="btn btn-primary" style={{ marginLeft: 8 }} onClick={submitBooking}>Pay & Book</button>
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      )}

      <hr style={{ marginTop: 24 }} />
      <div style={{ marginTop: 12 }}>
        <strong>Developer notes / fixes applied:</strong>
        <ul>
          <li>Fixed inconsistent API base usage (API_BASE now points to root like <code>http://localhost:8000</code> — endpoints use <code>/search</code>, <code>/book</code>, <code>/pnr/:pnr</code>).</li>
          <li>Robust fetch error handling and sensible defaults when backend returns different shapes.</li>
          <li>Cleaned up jsPDF loading and usage for PDF receipts.</li>
          <li>Removed stray/undefined references and ensured all React hooks/state usages are valid.</li>
        </ul>
      </div>
    </div>
  );
}

