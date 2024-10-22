import re
import sqlite3


def setup_database():
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        email TEXT UNIQUE NOT NULL,
                        password TEXT NOT NULL,
                        account_number TEXT UNIQUE NOT NULL,
                        balance REAL NOT NULL DEFAULT 10000,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        transaction_type TEXT,
                        amount REAL,
                        balance_after REAL,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                      )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER,
                        action TEXT,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(user_id) REFERENCES users(id)
                      )''')
    conn.commit()
    conn.close()

def valid_phone_number(phone_number):
    return bool(re.match(r'^(?:\+234|0)(80|81|70|71|90|91)[0-9]{8}$', phone_number))

def valid_email(email):
    return bool(re.match(r'([a-zA-Z0-9.]+@[a-z]+\.(com|edu|org))', email))

def validate_password(password):
    pattern = r'^(?=.[A-Z])(?=.[a-z])(?=.*\d).{8,}$'
    if not re.match(pattern, password):
        print("Invalid password. Password must be at least 8 characters long, "
              "contain at least one uppercase letter, one lowercase letter, "
              "one digit, and one special character.")
        return False
    return True

def email_exists(email):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def phone_number_exists(phone_number):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE account_number = ?", (phone_number[1:],))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

def create_account(email, password, number):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()
    account_number = number[1:]
    try:
        cursor.execute("INSERT INTO users (email, password, account_number) VALUES (?, ?, ?)",
                       (email, password, account_number))
        conn.commit()
        print(f"Account creation successful.\nYour account number is: {account_number}")
        print("You have received an initial balance of 10000 naira from Abbey's Bank!")
    except sqlite3.IntegrityError:
        print("Email or account number already exists.")
    conn.close()

def log_user_action(user_id, action):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_log (user_id, action) VALUES (?, ?)", (user_id, action))
    conn.commit()
    conn.close()

def login(email, password):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ? AND password = ?", (email, password))
    user = cursor.fetchone()
    if user:
        user_id = user[0]
        log_user_action(user_id, 'logged in')
        print("Login successful")
        conn.close()
        return user_id
    else:
        print("Invalid credentials")
        conn.close()
        return None

def check_balance(user_id):
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    balance = cursor.fetchone()[0]
    print(f"Current balance: {balance} naira")
    conn.close()

def deposit_amount(user_id, amount):
    if amount <= 0:
        print("Amount must be greater than zero")
        return
    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    current_balance = cursor.fetchone()[0]
    new_balance = current_balance + amount
    cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user_id))
    cursor.execute("INSERT INTO transactions (user_id, transaction_type, amount, balance_after) VALUES (?, ?, ?, ?)",
                   (user_id, 'deposit', amount, new_balance))
    conn.commit()
    conn.close()
    print(f"Deposited {amount} naira. New balance: {new_balance} naira")

def transfer_amount(sender_id, recipient_account_number, amount):
    if amount <= 0:
        print("Amount must be greater than zero.")
        return

    conn = sqlite3.connect('bank_system.db')
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM users WHERE id = ?", (sender_id,))
    sender_balance = cursor.fetchone()[0]

    if amount > sender_balance:
        print("Transfer amount exceeds account balance.")
        conn.close()
        return

    cursor.execute("SELECT id, balance FROM users WHERE account_number = ?", (recipient_account_number,))
    recipient = cursor.fetchone()
    if not recipient:
        print("Recipient account number not found.")
        conn.close()
        return

    recipient_id, recipient_balance = recipient
    cursor.execute("SELECT email FROM users WHERE account_number = ?", (recipient_account_number,))
    recipient_name = cursor.fetchone()[0]

    while True:
        confirmation = input(f"Are you sure you want to send {amount} naira to {recipient_name}? "
                             "Type 'y' to confirm or 'n' to decline: ").strip().lower()

        if confirmation == 'y':
            print("Transfer in progress...")

            new_sender_balance = sender_balance - amount
            cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_sender_balance, sender_id))
            cursor.execute("INSERT INTO transactions (user_id, transaction_type, amount, balance_after) VALUES (?, ?, ?, ?)",
                           (sender_id, 'transfer', -amount, new_sender_balance))

            new_recipient_balance = recipient_balance + amount
            cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_recipient_balance, recipient_id))
            cursor.execute("INSERT INTO transactions (user_id, transaction_type, amount, balance_after) VALUES (?, ?, ?, ?)",
                           (recipient_id, 'transfer', amount, new_recipient_balance))

            conn.commit()
            print(f"Transferred {amount} naira to account {recipient_account_number}. Your new balance is {new_sender_balance} naira.")
            break
        elif confirmation == 'n':
            print("Transfer canceled.")
            break
        else:
            print("Invalid input. Please type 'y' or 'n'.")
    conn.close()

def main():
    setup_database()
    while True:
        print("\n1. Create Account")
        print("2. Login")
        print("3. Logout")
        choice = input("Choose an option: ")
        if choice == '1':
            while True:
                email = input("Enter email: ").strip()
                if not valid_email(email):
                    print("Invalid email format. Please enter a valid email address.")
                elif email_exists(email):
                    print("This email is already registered. Please enter a different email.")
                else:
                    break

            while True:
                number = input("Enter your phone number in this format (08012345678): ").strip()
                if not valid_phone_number(number):
                    print("Invalid phone number format. Please use the format (08012345678).")
                elif phone_number_exists(number):
                    print("This phone number is already registered. Please enter a different number.")
                else:
                    break

            while True:
                password = input("Enter password: ").strip()
                confirmPassword = input("Re-enter password: ").strip()
                if password != confirmPassword:
                    print("Passwords do not match, re-enter password.")
                elif not validate_password(password):
                    continue
                else:
                    break

            create_account(email, password, number)
        elif choice == '2':
            email = input("Enter email: ").strip()
            password = input("Enter password: ").strip()
            user_id = login(email, password)
            if user_id:
                while True:
                    print("\n1. Check Balance")
                    print("2. Deposit Amount")
                    print("3. Transfer Amount")
                    print("4. Logout")
                    action = input("Choose an action: ")
                    if action == '1':
                        check_balance(user_id)
                    elif action == '2':
                        amount = float(input("Enter amount to deposit: "))
                        deposit_amount(user_id, amount)
                    elif action == '3':
                        amount = float(input("Enter amount to transfer: "))
                        recipient_account_number = input("Enter recipient account number: ")
                        transfer_amount(user_id, recipient_account_number, amount)
                    elif action == '4':
                        log_user_action(user_id, 'logged out')
                        print("Logged out.")
                        break
                    else:
                        print("Invalid action, Please try again")
        elif choice == '3':
            break
        else:
            print("Invalid option, Please try again")

main()