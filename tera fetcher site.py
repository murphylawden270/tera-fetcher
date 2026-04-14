import streamlit as st
import re
import requests
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from collections import Counter

st.set_page_config(
    page_title="Tera Fetcher",
    layout="wide"
)

st.title("Tera Fetcher Tool For Usage Stats:")

if "bbcode" not in st.session_state:
    st.session_state.bbcode = ""

links = st.text_area("Enter Replay URL Here...", value=st.session_state.get("links", ""), key="links", height=200)

replay_warn = []
if st.button("Fetch"):
    if links.strip():
        pokemon_tera = {}
        table = []
        lock = Lock()

        header = '''[TABLE width="100%"]
[TR][TD width="33.3333%"]Pokemon[/TD][TD width="10%"]Count[/TD][TD width="33.3333%"]Type[/TD][/TR]'''
        table.append(header)
        final_no_tera = 0
        proccessed_replays = []
        
        tech = requests.Session()
        
        def proccess_replays(replay, retry = 5):
            no_tera = 0

            if replay.strip() == "":
                return

            if not replay.startswith("https://replay"):
                with lock:
                    replay_warn.append(f'{replay} is not a replay! No Tera could be extracted!')
                return None

            if "gen9" not in replay :
                with lock:
                    replay_warn.append(f'{replay} is not a Generation 9 replay! No Tera could be extracted!')
                return None
            
            with lock:
                if replay in proccessed_replays:
                    replay_warn.append(f'Duplicate Replay: {replay}!')
                    return None
                proccessed_replays.append(replay)

            c = None
            for attempt in range(retry):
                try:
                    with requests.Session() as tech:
                        b = tech.get(replay, timeout=10)
                        c = b.text
                    break
                except requests.exceptions.Timeout:
                    if attempt == retry - 1:
                        with lock:
                            replay_warn.append(f'Timeout after {retries} attempts: {replay}!')
                        return None
                except requests.exceptions.RequestException as e:
                    with lock:
                        replay_warn.append(f'Error fetching {replay}! Replay is most likely invalid. Please, recheck the link and try again!')
                    return None
            if "<h1>Not Found</h1>" in c:
                with lock:
                    replay_warn.append(f'Invalid Replay : {replay}! No Tera could be extracted!')
                return None
            else:
                x = re.findall(r'\|-terastallize\|(.*): (.*)', c)
            if len(x) == 1:
                no_tera += 1
            elif len(x) == 0:
                no_tera += 2

            for i in x:
                y = i[1].split("|")
                correct_name = re.findall(rf'\|(?:switch|drag)\|{i[0]}: {re.escape(y[0].strip())}\|([^,|]+)(?:,[^|]*)?\|', c)
                with lock:
                    if correct_name[0] not in pokemon_tera:
                        pokemon_tera[correct_name[0]] = []
                    tera = y[1].strip()
                    pokemon_tera[correct_name[0]].append(tera)
            return no_tera
            
        attempts = links.splitlines()
        n = len(attempts)

        with st.spinner("",show_time=True):
            limit = min(100, n)
            with ThreadPoolExecutor(max_workers=limit) as executor:
                link = list(executor.map(proccess_replays, attempts))

        for i in link:
            if i is not None:
                final_no_tera += i

        sorted_by_tera = sorted(pokemon_tera.keys(), key=lambda k: len(pokemon_tera[k]), reverse=True)
        sorted_table = {k: pokemon_tera[k] for k in sorted_by_tera}

        for key, values in sorted_table.items():
            type_count = Counter(values)
            each_mon = ", ".join([f"{t} ({c})" for t, c in type_count.items()])
            h1 = f'[TR][TD width="33.3333%"]:{key}:{key}[/TD][TD width="10%"]{len(values)}[/TD][TD width="33.3333%"]{each_mon}[/TD][/TR]'
            table.append(h1)
        table.append(f'[TR][TD width="33.3333%"]No Tera[/TD][TD width="10%"]{final_no_tera}[/TD][TD width="33.3333%"][/TD][/TR]')
        table.append("[/TABLE]")

        st.session_state.bbcode = "\n".join(table)
    
if replay_warn:
    st.code("\n".join(replay_warn))

st.caption("BB Code:")
st.code(st.session_state.bbcode, language=None, height=300)
