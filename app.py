from flask import Flask, render_template, request, redirect, session, flash
import sqlite3
from datetime import datetime
import qrcode
import io
import base64

app = Flask(__name__)
app.secret_key = 'opdmitra_secret_2026_change_this'

def init_db():
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tokens
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  hospital TEXT,
                  opd TEXT,
                  disease TEXT,
                  patient_name TEXT,
                  address TEXT,
                  hospital_fee INTEGER,
                  service_fee INTEGER,
                  amount INTEGER,
                  status TEXT DEFAULT 'Waiting',
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  called_at TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

DISEASES = ["Fever / Sardi Khasi", "Heart / BP", "Skin / Allergy", "Ortho / Haddi", "Gynecology"]

# ============== 36 HOSPITAL + 5 BIMARI KA OPD ==============
OPD_MAP = {
    # MUMBAI - 8
    "Sir J.J. Hospital Mumbai": {"Fever / Sardi Khasi": "OPD 15 - General Medicine", "Heart / BP": "OPD 22 - Cardiology", "Skin / Allergy": "OPD 8 - Dermatology", "Ortho / Haddi": "OPD 31 - Orthopedics", "Gynecology": "OPD 44 - Gynecology"},
    "KEM Hospital Mumbai": {"Fever / Sardi Khasi": "OPD 12 - General Medicine", "Heart / BP": "OPD 18 - Cardiology", "Skin / Allergy": "OPD 6 - Dermatology", "Ortho / Haddi": "OPD 27 - Orthopedics", "Gynecology": "OPD 40 - Gynecology"},
    "Lokmanya Tilak Municipal Hospital Sion": {"Fever / Sardi Khasi": "OPD 10 - General Medicine", "Heart / BP": "OPD 16 - Cardiology", "Skin / Allergy": "OPD 5 - Dermatology", "Ortho / Haddi": "OPD 24 - Orthopedics", "Gynecology": "OPD 35 - Gynecology"},
    "GT Hospital Mumbai": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},
    "St George Hospital Mumbai": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},
    "Cooper Hospital Mumbai": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},
    "Bhabha Hospital Mumbai": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},
    "V.N. Desai Hospital Mumbai": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},

    # PUNE - 4
    "Sassoon General Hospital Pune": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},
    "Naidu Hospital Pune": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},
    "BJ Government Medical College Pune": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},
    "Yashwantrao Chavan Memorial Hospital Pune": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},

    # NAGPUR - 3
    "Government Medical College Nagpur GMCH": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},
    "Indira Gandhi Govt Medical College Nagpur": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},
    "Lata Mangeshkar Hospital Nagpur": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},

    # AURANGABAD - 2
    "Government Medical College Aurangabad": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},
    "Government Cancer Hospital Aurangabad": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},

    # NASHIK - 3
    "District Civil Hospital Nashik": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},
    "Dr. Vasantrao Pawar Medical College Nashik": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},
    "Civil Hospital Malegaon": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},

    # SOLAPUR - 2
    "District Civil Hospital Solapur": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},
    "Government Medical College Solapur": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},

    # AMRAVATI - 2
    "District Civil Hospital Amravati": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},
    "Government Medical College Amravati": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},

    # KOLHAPUR - 2
    "District Civil Hospital Kolhapur": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},
    "CPR Hospital Kolhapur": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},

    # JALGAON - 2
    "District Civil Hospital Jalgaon": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},
    "Government Medical College Jalgaon": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},

    # THANE - 5
    "Thane Civil Hospital": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},
    "Vashi Civil Hospital": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},
    "NMMC Hospital Nerul": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},
    "Kalwa Hospital Thane": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},
    "Central Hospital Ulhasnagar": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},

    # BAATKI DISTRICT - 3
    "District Civil Hospital Sangli": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"},
    "District Civil Hospital Satara": {"Fever / Sardi Khasi": "OPD 101 - General Medicine", "Heart / BP": "OPD 201 - Cardiology", "Skin / Allergy": "OPD 301 - Dermatology", "Ortho / Haddi": "OPD 401 - Orthopedics", "Gynecology": "OPD 501 - Gynecology"},
    "District Civil Hospital Ratnagiri": {"Fever / Sardi Khasi": "OPD 1 - General Medicine", "Heart / BP": "OPD 2 - Cardiology", "Skin / Allergy": "OPD 3 - Dermatology", "Ortho / Haddi": "OPD 4 - Orthopedics", "Gynecology": "OPD 5 - Gynecology"}
}

