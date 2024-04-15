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
logging.getLogger('discord').setLevel(logging.INFO)
logging.getLogger('matplotlib').setLevel(logging.CRITICAL)

LOGIN = "warthunder"
PASSWORD="warthunder123"
IP = "135.125.188.169"
PORT = 6969

db = sqlite3.connect('rtanks.db', check_same_thread=False)
cursor = db.cursor()

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

@tasks.loop(seconds=200)
async def parse_online():
    con = db.cursor()
    client = ProxyClient(IP, PORT)
    try:
        client.handshake()
        is_success = client.auth(LOGIN, PASSWORD)
        if not is_success:
            raise Exception("Can't login account")
        sleep(5)
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
        await bot.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game(name=f"Online: {len(players)}"))
        logging.debug(f"Parsing ended. Results {len(battles)} / {len(players)}")
    except Exception as e:
            logging.error(e)
    client.disconnect() 

def plot_online_data(hours_ago = 24, time_freq = '1h'):
    cur = db.cursor()
    now = datetime.now()
    date = now - timedelta(hours=hours_ago)
    cur.execute("SELECT date, online, battles FROM online WHERE date >= ? ORDER BY date", (date,))
    rows = cur.fetchall()
    df = pd.DataFrame(rows, columns=['date', 'online', 'battles'])
    df['date'] = pd.to_datetime(df['date'])
    min_time = df['date'].min().round(freq=time_freq)
    max_time = df['date'].max().round(freq=time_freq)

    plt.plot(df['date'], df['online'], label='Online')
    plt.plot(df['date'], df['battles'], label='Battles')

    plt.xlabel('Time (MSK)')
    plt.ylabel('Online')
    plt.legend()

    plt.yticks(np.arange(0, max(df['online']) + 10, step=10))
    plt.gca().xaxis.set_major_formatter(md.DateFormatter('%H:%M'))
    plt.gca().xaxis.set_tick_params(labelsize=8)
    plt.gca().yaxis.set_tick_params(labelsize=8)

    time_range = pd.date_range(min_time, max_time, freq=time_freq)
    plt.xticks(time_range, rotation=45)
    for time in md.date2num(time_range):
        online = round(np.interp(time, md.date2num(df['date']), df['online'].values))
        plt.text(time, online, str(online), ha='center', va='center', fontsize=7, color='white', bbox=dict(facecolor='black', alpha=0.7, boxstyle='round'))
        battles = round(np.interp(time, md.date2num(df['date']), df['battles'].values))
        plt.text(time, battles, str(battles), ha='center', va='center', fontsize=7, color='white', bbox=dict(facecolor='black', alpha=0.7, boxstyle='round'))
    mplcyberpunk.add_glow_effects()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close('all')
    return buf

bot = discord.Bot()

@bot.event
async def on_ready():
    await parse_online.start()

@bot.command(description="Get player's last online")
async def lastonline(ctx: discord.ApplicationContext,
                     nick: discord.Option(str)):
    cur = db.cursor()
    cur.execute("SELECT last_online FROM users WHERE nickname = ? COLLATE NOCASE", (nick,))
    last_online = cur.fetchone()
    if last_online is None:
        await ctx.send_response(content=f'No data for {nick}')
        return
    last_online = last_online[0]
    last_online = datetime.strptime(last_online, '%Y-%m-%d %H:%M:%S').timestamp()
    last_online = f"<t:{int(last_online)}>"
    await ctx.send_response(content=f'Last online for {nick}: {last_online}')

@bot.command(description="Get total players in database")
async def total(ctx: discord.ApplicationContext):
    cur = db.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()
    print(total)
    if total is None:
        total = 0
    else:
        total = int(total[0])
    await ctx.send_response(content=f'Total players in database: `{total}`')

@bot.command(description="Get Rtanks online")
async def online(ctx: discord.ApplicationContext,
                 time: discord.Option(str, choices=['halfhour', 'hour', '12h', '24h'])):
    if time == "halfhour":
        plot = plot_online_data(0.5, '5min')
    elif time == "hour":
        plot = plot_online_data(1, '15min')
    elif time == '12h':
        plot = plot_online_data(12, '1h')
    else:
        plot = plot_online_data(24, '1h')
    await ctx.send_response(content=f'Online for {time}', file=discord.File(plot, filename='image.png'))

bot.run("MTIxNjMzODAwMjIxODA1NzgyOQ.GfnmLP.v0GRYzSp9K8KNbfRcZswVZiXRJG_csrIs6QDmU")

