from datetime import datetime
import matplotlib
matplotlib.use("Agg")  # Non-GUI backend for servers
import matplotlib.pyplot as plt
import sqlite3, os
from flask import Flask, render_template,request, session, redirect, url_for, send_file

app = Flask(__name__)
app.secret_key = "super_secret_key"  # You can set any secret string


# ✅ Create or connect to the SQLite database
def init_db():
    conn = sqlite3.connect('admin.db')
    cursor = conn.cursor()

    cursor.execute('''
         CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
         sem TEXT,
         department TEXT,
        role TEXT NOT NULL,
        student_name TEXT,
        age INTEGER,
        rollno TEXT,
        city TEXT
        )
    ''')
    

    # Insert default admin
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', '123', 'admin'))

       # ✅ Create results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            python INTEGER,
            dsa INTEGER,
            iks INTEGER,
            fsd INTEGER,
            cn INTEGER,
            os INTEGER,
            total INTEGER,
            average REAL,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')

    conn.commit()
    conn.close()
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect("admin.db")
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone()
        conn.close()

        if result:
            role = result[0]
            session["username"] = username  # ✅ Stores username in session

            if role == "admin":
                return redirect(url_for("admin_dashboard"))
            elif role == "user":
                return redirect(url_for("user_dashboard"))
        else:
            return "Invalid username or password"

    return render_template("login.html")



    return render_template("login.html")

# ✅ Admin Dashboard
@app.route("/admin")
def admin_dashboard():
    return render_template("admin.html")

# ✅ User Dashboard
@app.route("/user")
def user_dashboard():
    return render_template("user.html")



@app.route("/addstudent", methods=["GET", "POST"])

def addstudent():
    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()

    message = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        student_name = request.form["student_name"]
        age = request.form["age"]
        rollno = request.form["rollno"]
        city = request.form["city"]

        try:
            cursor.execute('''
                INSERT INTO users (username, password, role, student_name, age, rollno, city)
                VALUES (?, ?, 'user', ?, ?, ?, ?)
            ''', (username, password, student_name, age, rollno, city))
            conn.commit()
            message = "Student added successfully!"
        except sqlite3.IntegrityError:
            message = "Username already exists!"   
    conn.close()

    return render_template("addstudent.html",message=message)

@app.route("/attendance")
def attendance():
    return "Attendance Page"

# ✅ User Features

@app.route("/showresult")
def showresult():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM results WHERE username = ?", (username,))
    result = cursor.fetchone()
    conn.close()

    if result:
        subjects = ["Python", "DSA", "IKS", "FSD", "CN", "OS"]
        marks = [result[2], result[3], result[4], result[5], result[6], result[7]]
        chart_file = generate_bar_chart(subjects, marks, username)
        return render_template("user_showresult.html", result=result, chart_file=chart_file)
    else:
        return "No result found for user."

def generate_bar_chart(subjects, marks, username):
    plt.figure(figsize=(8, 5))
    bars = plt.bar(subjects, marks)
    plt.ylim(0, 100)
    plt.title(f"Marks for {username}")
    plt.ylabel("Marks")

    for bar, mark in zip(bars, marks):
        bar.set_color("green" if mark >= 40 else "red")
        plt.text(bar.get_x() + bar.get_width()/2, mark + 2, str(mark), ha='center')

    plt.tight_layout()
    filename = f"chart_{username}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join("static", filename)
    plt.savefig(filepath)
    plt.close()
    return filename

@app.route("/result_chart")
def result_chart():
    if "username" not in session:
        return redirect(url_for("login"))

    username = session["username"]

    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()
    cursor.execute("SELECT python, dsa, iks, fsd, cn, os FROM results WHERE username = ?", (username,))
    data = cursor.fetchone()
    conn.close()

    if not data:
        return "No data"

    subjects = ["Python", "DSA", "IKS", "FSD", "CN", "OS"]
    marks = list(map(int, data))

    # Create bar chart
    plt.figure(figsize=(8, 5))
    plt.bar(subjects, marks, color="teal")
    plt.title("Subject-wise Marks")
    plt.xlabel("Subjects")
    plt.ylabel("Marks")
    plt.ylim(0, 100)
    plt.tight_layout()

    chart_path = "static/result_chart.png"
    plt.savefig(chart_path)
    plt.close()

    return send_file(chart_path, mimetype='image/png')


@app.route("/attendancecheck")
def attendancecheck():
    return "Attendance Check Page for User"

# ✅ Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



