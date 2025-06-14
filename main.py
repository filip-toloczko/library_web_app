from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
import os

app = Flask(__name__)
app.secret_key = 'super_secret_key'

def create_connection():
    #connect to my database
    try:
        conn = psycopg2.connect(
            host="127.0.0.1",
            database="library_db",
            user="postgres",
            password="password",
            port="5433"
        )
        return conn
    except psycopg2.DatabaseError as e:
        print(f"Database connection error: {e}")
        return None

@app.route('/')
def index():
    #go to home page
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    #login
    if request.method == 'POST':

        #email and password the user entered
        email = request.form['email']
        password = request.form['password']
        
        conn = create_connection()
        
        cur = conn.cursor()
        
        #check if librarian
        cur.execute("SELECT password, name FROM Librarians WHERE email = %s", (email,))
        librarian_result = cur.fetchone()
        #if it is a librarian check if the password matches
        if librarian_result and librarian_result[0] == password:
            #handle librarian variables and go to the lib page
            session['user_email'] = email
            session['user_name'] = librarian_result[1]
            session['user_type'] = 'librarian'
            cur.close()
            conn.close()
            return redirect(url_for('librarian_dashboard'))
        
        #check if client
        cur.execute("SELECT password, name FROM Clients WHERE email = %s", (email,))
        client_result = cur.fetchone()
        #if its a client and the password matches
        if client_result and client_result[0] == password:
            #client variables and dashboard
            session['user_email'] = email
            session['user_name'] = client_result[1]
            session['user_type'] = 'client'
            cur.close()
            conn.close()
            return redirect(url_for('client_dashboard'))
        
        cur.close()
        conn.close()
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    #register the user
    if request.method == 'POST':
        user_type = request.form['user_type']
        
        conn = create_connection()
        
        #librarian registration 
        if user_type == 'librarian':
            ssn = request.form['ssn']
            name = request.form['name']
            email = request.form['email']
            password = request.form['password']
            salary = request.form['salary']
            
            if add_librarian(conn, ssn, name, email, password, salary):
                conn.close()
                return redirect(url_for('login'))
        #client registration
        elif user_type == 'member':
            email = request.form['email']
            password = request.form['password']
            name = request.form['name']
            card_number = request.form['card_number']
            address = request.form['address']
            
            if add_member(conn, email, password, name, card_number, address):
                conn.close()
                return redirect(url_for('login'))
        
        conn.close()
    
    return render_template('register.html')

def add_librarian(conn, ssn, name, email, password, salary):
    #add librarian to database
    
    cur = conn.cursor()
    cur.execute("INSERT INTO Librarians(ssn, name, email, password, salary) VALUES (%s, %s, %s, %s, %s)",
                (ssn, name, email, password, salary))

    cur.close()
    return True

def add_member(conn, email, password, name, card_number, address):
    #add member to database
    cur = conn.cursor()

    cur.execute("INSERT INTO Clients(email, name, password) VALUES (%s, %s, %s)",
                (email, name, password))
    

    cur.execute("INSERT INTO ClientAddresses(email, address) VALUES (%s, %s)",
                (email, address))
    


    cur.execute("INSERT INTO CreditCards(email, card_address, card_number) VALUES (%s, %s, %s)",
                (email, address, card_number))
    
    conn.commit()
    cur.close()
    return True




@app.route('/client_dashboard')
def client_dashboard():
    #main page for the clients

    
    return render_template('client_dashboard.html', user_name=session['user_name'])

@app.route('/librarian_dashboard')
def librarian_dashboard():
    #main page for librarians
    
    return render_template('librarian_dashboard.html', user_name=session['user_name'])

@app.route('/search')
def search():
    #show all the available documents

    
    conn = create_connection()
    if conn is None:
        return redirect(url_for('client_dashboard'))
    
    cur = conn.cursor()
    
    query = """SELECT 
        d.barcode, d.year, d.publisher, d.copies,
        j.title AS journal_title, j.issue, j.name AS journal_name, j.authors, j.number,
        b.title AS book_title, b.authors AS book_authors, b.edition, b.pages,
        m.name AS magazine_name, m.month
        FROM documents d
        LEFT JOIN journal j ON d.barcode = j.barcode
        LEFT JOIN nonjournal n ON d.barcode = n.barcode
        LEFT JOIN book b ON n.isbn = b.isbn
        LEFT JOIN magazine m ON n.isbn = m.isbn;"""
    
    cur.execute(query)
    documents = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('search.html', documents=documents)

@app.route('/add_book', methods=['GET', 'POST'])
def add_book_route():
    #let libs enter new books and docs
    
    if request.method == 'POST':
        barcode = request.form['barcode']
        copies = request.form['copies']
        publisher = request.form['publisher']
        year = request.form['year']
        isbn = request.form['isbn']
        title = request.form['title']
        authors = request.form['authors']
        edition = request.form['edition']
        pages = request.form['pages']
        
        if add_book(barcode, copies, publisher, year, isbn, title, authors, edition, pages):

            return redirect(url_for('librarian_dashboard'))
    
    return render_template('add_book.html')

def add_book(barcode, copies, publisher, year, isbn, title, authors, edition, pages):
    #function to add the books
    conn = create_connection()
    if conn is None:
        return False
    
    cur = conn.cursor()
    try:

        cur.execute(
            "INSERT INTO Documents (barcode, copies, publisher, year) VALUES (%s, %s, %s, %s)",
            (barcode, copies, publisher, year))
        cur.execute(
            "INSERT INTO NonJournal (isbn, barcode) VALUES (%s, %s)",
            (isbn, barcode))
        
   
        cur.execute(
            "INSERT INTO Book (isbn, title, authors, edition, pages) VALUES (%s, %s, %s, %s, %s)",
            (isbn, title, authors, edition, pages))
        
        conn.commit()
        return True
    except psycopg2.DatabaseError as e:
        conn.rollback()
        print(f"Database error: {e}")
        return False
    finally:
        cur.close()
        conn.close()

@app.route('/account')
def account():
    #page to view account info
    
    return render_template('account.html', 
                         user_name=session['user_name'], 
                         user_email=session['user_email'],
                         user_type=session['user_type'])

@app.route('/logout')
def logout():
    #logout of your account
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)