from proxyclient import ProxyClient
from threading import Thread
from time import sleep
from datetime import datetime, timedelta
import sqlite3
import coloredlogs, logging
import discord
from discord.ext import tasks
from queue import Queue

coloredlogs.install(level='DEBUG', fmt='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('discord')
logger.setLevel(logging.INFO)

LOGIN = "rtanks_bot"
PASSWORD="rtanks_bot123"
IP = "135.125.188.169"
PORT = 6969

db = sqlite3.connect('rtanks.db', check_same_thread=False)
cursor = db.cursor()

presence_queue = Queue()

# Table online
db.execute('''
CREATE TABLE IF NOT EXISTS online (
    online INT,
    battles INT,
    date   DATETIME
);
''')

# Table users
db.execute('''
CREATE TABLE IF NOT EXISTS users (nickname VARCHAR PRIMARY KEY, last_online DATETIME);
''')


def parse_online():
    con = db.cursor()
    while True:
        client = ProxyClient(IP, PORT)
        try:
            client.handshake()
            is_success = client.auth(LOGIN, PASSWORD)
            if not is_success:
                logging.error("Invalid login/pass")
                exit()
            sleep(10)
            logging.debug("Started parsing")
            battles_info = client.get_battles()
            battles = battles_info["battles"]
            players = []
            for battle in battles:
                battle_info = client.get_battle_info(battle["battleId"])
                for user in battle_info['users_in_battle']:
                    players.append(user["nickname"])
            datetime_now = datetime.now().replace (microsecond=0)
            players = [(player, datetime_now) for player in players]
            con.executemany("REPLACE INTO users VALUES (?, ?)", players)
            con.execute("INSERT INTO online VALUES (?, ?, ?)", (len(players), len(battles), datetime_now))
            db.commit()
            presence_queue.put(len(players))
            logging.debug(f"Parsing ended. Results {len(battles)} / {len(players)}")
        except Exception as e:
            logging.error(e)
        client.disconnect() 
        sleep(300)

def get_last_online():
    cursor.execute('''
        SELECT online
        FROM online
        ORDER BY date DESC
        LIMIT 1
    ''')
    last_online = cursor.fetchone()[0]
    return last_online

def get_average_online_last_n_hours(n):
    current_time = datetime.now()
    start_time = current_time - timedelta(hours=n)
    start_time_str = start_time.strftime('%Y-%m-%d %H:%M:%S')
    current_time_str = current_time.strftime('%Y-%m-%d %H:%M:%S')
    query = '''
        SELECT AVG(online)
        FROM online
        WHERE date >= ? AND date <= ?
    '''
    cursor.execute(query, (start_time_str, current_time_str))
    average_online = cursor.fetchone()[0]
    return int(average_online)

@tasks.loop(seconds=5)
async def update_presence():
    while True:
        online_count = presence_queue.get()
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game(name=f"Online: {online_count}"))

th = Thread(target=parse_online)
th.start()
bot = discord.Bot()

@bot.event
async def on_ready():
    update_presence.start()

@bot.command(description="Get Rtanks online")
async def online(ctx: discord.ApplicationContext):
    last_online = get_last_online()
    last_hour = get_average_online_last_n_hours(1)
    last_half_day = get_average_online_last_n_hours(12)
    last_day = get_average_online_last_n_hours(24)
    await ctx.respond(f"Current online: {last_online}\nLast hour: {last_hour}\nLast 12 hours: {last_half_day}\nLast 24 hours: {last_day}")

bot.run("MTIxNjMzODAwMjIxODA1NzgyOQ.GfnmLP.v0GRYzSp9K8KNbfRcZswVZiXRJG_csrIs6QDmU")