HOSPITALS = list(OPD_MAP.keys())

# ============== DOCTOR PASSWORD ==============
OPD_PASSWORDS = {}
for hospital in OPD_MAP:
    for disease, opd_name in OPD_MAP[hospital].items():
        short = ''.join([w[0].lower() for w in hospital.split()[:2]])
        num = ''.join([c for c in opd_name if c.isdigit()])
        OPD_PASSWORDS[opd_name] = short + num

def generate_qr(data):
    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode()

def generate_upi_qr(amount, token_id, patient_name):
    # ========== YAHI APNI UPI ID DAAL DE BHAI ==========
    upi_id = "opdmitra@upi" # PhonePe / GPay / Paytm UPI ID
    upi_name = "OpdMitra Hospital"
    # ===================================================

    upi_link = f"upi://pay?pa={upi_id}&pn={upi_name}&am={amount}&cu=INR&tn=Token{token_id}-{patient_name}"

    qr = qrcode.QRCode(version=1, box_size=8, border=4)
    qr.add_data(upi_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.getvalue()).decode()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        hospital = request.form['hospital']
        disease = request.form['disease']
        opd = OPD_MAP[hospital][disease] # Auto OPD

        patient_name = request.form['name']
        address = request.form['address']
        hospital_fee = 20
        service_fee = 10
        amount = 30

        conn = sqlite3.connect('tokens.db')
        c = conn.cursor()
        c.execute("INSERT INTO tokens (hospital, opd, disease, patient_name, address, hospital_fee, service_fee, amount) VALUES (?,?,?,?,?,?,?,?)",
                  (hospital, opd, disease, patient_name, address, hospital_fee, service_fee, amount))
        token_id = c.lastrowid
        conn.commit()
        c.execute("SELECT * FROM tokens WHERE id=?", (token_id,))
        patient = c.fetchone()
        conn.close()

        # Status QR
        qr_data = f"http://localhost:5000/check/{token_id}"
        qr_img = generate_qr(qr_data)

        # Fee QR - NAYA
        fee_qr = generate_upi_qr(amount, token_id, patient_name)

        return render_template('index.html', patient=patient, hospitals=HOSPITALS, diseases=DISEASES, opd_map=OPD_MAP, qr_img=qr_img, fee_qr=fee_qr)

    return render_template('index.html', patient=None, hospitals=HOSPITALS, diseases=DISEASES, opd_map=OPD_MAP, qr_img=None, fee_qr=None)

@app.route('/check/<int:token_id>')
def check_token(token_id):
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute("SELECT * FROM tokens WHERE id=?", (token_id,))
    patient = c.fetchone()
    conn.close()
    return render_template('check.html', patient=patient)

@app.route('/checkin/<int:token_id>', methods=['POST'])
def checkin(token_id):
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute("UPDATE tokens SET status='Completed' WHERE id=?", (token_id,))
    conn.commit()
    conn.close()
    return redirect('/')

@app.route('/doctor/login', methods=['GET', 'POST'])
def doctor_login():
    if request.method == 'POST':
        opd = request.form['opd']
        password = request.form['password']
        if opd in OPD_PASSWORDS and OPD_PASSWORDS[opd] == password:
            session['doctor_opd'] = opd
            return redirect('/doctor/panel')
        else:
            flash('Galat OPD ya Password')
    options = ''.join([f'<option value="{opd}">{opd}</option>' for opd in OPD_PASSWORDS.keys()])
    return f'''<html><head><title>Doctor Login</title><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>body{{font-family:Arial;background:#f0f2f5;padding:20px}}.box{{max-width:400px;margin:100px auto;background:white;padding:30px;border-radius:12px}}h2{{text-align:center;color:#007bff}}input,select{{width:100%;padding:12px;margin:10px 0;border:1px solid #ddd;border-radius:8px;font-size:16px}}button{{width:100%;padding:14px;background:#28a745;color:white;border:none;border-radius:8px;font-size:16px;font-weight:bold;cursor:pointer}}</style>
    </head><body><div class="box"><h2>🏥 Doctor Login</h2><form method="post">
    <label>OPD Select Kare:</label><select name="opd" required><option value="">-- OPD Chuno --</option>{options}</select>
    <label>Password:</label><input type="password" name="password" placeholder="Password" required>
    <button type="submit">Login Kare</button></form></div></body></html>'''

