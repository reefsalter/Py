import tkinter as tk
from tkinter import ttk

from datetime import datetime, timezone

import json
import os.path
import requests

import locale
locale.setlocale(locale.LC_ALL, '')  # Use '' for auto, or force e.g. to 'en_US.UTF-8'

TRADER_FILE = 'traders.json'

CLAIM_USER = 'f"https://api.spacetraders.io/users/{username}/claim"'
MY_ACCOUNT = 'https://api.spacetraders.io/my/account'
CURRENT_LEADERBOARD = 'https://api.spacetraders.io/game/leaderboard/net-worth'
MY_LOANS = 'https://api.spacetraders.io/my/loans'
MY_SHIPS = 'https://api.spacetraders.io/my/ships'
MY_STRUCTURES = 'https://api.spacetraders.io/my/structures'
GAME_LIVE = 'https://api.spacetraders.io/game/status'
MY_LOANS = "https://api.spacetraders.io/my/loans"
AVAILABLE_LOANS = "https://api.spacetraders.io/types/loans"
PAY_OFF_LOAN = 'f"https://api.spacetraders.io/my/loans/{loanId}"'

UTC_FORMAT = '%Y-%m-%dT%H:%M:%S.%f%z'
DISPLAY_FORMAT = ' %B, %Y'

proxies = { 'http' : None, 'https' : None }


def parse_datetime(dt):
    return datetime.strptime(dt, UTC_FORMAT)


def format_datetime(dt_text):
    dt = parse_datetime(dt_text)
    d = dt.day
    return str(d) + ('th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')) + datetime.strftime(dt, DISPLAY_FORMAT)


def load_trader_logins():
    known_traders = {}

    if os.path.exists(TRADER_FILE):
        with open(TRADER_FILE) as json_traders:
            known_traders = json.load(json_traders)

    return known_traders


def store_trader_login(json_result):
    known_traders = load_trader_logins()
    known_traders[json_result['user']['username']] = json_result['token']

    with open(TRADER_FILE, 'w') as json_traders:
        json.dump(known_traders, json_traders)


def generate_login_combobox():
    known_traders = load_trader_logins()
    trader_list = sorted(known_traders.keys(), key=str.casefold)
    id_login['values'] = trader_list


def show_trader_summary(json_result):
    tabs.tab(0, state=tk.DISABLED)
    tabs.tab(1, state=tk.NORMAL)
    tabs.tab(2, state=tk.NORMAL)
    tabs.tab(3, state=tk.NORMAL)
    tabs.tab(4, state=tk.NORMAL)
    
    trader_login.set(json_result['user']['username'])
    trader_token.set(json_result['token'])

    user_joined.set(format_datetime(json_result['user']['joinedAt']))
    user_worth.set(f"{json_result['user']['credits']:n}")

    tabs.select(1)


