from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
import MySQLdb.cursors
import MySQLdb.cursors
from flask_bcrypt import Bcrypt
from functools import wraps
import mysql.connector 

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key

# MySQL Configurations
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '123456'
app.config['MYSQL_DB'] = 'emp_prod'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:123456@localhost/emp_prod'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
mysql = MySQL(app)

bcrypt = Bcrypt(app)





# Login required decorator
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'user_logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('You need to login first.')
            return redirect(url_for('login'))
    return wrap

# Home route
@app.route('/')
@login_required
def home():
    user_logged_in = session.get('user_logged_in')
    return render_template('home.html', user_logged_in=user_logged_in)

# Employee route
@app.route('/employees')
@login_required
def employees():
    # Logic for managing employees will go here

    # cursor = mysql.cursor(dictionary=True)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Modify the query to include department names
    query = '''
        SELECT e.id, e.f_name, e.m_name, e.l_name, e.designation, d.name AS department
        FROM employees e
        JOIN departments d ON e.department_id = d.id
    '''
    cursor.execute(query)
    employee_data = cursor.fetchall()
    cursor.close()

    user_logged_in = session.get('user_logged_in')
    return render_template('employees.html', employees=employee_data, user_logged_in=user_logged_in)


# Employee route
@app.route('/departments')
@login_required
def departments():
    # Logic for managing employees will go here

    # cursor = mysql.cursor(dictionary=True)
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM departments")
    department_data = cursor.fetchall()
    cursor.close()
    user_logged_in = session.get('user_logged_in')
    
    return render_template('departments.html', departments=department_data, user_logged_in=user_logged_in)


@app.route('/add_department', methods=['GET', 'POST'])
@login_required
def add_department():
    if request.method == 'POST':
        department_name = request.form['department_name']

        # Insert the department into the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("INSERT INTO departments (name) VALUES (%s)", (department_name,))
        mysql.connection.commit()
        cursor.close()

        flash('Department added successfully!')
        return redirect(url_for('add_department'))
    
    return render_template('add_department.html')

@app.route('/edit_department/<int:dept_id>', methods=['GET', 'POST'])
@login_required
def edit_department(dept_id):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM departments WHERE id = %s", (dept_id,))
    department = cursor.fetchone()
    cursor.close()

    if request.method == 'POST':
        department_name = request.form['department_name']
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE departments SET name = %s WHERE id = %s", (department_name, dept_id))
        mysql.connection.commit()
        cursor.close()
        flash('Department updated successfully!')
        return redirect(url_for('edit_department', dept_id=dept_id))

    return render_template('edit_department.html', department=department)

