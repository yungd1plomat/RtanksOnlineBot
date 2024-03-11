from proxyclient import ProxyClient
from threading import Thread
from time import sleep
from datetime import datetime, timedelta
import sqlite3
import coloredlogs, logging
import discord
from discord.ext import tasks
from queue import Queue
import matplotlib.pyplot as plt
import mplcyberpunk
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.dates as md
import numpy as np
import io

plt.style.use('cyberpunk')

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

def plot_online_data(hours_ago = 24, time_freq = '1h'):
    cur = db.cursor()
    now = datetime.now()
    date = now - timedelta(hours=hours_ago)
    cur.execute("SELECT date, online FROM online WHERE date >= ? ORDER BY date", (date,))
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=['date', 'online'])
    df['date'] = pd.to_datetime(df['date'])
    min_time = df['date'].min().round(freq=time_freq)
    max_time = df['date'].max().round(freq=time_freq)
    plt.plot(df['date'], df['online'])
    plt.xlabel('Time (MSK)')
    plt.ylabel('Online')

    plt.yticks(np.arange(0, max(df['online']) + 10, step=10))
    plt.gca().xaxis.set_major_formatter(md.DateFormatter('%H:%M'))

    time_range = pd.date_range(min_time, max_time, freq=time_freq)
    plt.xticks(time_range, rotation=45)
    for time in md.date2num(time_range):
        online = round(np.interp(time, md.date2num(df['date']), df['online'].values))
        plt.text(time, online, str(online), ha='center', va='center', fontsize=7, color='white', bbox=dict(facecolor='black', alpha=0.7, boxstyle='round'))
    mplcyberpunk.add_glow_effects()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

@tasks.loop(seconds=5)
async def update_presence():
    try:
        online_count = presence_queue.get(timeout=1)
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game(name=f"Online: {online_count}"))
    except:
        pass

th = Thread(target=parse_online)
th.start()
bot = discord.Bot()

@bot.event
async def on_ready():
    await update_presence.start()

@bot.command(description="Get Rtanks online")
async def online(ctx: discord.ApplicationContext,
                 time: discord.Option(str, choices=['halfhour', 'hour', 'halfday', 'day'])):
    if time == "halfhour":
        plot = plot_online_data(0.5, '5min')
    elif time == "hour":
        plot = plot_online_data(1, '15min')
    elif time == 'halfday':
        plot = plot_online_data(12, '1h')
    else:
        plot = plot_online_data(24, '1h')
    await ctx.send(content=f'Online for {time}', file=discord.File(plot, filename='image.png'))


bot.run("MTIxNjMzODAwMjIxODA1NzgyOQ.GfnmLP.v0GRYzSp9K8KNbfRcZswVZiXRJG_csrIs6QDmU")