@app.route('/doctor/panel')
def doctor_panel():
    if 'doctor_opd' not in session:
        return redirect('/doctor/login')

    opd = session['doctor_opd']
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM tokens WHERE opd=? AND status='Completed' AND DATE(created_at)=DATE('now')", (opd,))
    completed_count = c.fetchone()[0]

    c.execute("SELECT COUNT(*) FROM tokens WHERE opd=? AND status='Missed'", (opd,))
    missed_count = c.fetchone()[0]

    # 5 ke baad break - par missed call button rahega
    if completed_count >= 5:
        conn.close()
        return f'''<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>body{{font-family:Arial;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);text-align:center;padding:60px 20px;min-height:100vh}}
     .box{{max-width:420px;margin:auto;background:white;padding:40px;border-radius:20px;box-shadow:0 20px 60px rgba(0,0,0,0.3)}}
        h2{{color:#ff9800;font-size:32px;margin-bottom:15px}}
      .count{{font-size:60px;font-weight:bold;color:#667eea;margin:20px 0}}
        button{{padding:15px 24px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;border:none;border-radius:12px;cursor:pointer;margin:10px 0;width:100%;font-size:16px;font-weight:bold}}
     .red{{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%)}}
        p{{color:#666;font-size:15px;line-height:1.6;margin:8px 0}}</style>
        </head><body>
        <div class="box">
        <h2>☕ Break Time!</h2>
        <p>Aapne aaj</p>
        <div class="count">{completed_count}</div>
        <p>patient complete kar liye</p>
        <p style="margin-top:20px;">5 min break le lo</p>
        {f'<form method="post" action="/doctor/call_missed"><button type="submit" class="red">📢 Missed Patient Call Kare ({missed_count})</button></form>' if missed_count > 0 else '<p style="color:#28a745">✅ Koi missed patient nahi hai</p>'}
        <button onclick="location.reload()">🔄 Break Khatam - Refresh</button>
        <br><a href="/doctor/logout" style="color:red;text-decoration:none;margin-top:15px;display:block">Logout</a>
        </div></body></html>'''

    c.execute("SELECT * FROM tokens WHERE opd=? AND status='Called' ORDER BY called_at DESC LIMIT 1", (opd,))
    current = c.fetchone()
    c.execute("SELECT * FROM tokens WHERE opd=? AND status='Waiting' ORDER BY id ASC LIMIT 10", (opd,))
    waiting = c.fetchall()
    c.execute("SELECT * FROM tokens WHERE opd=? AND status='Missed' ORDER BY called_at ASC", (opd,))
    missed = c.fetchall()
    conn.close()
    return render_template('doctor.html', opd=opd, current=current, waiting=waiting, missed=missed, missed_count=missed_count, completed_count=completed_count)

@app.route('/doctor/next', methods=['POST'])
def next_patient():
    if 'doctor_opd' not in session:
        return redirect('/doctor/login')
    opd = session['doctor_opd']
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute("UPDATE tokens SET status='Missed', called_at=? WHERE opd=? AND status='Called'", (datetime.now(), opd))
    c.execute("SELECT id FROM tokens WHERE opd=? AND status='Waiting' ORDER BY id ASC LIMIT 1", (opd,))
    next_token = c.fetchone()
    if next_token:
        c.execute("UPDATE tokens SET status='Called', called_at=? WHERE id=?", (datetime.now(), next_token[0]))
    conn.commit()
    conn.close()
    return redirect('/doctor/panel')

@app.route('/doctor/call_missed', methods=['POST'])
def call_missed():
    if 'doctor_opd' not in session:
        return redirect('/doctor/login')
    opd = session['doctor_opd']
    conn = sqlite3.connect('tokens.db')
    c = conn.cursor()
    c.execute("SELECT id FROM tokens WHERE opd=? AND status='Missed' ORDER BY called_at ASC LIMIT 1", (opd,))
    missed_token = c.fetchone()
    if missed_token:
        c.execute("UPDATE tokens SET status='Called', called_at=? WHERE id=?", (datetime.now(), missed_token[0]))
    conn.commit()
    conn.close()
    return redirect('/doctor/panel')

@app.route('/doctor/logout')
def doctor_logout():
    session.pop('doctor_opd', None)
    return redirect('/doctor/login')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
