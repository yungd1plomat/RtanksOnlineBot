import string
import secrets

def get_battle_max(user_info, battles_data):
    current_rank = user_info["rank"]
    max_count = -1
    battle = None
    for battle in battles_data["battles"]:
        if current_rank < battle["minRank"] or current_rank > battle["maxRank"]:
            continue
        count = battle["redPeople"] + battle["bluePeople"] + battle["countPeople"]
        if count > max_count and battle["maxPeople"] < count:
            count = max_count
            battle = battle
    return battle

def battles_to_count(user_info, battles_data):
    current_rank = user_info["rank"]
    battles = {}
    for battle in battles_data["battles"]:
        if current_rank < battle["minRank"] or current_rank > battle["maxRank"]:
            continue
        count = battle["redPeople"] + battle["bluePeople"] + battle["countPeople"]
        battle_count = {
            battle,
            count,
        }
        battles.append(battle_count)

def read_file(filename):
    with open(filename, encoding='utf-8') as file:
        lines = [line.rstrip('\n') for line in file]
        return lines
    
def write_lines(filename, lines):
    with open(filename, 'w', encoding='utf-8') as file:
        for line in lines:
            file.write(f"{line}\n")

def write_file(filename, content, append = False):
    mode = 'a' if append else 'w'
    with open(filename, mode, encoding='utf-8') as file:
        file.write(content)

def random_string(size):        
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits            
    return ''.join(secrets.choice(letters) for i in range(size))
