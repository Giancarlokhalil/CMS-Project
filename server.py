from flask import Flask, render_template, request, redirect, session
import sqlite3

app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'sfggsgfgsgfsfsfbdvfbfsbsfbsfbfbsbfsbbbfvfbdbdfbfbs'

conn = sqlite3.connect('auth.db')
conn.execute("""
            CREATE TABLE IF NOT EXISTS users
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            role TEXT)
            """)


def create_projects_table():
    conn = sqlite3.connect('projects.db') 
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER,
            title TEXT,
            description TEXT,
            status TEXT,
            deadline DATE,
            FOREIGN KEY(client_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()

create_projects_table()



def create_tasks_table():
    conn = sqlite3.connect('tasks.db')
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            priority TEXT NOT NULL,
            deadline DATE NOT NULL,
            FOREIGN KEY(project_id) REFERENCES projects(id)
        )
    """)
    conn.commit()
    conn.close()

# Call the function to create the tasks table
create_tasks_table()

@app.route("/add_task", methods=['GET', 'POST'])
def add_task():
    # Ensure the user is logged in
    if 'username' not in session:
        return redirect('/login')  # Redirect to login if not logged in

    # Ensure only admins can access this route (you can modify this for consultants too)
    if session.get('role') != 'admin':
        return redirect('/login')  # Redirect non-admins to login

    # Handle form submission for adding a task
    if request.method == 'POST':
        project_id = request.form['project_id']
        title = request.form['title']
        description = request.form['description']
        status = request.form['status']
        priority = request.form['priority']
        deadline = request.form['deadline']

        # Insert new task into the 'tasks' table
        conn = sqlite3.connect('tasks.db')
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (project_id, title, description, status, priority, deadline)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (project_id, title, description, status, priority, deadline))
        conn.commit()
        conn.close()

        return redirect('/tasks')  # Redirect to the tasks page to view all tasks

    # If the request is GET, show the form to add a task
    return render_template('add_task.html')


@app.route("/tasks")
def tasks():
    # Check if the user is logged in
    if 'username' not in session:
        return redirect('/login')  # Redirect to login page if not logged in
    
    # Fetch all tasks from the 'tasks' table in the database
    conn = sqlite3.connect('tasks.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks")
    all_tasks = cursor.fetchall()
    conn.close()
    
    # Render the tasks.html template and pass the tasks data
    return render_template('tasks.html', tasks=all_tasks)


@app.route("/")
def home():
    return render_template('home.html')


@app.route("/consultant")
def consultant():
    # Ensure only consultants can access this page
    if session.get('role') != 'consultant':
        return render_template('login.html', error='Access denied: Consultants only')

    return render_template('consultant.html')

@app.route("/consultant/projects")
def consultant_projects():
    # Ensure only consultants can access this page
    if session.get('role') != 'consultant':
        return render_template('login.html', error='Access denied: Consultants only')

    # Fetch all projects from the database
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    projects = cursor.fetchall()
    conn.close()

    # Render a template to display the projects
    return render_template('consultant_projects.html', projects=projects)



@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = request.form 
        username = data['username']
        password = data['password']
        role = 'user'
        conn = sqlite3.connect("auth.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
        conn.commit()
        conn.close()  
        return redirect('/')
    else:
        return render_template('register.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form
        username = data['username']
        password = data['password']
        db = sqlite3.connect('auth.db')
        user = db.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        
        if user is None:
            return render_template('login.html', error='Wrong credentials')
        else:
            session.clear()
            session['username'] = username
            session['role'] = user[3]
            user_id = user[0]  # Assuming the user ID is in the first column
            
            if user[3] == 'user':
                # Fetch user's projects from the project database
                conn = sqlite3.connect('projects.db')
                projects = conn.execute("SELECT * FROM projects WHERE client_id=?", (user_id,)).fetchall()
                conn.close()
                
                # Pass the projects to the profile template
                return render_template('profile.html', projects=projects)
            
            elif user[3] == 'admin':
                return redirect('/dashboard')
            
            elif user[3] == 'consultant':
                return redirect('/consultant')
            
            else:
                return render_template('login.html', error='Unknown role')
    else:
        return render_template('login.html')


@app.route("/profile")
def profile():
    if (session.get('role') is None) or (session.get('role') != 'user'):
        return render_template('login.html', error='No access')

    return render_template('profile.html')

@app.route("/dashboard")
def dashboard():
    if (session.get('role') is None) or (session.get('role') != 'admin'):
        return render_template('login.html', error='No access')

    # return render_template('dashboard.html')

    conn = sqlite3.connect('projects.db')  # Connecting to the new database
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")  # Fetch all projects
    projects = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', projects=projects)


@app.route("/add_project", methods=['POST'])
def add_project():
    # Ensure only admins can access this route
    if session.get('role') != 'admin':
        return redirect('/login')  # Redirect non-admins to login

    # Retrieve form data
    client_id = request.form['client_id']
    title = request.form['title']
    description = request.form['description']
    status = request.form['status']
    deadline = request.form['deadline']

    # Insert new project into the 'projects' table in the 'projects.db' database
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO projects (client_id, title, description, status, deadline) 
        VALUES (?, ?, ?, ?, ?)
    """, (client_id, title, description, status, deadline))
    conn.commit()
    conn.close()

    # Redirect to the /projects page to view all projects
    return redirect('/projects')



@app.route("/projects")
def projects():
    # Check if the user is logged in
    if 'username' not in session:
        return redirect('/login')  # Redirect to login if not logged in

    # Fetch all projects from the 'projects' database
    conn = sqlite3.connect('projects.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects")
    all_projects = cursor.fetchall()
    conn.close()

    # Render the projects.html template and pass the projects data
    return render_template('projects.html', projects=all_projects)

@app.route("/logout")
def logout():
    session.clear()
    return redirect('/')



@app.route('/users')
def users():
    conn = sqlite3.connect("auth.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")  # Fetch data
    users_list = cursor.fetchall()  # Get all users from the database
    conn.close()  # Close the connection
    return render_template('users.html', users=users_list)


# Add user route
@app.route("/add_user", methods=['POST'])
def add_user():
    if session.get('role') != 'admin':
        return redirect('/login')  # Redirect if not an admin

    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    # Add user to database
    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
    conn.commit()
    conn.close()

    return redirect('/users')  


@app.route("/edit_user/<int:user_id>", methods=['GET', 'POST'])
def edit_user(user_id):
    if session.get('role') != 'admin':
        return redirect('/login')  # Redirect if not an admin

    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        # Fetch data from the form
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']

        # Check for empty fields
        if not username or not password or not role:
            conn.close()
            return "All fields are required.", 400

        # Update user details in the database
        cursor.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?",
                       (username, password, role, user_id))
        conn.commit()
        conn.close()
        return redirect('/users')  # Redirect to the users page

    # Fetch the user details for the form
    cursor.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return render_template('edit_user.html', user=user)
    else:
        return "User not found.", 404


# Delete user route
@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect('/login')  # Redirect if not an admin

    conn = sqlite3.connect('auth.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()

    return redirect('/users')  # Redirect to the users page after deletion



if __name__ == '__main__':
    app.run()