@app.route("/view")
def view():
    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT student_name, age, rollno, city, username, password
        FROM users WHERE role = 'user'
    """)
    students = cursor.fetchall()
    conn.close()
    return render_template('view.html', students=students)



@app.route("/delete/<username>")
def delete_user(username):
    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()

    return redirect(url_for("view"))  # Go back to view page




@app.route("/result", methods=["GET", "POST"])
def result():
    conn   = sqlite3.connect("admin.db")
    cursor = conn.cursor()

    # pull a fresh list of student usernames for the dropdown
    cursor.execute("SELECT username FROM users WHERE role = 'user'")
    students = [row[0] for row in cursor.fetchall()]

    if request.method == "POST":
        # ── 1. fetch data from the form ───────────────────────────
        username   = request.form["username"]
        sem        = request.form["sem"]
        department = request.form["department"]

        # marks – convert to int, you can wrap each in try/except if you want validation
        python_mark = int(request.form["python"])
        dsa_mark    = int(request.form["dsa"])
        iks_mark    = int(request.form["iks"])
        fsd_mark    = int(request.form["fsd"])
        cn_mark     = int(request.form["cn"])
        os_mark     = int(request.form["os"])

        # ── 2. calculate total / average ──────────────────────────
        total   = python_mark + dsa_mark + iks_mark + fsd_mark + cn_mark + os_mark
        average = round(total / 6, 2)          # round to two decimals

        # ── 3. insert into DB ─────────────────────────────────────
        cursor.execute("""
            INSERT INTO results
            (username, sem, department, python, dsa, iks, fsd, cn, os, total, average)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            username, sem, department,
            python_mark, dsa_mark, iks_mark, fsd_mark, cn_mark, os_mark,
            total, average
        ))
        conn.commit()
        conn.close()
        return redirect(url_for("viewresults"))

    # GET request → show the add‑result form
    conn.close()
    return render_template("result.html", students=students)



@app.route("/viewresults")
def viewresults():
    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM results")
    results = cursor.fetchall()
    conn.close()
    return render_template("viewresults.html", results=results)

@app.route("/searchresult", methods=["GET", "POST"])
def searchresult():
    """Search by roll‑number (or username) and show marks + bar chart."""
    chart_filename = None
    result_row = None
    error_msg = None

    if request.method == "POST":
        rollno = request.form["rollno"].strip()

        conn = sqlite3.connect("admin.db")
        cursor = conn.cursor()

        # get username + marks for that roll number
        cursor.execute("""
            SELECT r.*, u.student_name
            FROM results AS r
            JOIN users   AS u ON r.username = u.username
            WHERE u.rollno = ?
        """, (rollno,))
        row = cursor.fetchone()

        if row:
            result_row = row
            # column order from PRAGMA table_info: see your earlier printout
            subjects = ["Python", "DSA", "IKS", "FSD", "CN", "OS"]
            marks    = [row[2], row[3], row[4], row[5], row[6], row[7]]

            chart_filename = generate_bar_chart(subjects, marks, rollno)
        else:
            error_msg = f"No result found for roll number {rollno}"

        conn.close()

    return render_template(
        "searchresult.html",
        result=result_row,
        chart_file=chart_filename,
        error=error_msg
    )


# ---------- helper ------------
def generate_bar_chart(subj, marks, rollno):
    """Save chart to static/, return filename."""
    plt.figure(figsize=(8, 5))
    bars = plt.bar(subj, marks)
    plt.ylim(0, 100)
    plt.title(f"Marks for Roll No {rollno}")
    plt.ylabel("Marks")
    plt.xlabel(f"Subjects Of Rollno {rollno}", fontsize=12)
    plt.grid(axis='y', linestyle='--', alpha=0.5)

    # quick color highlight
    for b, m in zip(bars, marks):
        if m >= 80:
            b.set_color("tab:purple")
        elif m >= 40:
            b.set_color("tab:cyan")
        else :
            b.set_color("tab:red")

    # quick color highlight
    #  for b, m in zip(bars, marks):
       # b.set_color("tab:green" if m >= 40 else "tab:red")

    # annotate each bar
    for idx, m in enumerate(marks):
        plt.text(idx, m + 2, str(m), ha="center", va="bottom", fontsize=8)

    plt.tight_layout()

    # unique filename (timestamp avoids browser cache)
    fname = f"chart_{rollno}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    path  = os.path.join("static", fname)
    plt.savefig(path)
    plt.close()
    return fname

@app.route("/update_result_inline/<int:result_id>", methods=["POST"])
def update_result_inline(result_id):
    sem        = request.form["sem"]
    department = request.form["department"]
    python     = int(request.form["python"])
    dsa        = int(request.form["dsa"])
    iks        = int(request.form["iks"])
    fsd        = int(request.form["fsd"])
    cn         = int(request.form["cn"])
    os         = int(request.form["os"])

    total   = python + dsa + iks + fsd + cn + os
    average = round(total / 6, 2)

    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE results
        SET sem = ?, department = ?, python = ?, dsa = ?, iks = ?, fsd = ?, cn = ?, os = ?, total = ?, average = ?
        WHERE id = ?
    """, (sem, department, python, dsa, iks, fsd, cn, os, total, average, result_id))
    conn.commit()
    conn.close()

    return redirect(url_for("viewresults"))

    return render_template("editresult.html", result=result)

@app.route("/deleteresult/<int:result_id>")
def delete_result(result_id):
    conn = sqlite3.connect("admin.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM results WHERE id = ?", (result_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("viewresults"))

# ✅ Run and initialize DB
if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=7000)