def register_trader():
    username = trader_name.get()
    claim_url = eval(CLAIM_USER)
    try:
        response = requests.post(claim_url, proxies=proxies)
        if response.status_code < 400:
            result = response.json()
            result['user']['joinedAt'] = datetime.now(timezone.utc).isoformat()
            store_trader_login(result)
            show_trader_summary(result)
            trader_name.set('')
        else:
            print('Failed:', response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        print('Failed:', ce)


def login_trader():
    trader_token.set(trader_login.get())

    # -1 -> user entered a new token, so there won't be a name selected
    if id_login.current() != -1:
        known_traders = load_trader_logins()
        trader_token.set(known_traders[trader_login.get()])

    try:
        response = requests.get(MY_ACCOUNT, params={'token': trader_token.get()}, proxies=proxies)
        if response.status_code == 200:
            result = response.json()
            result['token'] = trader_token.get() # used to hold the token for later
            show_trader_summary(result)
            # print(result)

            # -1, so now store the trader name / token for future runs
            if id_login.current() == -1:
                store_trader_login(result)

        else:
            print('Failed:', response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        print('Failed:', ce)


def logout_trader():
    tabs.tab(0, state=tk.NORMAL)
    tabs.tab(1, state=tk.DISABLED)
    tabs.tab(2, state=tk.DISABLED)
    tabs.tab(3, state=tk.DISABLED)
    tabs.tab(4, state=tk.DISABLED)
    
    trader_login.set('')
    trader_token.set('')
    
    tabs.select(0)


def refresh_tabs(event):
    selected_index = tabs.index(tabs.select())
    if selected_index == 1:
        refresh_user_summary()
        
    elif selected_index == 2:
        refresh_leaderboard()
    elif selected_index == 3:
        refresh_loans()
    elif selected_index == 4:
        logout_trader()


def refresh_user_summary(*args):
    try:
        response = requests.get(MY_ACCOUNT, params={'token': trader_token.get()}, proxies=proxies)
        if response.status_code == 200:
            result = response.json()
            # print(result)

            user_joined.set(format_datetime(result['user']['joinedAt']))
            user_worth.set(f"{result['user']['credits']:n}")

        response = requests.get(MY_LOANS, params={'token': trader_token.get()}, proxies=proxies)
        if response.status_code == 200:
            result = response.json()
            # print(result)
            loan_view.delete(*loan_view.get_children())
            loan_view.heading('#1', text='Type')
            loan_view.heading('#2', text='Status')
            loan_view.heading('#3', text='Due')
            loan_view.heading('#4', text='Amount Owing')
            for row in result['loans']:
                loan_view.insert('', 'end', text='loan_values', values=(row['type'], row['status'], format_datetime(row['due']), f"{row['repaymentAmount']:n}"))

        else:
            print('Failed:', response.status_code, response.reason, response.text)

        response = requests.get(MY_SHIPS, params={'token': trader_token.get()}, proxies=proxies)
        if response.status_code == 200:
            result = response.json()
            # print(result)
            ship_view.delete(*ship_view.get_children())
            ship_view.heading('#1', text='Manufacturer')
            ship_view.heading('#2', text='Class')
            ship_view.heading('#3', text='Type')
            ship_view.heading('#4', text='Location')
            for row in result['ships']:
                ship_view.insert('', 'end', text='ship_values', values=(row['manufacturer'], row['class'], row['type'], row['location'] if 'location' in row else 'In transit'))

        else:
            print('Failed:', response.status_code, response.reason, response.text)

        response = requests.get(MY_STRUCTURES, params={'token': trader_token.get()}, proxies=proxies)
        if response.status_code == 200:
            result = response.json()
            # print(result)
            structure_view.delete(*structure_view.get_children())
            structure_view.heading('#1', text='Type')
            structure_view.heading('#2', text='Location')
            structure_view.heading('#3', text='Active')
            structure_view.heading('#4', text='Status')
            for row in result['structures']:
                structure_view.insert('', 'end', text='structure_values', values=(row['type'], row['location'], row['active'], row['status']))

        else:
            print('Failed:', response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        print('Failed:', ce)


def refresh_leaderboard(*args):
    try:
        response = requests.get(CURRENT_LEADERBOARD, params={'token': trader_token.get()}, proxies=proxies)
        if response.status_code == 200:
            result = response.json()
            
            # print(result)
            leaderboard_view.delete(*leaderboard_view.get_children())
            leaderboard_view.heading('#1', text='Rank')
            leaderboard_view.heading('#2', text='Trader')
            leaderboard_view.heading('#3', text='Net Worth')
            for row in result['netWorth']:
                leaderboard_view.insert('', 'end', text='values', values=(row['rank'], row['username'], f"{row['netWorth']:n}"))
            if result["userNetWorth"]["rank"] > 10:
                leaderboard_view.insert('', 'end', text='values', values=(result["userNetWorth"]['rank'], result["userNetWorth"]['username'], f"{result['userNetWorth']['netWorth']:n}"))

        else:
            print('Failed:', response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        print('Failed:', ce)

def take_out_loan(*args):
    response = requests.post(MY_LOANS,params={"token": trader_token.get(), "type": "STARTUP"})

    if response.status_code == 422:
        print(response.json()["error"]["message"])

def pay_off_loan(*args):
    result = requests.get(MY_LOANS, params={"token": trader_token.get()})
    try:
        loanId = result.json()["loans"][0]["id"]

        pay_loan = eval(PAY_OFF_LOAN)

        response = requests.put(
            pay_loan, params={"token": trader_token.get(), "loanId": loanId}
        )

        if response.status_code == 400:
            print(response.json()["error"]["message"])

    except IndexError:
        print("You dont have any loans to pay off.")

def refresh_loans(*args):
    try:
        response = requests.get(
            AVAILABLE_LOANS, params={"token": trader_token.get()})
        if response.status_code == 200:
            result = response.json()
            available_loans_view.delete(*available_loans_view.get_children())
            available_loans_view.heading('#1', text='Type')
            available_loans_view.heading('#2', text='Days')
            available_loans_view.heading('#3', text='Rate')
            available_loans_view.heading('#4', text='Amount')
            for row in result["loans"]:
                available_loans_view.insert('', 'end', text='values',values=(row["type"], row["termInDays"], row["rate"], row["amount"]))

        response = requests.get(MY_LOANS, params={"token": trader_token.get()})
        if response.status_code == 200:
            result = response.json()
            current_loans_view.delete(*current_loans_view.get_children())
            current_loans_view.heading('#1', text='Type')
            current_loans_view.heading('#2', text='Status')
            current_loans_view.heading('#3', text='Due')
            current_loans_view.heading('#4', text='Amount')
            for row in result["loans"]:
                current_loans_view.insert('', 'end', text='values', values=(row['type'], row['status'], format_datetime(row['due']), f"{row['repaymentAmount']:n}"))
        else:
            print('Failed:', response.status_code, response.reason, response.text)

    except ConnectionError as ce:
        print('Failed:', ce)

def check_game_online():
    try:
        response = requests.get(GAME_LIVE)
        if response.status_code == 200:
            # Parse the response JSON
            game_status = response.json().get("status", "")
            # print("Game status:", game_status)

            # Check if the game status indicates it's online
            if "available" in game_status.lower():
                # Game is online
                show_emoji("🟢")
            else:
                # Game is offline
                show_emoji("🔴")
        else:
            # Game is offline
            show_emoji("🔴")
    except ConnectionError as ce:
        print('Failed:', ce)
def show_emoji(emoji):
    emoji_label.config(text='Game Status: ' + emoji)

###
# Root window, with app title
#
root = tk.Tk()
root.title("Io Space Trading")

# Main themed frame, for all other widgets to rest upon
main = ttk.Frame(root, padding='3 3 12 12')
main.grid(sticky=tk.NSEW)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Tabbed widget for rest of the app to run in
tabs = ttk.Notebook(main)
tabs.grid(sticky=tk.NSEW)
tabs.bind('<<NotebookTabChanged>>', refresh_tabs)

main.columnconfigure(0, weight=1)
main.rowconfigure(0, weight=1)

# setup the three main tabs
user = ttk.Frame(tabs)
summary = ttk.Frame(tabs)
leaderboard = ttk.Frame(tabs)
loans = ttk.Frame(tabs)
Logout = ttk.Frame(tabs)

tabs.add(user, text='User')
tabs.add(summary, text='Summary')
tabs.add(leaderboard, text='Leaderboard')
tabs.add(loans, text='Loans')
tabs.add(Logout, text='Logout')

tabs.tab(1, state=tk.DISABLED)
tabs.tab(2, state=tk.DISABLED)
tabs.tab(3, state=tk.DISABLED)
tabs.tab(4, state=tk.DISABLED)

###
# user registration/login tab
#

user_frame = ttk.Frame(user)
user_frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW)

# left hand frame will check/register new users and return/store the UUID
register = ttk.LabelFrame(user_frame, text='Register', relief='groove', padding=5)
register.grid(sticky=tk.NSEW)

# widgets required on the left are a label, an entry, and a button
trader_name = tk.StringVar()
ttk.Label(register, text='Enter a new trader name\nto start a new account', anchor=tk.CENTER).grid(sticky=tk.EW)
ttk.Entry(register, textvariable=trader_name).grid(row=1, column=0, sticky=tk.EW)
ttk.Button(register, text='Register new trader', command=register_trader).grid(row=2, column=0, columnspan=2, sticky=tk.EW)

register.columnconfigure(0, weight=1)
register.rowconfigure(0, weight=1)

ttk.Label(user_frame, text='or', padding=10, anchor=tk.CENTER).grid(row=0, column=1, sticky=tk.EW)

# right hand frame will allow to choose from known users and/or paste in existing
# UUID to login and play as that user
login = ttk.LabelFrame(user_frame, text='Login', relief=tk.GROOVE, padding=5)
login.grid(row=0, column=2, sticky=tk.NSEW)

# widgets required on the right are a dropdown, and a button
trader_login = tk.StringVar()
trader_token = tk.StringVar() # going to use this to remember the currently logged in trader
ttk.Label(login, text='Choose the trader to play as\nor paste an existing id').grid(sticky=tk.EW)
id_login = ttk.Combobox(login, textvariable=trader_login, postcommand=generate_login_combobox)
id_login.grid(row=1, column=0, sticky=tk.EW)
ttk.Button(login, text='Login trader', command=login_trader).grid(row=2, column=0, columnspan=2, sticky=tk.EW)

# Define frame for game status
game_status_frame = ttk.Frame(user_frame, padding=5)
game_status_frame.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW)

# Define emoji label inside game status frame
emoji_label = tk.Label(game_status_frame, text='Game Status: 🔴', font=("Segoe UI Emoji", 20))
emoji_label.grid(row=0, column=0, sticky=tk.EW)

login.columnconfigure(0, weight=1)
login.rowconfigure(0, weight=1)

user_frame.columnconfigure(0, weight=1)
user_frame.columnconfigure(2, weight=1)
user_frame.rowconfigure(0, weight=1)

user.columnconfigure(0, weight=1)
user.rowconfigure(0, weight=1)

###
# summary tab
#

user_summary = ttk.LabelFrame(summary, text='Trader', relief=tk.GROOVE, padding=5)

user_joined = tk.StringVar()
user_worth = tk.StringVar()

ttk.Label(user_summary, textvariable=trader_login, anchor=tk.CENTER).grid(columnspan=2, sticky=tk.EW)
ttk.Label(user_summary, text='Joined on:').grid(row=1, column=0, sticky=tk.W)
ttk.Label(user_summary, textvariable=user_joined, anchor=tk.CENTER).grid(row=1, column=1, sticky=tk.EW)
ttk.Label(user_summary, text='Credits:').grid(row=2, column=0, sticky=tk.W)
ttk.Label(user_summary, textvariable=user_worth, anchor=tk.CENTER).grid(row=2, column=1, sticky=tk.EW)
ttk.Button(user_summary, text='Logout', command=logout_trader).grid(row=3, column=0, columnspan=2, sticky=tk.EW)

user_summary.columnconfigure(0, weight=1)

loan_summary = ttk.LabelFrame(summary, text='Loans', relief=tk.GROOVE, padding=5)
loan_view = ttk.Treeview(loan_summary, height=3, columns=('Type', 'Status', 'Due', 'Amount'), show='headings')
loan_view.column('Type', anchor=tk.W, width=20)
loan_view.column('Status', anchor=tk.W, width=20)
loan_view.column('Due', anchor=tk.W, width=20)
loan_view.column('Amount', anchor=tk.E, width=30)
loan_view.grid(sticky=tk.NSEW)
loan_scroll = ttk.Scrollbar(loan_summary, orient=tk.VERTICAL, command=loan_view.yview)
loan_scroll.grid(column=1, row=0, sticky=tk.NS)
loan_view['yscrollcommand'] = loan_scroll.set

loan_summary.columnconfigure(0, weight=1)
loan_summary.rowconfigure(0, weight=1)

ship_summary = ttk.LabelFrame(summary, text='Ships', relief=tk.GROOVE, padding=5)
ship_view = ttk.Treeview(ship_summary, height=3, columns=('Manufacturer', 'Class', 'Type', 'Location'), show='headings')
ship_view.column('Manufacturer', anchor=tk.W, width=30)
ship_view.column('Class', anchor=tk.W, width=30)
ship_view.column('Type', anchor=tk.W, width=30)
ship_view.column('Location', anchor=tk.W, width=30)
ship_view.grid(sticky=tk.NSEW)
ship_scroll = ttk.Scrollbar(ship_summary, orient=tk.VERTICAL, command=ship_view.yview)
ship_scroll.grid(column=1, row=0, sticky=tk.NS)
ship_view['yscrollcommand'] = ship_scroll.set

ship_summary.columnconfigure(0, weight=1)
ship_summary.rowconfigure(0, weight=1)

structure_summary = ttk.LabelFrame(summary, text='Structures', relief=tk.GROOVE, padding=5)
structure_view = ttk.Treeview(structure_summary, height=3, columns=('Type', 'Location', 'Active', 'Status'), show='headings')
structure_view.column('Type', anchor=tk.W, width=20)
structure_view.column('Location', anchor=tk.W, width=20)
structure_view.column('Active', anchor=tk.W, width=20)
structure_view.column('Status', anchor=tk.W, width=60)
structure_view.grid(sticky=tk.NSEW)
structure_scroll = ttk.Scrollbar(structure_summary, orient=tk.VERTICAL, command=structure_view.yview)
structure_scroll.grid(column=1, row=0, sticky=tk.NS)
structure_view['yscrollcommand'] = structure_scroll.set

structure_summary.columnconfigure(0, weight=1)
structure_summary.rowconfigure(0, weight=1)

user_summary.grid(row=0, column=0, sticky=tk.NSEW)
loan_summary.grid(row=0, column=1, sticky=tk.NSEW)
ship_summary.grid(row=1, column=0, sticky=tk.NSEW)
structure_summary.grid(row=1, column=1, sticky=tk.NSEW)

summary.columnconfigure(0, weight=1)
summary.columnconfigure(1, weight=1)
summary.rowconfigure(0, weight=1)
summary.rowconfigure(1, weight=1)

###
# leaderboard tab
#

leaderboard_view = ttk.Treeview(leaderboard, height=6, columns=('Rank', 'Trader', 'Net Worth'), show='headings')
leaderboard_view.column('Rank', anchor=tk.CENTER, width=10)
leaderboard_view.column('Trader', anchor=tk.W, width=100)
leaderboard_view.column('Net Worth', anchor=tk.E, width=100)
leaderboard_view.grid(sticky=tk.NSEW)
leaderboard_scroll = ttk.Scrollbar(leaderboard, orient=tk.VERTICAL, command=leaderboard_view.yview)
leaderboard_scroll.grid(column=1, row=0, sticky=tk.NS)
leaderboard_view['yscrollcommand'] = leaderboard_scroll.set
refresh = ttk.Button(leaderboard, text='Refresh', command=refresh_leaderboard)
refresh.grid(column=0, row=1, sticky=tk.EW)

leaderboard.columnconfigure(0, weight=1)
leaderboard.rowconfigure(0, weight=1)

###
# loans tab
#

availableLoansFrame = ttk.LabelFrame(loans, text="Available Loans", padding="3")
availableLoansFrame.grid(row=0, column=0, sticky=tk.NSEW, padx=5, pady=5)
availableLoansFrame.columnconfigure(0, weight=1)
availableLoansFrame.rowconfigure(0, weight=1)

# Treeview for Available Loans
available_loans_view = ttk.Treeview(availableLoansFrame, height=6, columns=('Type', 'Days', 'Rate', 'Amount'), show='headings')
available_loans_view.column('Type', anchor=tk.CENTER, width=100)
available_loans_view.column('Days', anchor=tk.CENTER, width=100)
available_loans_view.column('Rate', anchor=tk.CENTER, width=100)
available_loans_view.column('Amount', anchor=tk.E, width=100)
available_loans_view.grid(sticky=tk.NSEW)

# Scrollbar for Available Loans Treeview
available_loans_scroll = ttk.Scrollbar(availableLoansFrame, orient=tk.VERTICAL, command=available_loans_view.yview)
available_loans_scroll.grid(column=1, row=0, sticky=tk.NS)
available_loans_view['yscrollcommand'] = available_loans_scroll.set

take_out_loan_button = ttk.Button(availableLoansFrame, text='Take Out Loan', command=take_out_loan)
# command=take_out_loan
take_out_loan_button.grid(column=0, row=1, sticky=tk.EW, pady=5)

# Current Loans Frame setup
currentLoansFrame = ttk.LabelFrame(loans, text="Current Loans", padding="3")
currentLoansFrame.grid(row=0, column=1, sticky=tk.NSEW, padx=5, pady=5)
currentLoansFrame.columnconfigure(0, weight=1)
currentLoansFrame.rowconfigure(0, weight=1)

# Treeview for Current Loans
current_loans_view = ttk.Treeview(currentLoansFrame, height=6, columns=('Type', 'Status', 'Due', 'Amount'), show='headings')
current_loans_view.column('Type', anchor=tk.CENTER, width=100)
current_loans_view.column('Status', anchor=tk.W, width=100)
current_loans_view.column('Due', anchor=tk.E, width=100)
current_loans_view.column('Amount', anchor=tk.E, width=100)
current_loans_view.grid(sticky=tk.NSEW)

# Scrollbar for Current Loans Treeview
current_loans_scroll = ttk.Scrollbar(currentLoansFrame, orient=tk.VERTICAL, command=current_loans_view.yview)
current_loans_scroll.grid(column=1, row=0, sticky=tk.NS)
current_loans_view['yscrollcommand'] = current_loans_scroll.set

pay_off_loan_button = ttk.Button(currentLoansFrame, text='Pay Out Loan', command=pay_off_loan)
# , command=pay_off_loan
pay_off_loan_button.grid(column=0, row=1, sticky=tk.EW, pady=5)

# Refresh button for the entire tab
refresh_button = ttk.Button(loans, text='Refresh', command=refresh_loans)
#  command=refresh_loans
refresh_button.grid(column=0, row=1, columnspan=2, sticky=tk.EW, pady=5)

# Configuring the layout
loans.columnconfigure([0, 1], weight=1)
loans.rowconfigure(0, weight=1)

root.after(1000, check_game_online)
root.mainloop()