@app.route('/delete_department/<int:dept_id>', methods=['POST'])
@login_required
def delete_department(dept_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM departments WHERE id = %s", (dept_id,))
    mysql.connection.commit()
    cursor.close()
    flash('Department deleted successfully!')
    return redirect(url_for('employees'))  # Redirect to a relevant page



# Predict productivity route
@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    if request.method == 'POST':
        department_id = request.form['department']
        employee_id = request.form['employee']
        working_date = request.form['working_date']
        team_number = request.form['team_number']
        quarter = request.form['quarter']
        workers =int(request.form['workers'])
        std_minute_value = float(request.form['std_minute_value'])  
        incentive_day = float(request.form['incentive_day'])  

        # Calculate the prediction based on input values
        prediction = calculate_prediction(workers, std_minute_value, incentive_day)

        # Insert the data into the productivities table
        cursor = mysql.connection.cursor()
        cursor.execute('''
            INSERT INTO productivities (employee_id, department_id, working_date, team_number, quarter, workers, std_minute_value, incentive_day, prediction)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (employee_id, department_id, working_date, team_number, quarter, workers, std_minute_value, incentive_day, prediction))
        mysql.connection.commit()
        cursor.close()

        
        flash('Productivity predicted and saved successfully!')
        # Pass the prediction result to the template
        return render_template('predict.html', departments=get_departments(), prediction=prediction)

    # Fetch departments for dropdown
    return render_template('predict.html', departments=get_departments())
    
     # return render_template('predict.html')

# Utility function to fetch departments
def get_departments():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, name FROM departments")
    departments = cursor.fetchall()
    cursor.close()
    return departments

def calculate_prediction(workers, std_minute_value, incentive_day):
    # Example logic for prediction percentage
    prediction = (workers * std_minute_value) + incentive_day
    return 75

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    # Assuming the current logged-in user is fetched from the database based on their session
    user_id = session.get('user_id')
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT name, email FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()

    if request.method == 'POST':
        # Process form data
        name = request.form['name']
        email = request.form['email']
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Update user details
        if password:
            if not confirm_password:
                message = 'Please confirm your password!'
            elif password != confirm_password:
                message = 'Passwords do not match!'
            else:

                # Hash the password
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                cursor = mysql.connection.cursor()
                cursor.execute(''' 
                    UPDATE users 
                    SET name = %s, email = %s, password = %s 
                    WHERE id = %s
                ''', (name, email, hashed_password, user_id))
                mysql.connection.commit()
                cursor.close()
                message = 'Profile updated successfully!'
        else:
            # Update without changing the password
            cursor = mysql.connection.cursor()
            cursor.execute('''
                UPDATE users 
                SET name = %s, email = %s
                WHERE id = %s
            ''', (name, email, user_id))
            mysql.connection.commit()
            cursor.close()
            message = 'Profile updated successfully!'

        # Re-fetch updated user data
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT name, email FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()

        return render_template('profile.html', user=user, message=message)

    # Render the profile page for GET requests
    return render_template('profile.html', user=user)

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Create a MySQL cursor to execute the query
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Execute query to get the user with the provided email
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        print("user")
        print(user)

        if user:
            # Check if the provided password matches the stored hashed password
            if bcrypt.check_password_hash(user['password'], password):
                # Store user info in session if login is successful
                session['user_id'] = user['id']
                # session['username'] = user['username']
                session['email'] = user['email']
                session['user_logged_in'] = True


                # print(session['user_logged_in'])
                # print(user['email'])
                flash(f'Welcome {user["name"]}!', 'success')
                return render_template('home.html', user_logged_in=True)
            
            else:
                return render_template('login.html', message='Incorrect password! Please try again')

                # flash('Incorrect password! Please try again.', 'danger')
        else:
                return render_template('login.html', message='Email not found! Please register first')
            # flash('Email not found! Please register first.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Create a MySQL cursor to execute the query
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check if the email already exists
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()

        if user:
            flash('Email already exists! Please use a different email.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match! Please try again.', 'danger')
        else:
            # Hash the password before storing it
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

            # Insert the new user into the database
            cursor.execute('INSERT INTO users (username, email, password) VALUES (%s, %s, %s)', (username, email, hashed_password))
            mysql.connection.commit()

            flash('Registration successful! You can now log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')




@app.route('/add_employee', methods=['GET', 'POST'])
def add_employee():
    if request.method == 'POST':
        
        first_name = request.form['first_name']
        middle_name = request.form.get('middle_name', '')  # Middle name is optional
        last_name = request.form['last_name']
        department_id = request.form['department']
        designation = request.form['designation']

        # Insert the new employee into the database
        cursor = mysql.connection.cursor()
        cursor.execute('''
            INSERT INTO employees (f_name, m_name, l_name, department_id, designation)
            VALUES (%s, %s, %s, %s, %s)
        ''', (first_name, middle_name, last_name, department_id, designation))
        mysql.connection.commit()
        cursor.close()
        return render_template('add_employee.html', message='Employee added successfully')

        # Redirect or display success message
        # flash('Employee added successfully!')
        # return redirect(url_for('add_employee'))
    pass
    # For GET requests, fetch available departments from the database
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, name FROM departments")
    all_departments = cursor.fetchall()

    print("all_departments")
    print(all_departments)
    cursor.close()      
    return render_template('add_employee.html', departments=all_departments)


@app.route('/edit_employee/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def edit_employee(employee_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    
    if request.method == 'POST':
        first_name = request.form['first_name']
        middle_name = request.form['middle_name']
        last_name = request.form['last_name']
        department_id = request.form['department']
        designation = request.form['designation']
        
        cursor.execute('''
            UPDATE employees
            SET f_name = %s, m_name = %s, l_name = %s, department_id = %s, designation = %s
            WHERE id = %s
        ''', (first_name, middle_name, last_name, department_id, designation, employee_id))
        
        mysql.connection.commit()
        cursor.close()
        flash('Employee updated successfully!')
        return redirect(url_for('edit_employee', message='Employee updated successfully',employee_id=employee_id))
    
    cursor.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))
    employee = cursor.fetchone()
    cursor.execute("SELECT id, name FROM departments")
    departments = cursor.fetchall()
    cursor.close()
    
    return render_template('edit_employee.html', employee=employee, departments=departments)


@app.route('/delete_employee/<int:employee_id>', methods=['POST'])
@login_required
def delete_employee(employee_id):
    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM employees WHERE id = %s", (employee_id,))
    mysql.connection.commit()
    cursor.close()
    flash('Employee deleted successfully!')
    return redirect(url_for('employees'))  # Adjust redirect as needed

@app.route('/get_employees/<int:department_id>', methods=['GET'])
def get_employees(department_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT id, CONCAT(f_name, ' ', l_name) AS name FROM employees WHERE department_id = %s", (department_id,))
    employees = cursor.fetchall()
    cursor.close()

    # print("employees")
    # print(employees)
    return jsonify(employees)

@app.route('/employee/<int:employee_id>')
def employee_productivity(employee_id):
    # Fetch the productivity data for the selected employee from the database
    query = "SELECT * FROM productivities WHERE employee_id = %s"
    cursor = mysql.connection.cursor()
    cursor.execute(query, (employee_id,))
    employee_productivities = cursor.fetchall()
    cursor.close()
    
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM employees WHERE id = %s", (employee_id,))
    employee = cursor.fetchone()

    mysql.connection.commit()
    cursor.close()
    # Pass the fetched data to the HTML template
    return render_template('view_employee_productivities.html', productivities=employee_productivities, employee=employee)

# @app.route('/predict_productivity', methods=['POST'])
# def predict_productivity():
    # department_id = request.form['department']
    # user_id = request.form['user']
    # working_day = request.form['working_day']
    # team_number = request.form['team_number']
    # quarter = request.form['quarter']
    # workers = request.form['workers']
    # std_minute_value = request.form['std_minute_value']
    # incentive_day = request.form['incentive_day']

    # # Implement your ML model prediction here
    # # For demo purposes, let's assume the result is a random number
    # productivity_result = calculate_productivity(department_id, user_id, working_day, team_number, quarter, workers, std_minute_value, incentive_day)

    # cursor = mysql.connection.cursor()
    # cursor.execute('''
    #     INSERT INTO productivity (user_id, productivity_result, month, date)
    #     VALUES (%s, %s, %s, %s)
    # ''', (user_id, productivity_result, working_day, datetime.now()))
    # mysql.connection.commit()
    # cursor.close()

    # flash('Productivity predicted and saved successfully!')


    # return redirect(url_for('predict_productivity'))
    # return render_template('predict.html')

def calculate_productivity(department_id, user_id, working_day, team_number, quarter, workers, std_minute_value, incentive_day):
    # Replace with your ML model logic
    return 75  # Example result



# Logout route
@app.route('/logout')
@login_required
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
