import random
import sqlite3


def generate_pin():
    pin = random.randint(0000, 9999)
    if len(str(pin)) == 4:
        return pin
    else:
        return generate_pin()


def generate_checksum(card_number):
    card_sum = get_algo_sum(card_number)
    checksum = (10 - (card_sum % 10)) if card_sum % 10 != 0 else 0
    return checksum


def get_algo_sum(card_number):
    card = [int(x) * 2 if (count + 1) % 2 != 0 else int(x) for count, x in enumerate(card_number)]
    card = [int(x) - 9 if int(x) > 9 else int(x) for x in card]
    card_sum = sum(card)
    return card_sum


def check_algo_sum(card_number_full):
    without_checksum = card_number_full[:-1]
    actual_checksum = int(card_number_full[-1])
    get_checksum = generate_checksum(without_checksum)
    return actual_checksum == get_checksum


def show_account_data(current_account):
    print("Your card has been created")
    print("Your card number:")
    print(current_account['number'])
    print("Your card PIN:")
    print(current_account['pin'])


class BankingSystem:
    def __init__(self):
        self.conn = sqlite3.connect('card.s3db')
        self.cur = self.conn.cursor()
        self.running = True
        self.menu = {
            '1': 'Create an account',
            '2': 'Log into account',
            '0': 'Exit',
        }
        self.create_table()
        self.account_numbers = []
        self.account_data = {}
        self.is_logged_in = False
        self.logged_in_user = None
        self.show_menu()

    def create_table(self):
        create_table = """CREATE TABLE IF NOT EXISTS card(
            id INT,
            number TEXT,
            pin TEXT,
            balance INTEGER DEFAULT 0
        )"""

        self.cur.execute(create_table)
        self.save_changes()

    def save_changes(self):
        self.conn.commit()

    def add_card(self, card_id, card, pin, balance):
        self.cur.execute(f"INSERT INTO card VALUES({card_id}, {card},{pin}, {balance})")
        self.save_changes()

    def show_menu(self):
        while self.running:
            for x, y in self.menu.items():
                print(f"{x}. {y}")
            self.menu_function()
        else:
            print('Bye!')

    def menu_function(self):
        take_input = abs(int(input()))
        if take_input == 1:
            self.create_account()
        elif take_input == 2:
            self.login()
        else:
            self.running = False

    def create_account(self):
        account_data = self.generate_card()
        show_account_data(account_data)

    def login(self):
        print("Enter your card number:")
        card = input()
        print("Enter your PIN:")
        pin = input()
        pin = int(pin) if pin.isnumeric() else pin

        self.check_login(card, pin)

    def check_login(self, card, pin):
        if not self.verify_login(card, pin):
            print("Wrong card number or PIN!")
        else:
            print("You have successfully logged in!")
            self.is_logged_in = True
            self.logged_in_user = card
            self.show_logged_in()

    def show_logged_in(self):
        if self.is_logged_in:
            menu_log_in = {
                '1': 'Balance',
                '2': 'Add income',
                '3': 'Do transfer',
                '4': 'Close account',
                '5': 'Log out',
                '0': 'Exit',
            }
            while self.is_logged_in:
                for x, y in menu_log_in.items():
                    print(f"{x}. {y}")
                self.log_in_menu_function()

    def log_in_menu_function(self):
        take_input = abs(int(input()))
        do_logout = False
        if take_input == 1:
            account_data = self.get_single_account(self.logged_in_user)
            print(f"Balance: {account_data[-1]}")
        elif take_input == 2:
            # add income
            self.add_income_input()
        elif take_input == 3:
            # transfer
            self.transfer_input()
        elif take_input == 4:
            # close account
            self.del_account()
            self.is_logged_in = False
            self.logged_in_user = None
        elif take_input == 5:
            self.is_logged_in = False
            self.logged_in_user = None
            print("You have successfully logged out!")
        else:
            do_logout = True

        if do_logout:
            self.is_logged_in = False
            self.logged_in_user = None
            self.running = False

    def generate_card(self):
        iin = '400000'
        current_card = self.get_card_id()
        self.account_numbers.append(current_card)
        card_str = str(current_card).zfill(9)
        card_str = f"{iin}{card_str}"
        checksum = generate_checksum(card_str)
        card_number = f"{card_str}{str(checksum)}"
        pin_code = generate_pin()
        balance = 0
        self.add_card(current_card, card_number, pin_code, balance)

        return {
            'id': current_card,
            'number': card_number,
            'pin': pin_code,
            'balance': balance,
        }

    def get_card_id(self):
        self.cur.execute("SELECT MAX(id) FROM card")
        result = self.cur.fetchone()
        return 1 if result[0] is None else result[0] + 1

    def verify_login(self, card, pin):
        self.cur.execute(f"SELECT id FROM card WHERE number = '{card}' AND pin = '{pin}'")
        result = self.cur.fetchone()
        return result is not None

    def get_single_account(self, card):
        self.cur.execute(f"SELECT * FROM card WHERE number = '{card}'")
        result = self.cur.fetchone()
        return result

    def add_income_input(self):
        print("Enter income:")
        income = int(input())
        self.add_income(income)

    def add_income(self, amount):
        if self.is_logged_in and self.logged_in_user and amount > 0:
            income_query = f"UPDATE card set balance = balance + {amount} WHERE number = {self.logged_in_user}"
            self.cur.execute(income_query)
            self.conn.commit()
            print("Income was added!")

    def check_enough_balance(self, amount):
        if self.is_logged_in and self.logged_in_user:
            query = f"SELECT balance >= {amount} FROM card WHERE number = {self.logged_in_user}"
            self.cur.execute(query)
            result = self.cur.fetchone()
            return bool(result[0])
        else:
            return False

    def transfer_input(self):
        print("Transfer")
        print("Enter card number:")
        to_card = input()
        to_card = to_card.strip()
        if not check_algo_sum(to_card):
            print("Probably you made a mistake in the card number. Please try again!")
            return

        if self.get_single_account(to_card) is None:
            print("Such a card does not exist.")
            return

        if to_card == self.logged_in_user.strip():
            print("You can't transfer money to the same account!")
            return

        print("Enter how much money you want to transfer:")
        transfer_amount = int(input())

        if not self.check_enough_balance(transfer_amount):
            print("Not enough money!")
            return

        if self.do_transfer(to_card, transfer_amount):
            print("Success!")
            return

    def do_transfer(self, to_card, amount):
        debit_query = f"UPDATE card set balance = balance - {amount} WHERE number = {self.logged_in_user}"
        credit_query = f"UPDATE card set balance = balance + {amount} WHERE number = {to_card}"
        self.cur.execute(debit_query)
        self.cur.execute(credit_query)
        self.conn.commit()
        return True

    def del_account(self):
        del_query = f"DELETE FROM card WHERE number = {self.logged_in_user}"
        self.cur.execute(del_query)
        self.conn.commit()
        print("The account has been closed!")


bank = BankingSystem()
