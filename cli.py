import asyncio
import sys
import json
import shlex
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
import random

# --- ここで全ての設定を管理する ---
# ◆絶対にファイルの名前変更するな
TOKENS = [
    # ★★★★★ お前のトークンをここに入れろ ★★★★★
    #複数のトークンは"",で囲む、以下の通り

"◆変更-TOKEN",
"◆変更-TOKEN2",
]
PROXIES = []
COMMAND_PREFIX = '!'
AUDIO_SOURCE_FILE = "loud_sound.mp3"
VERBOSE_LOGGING = True
SETTINGS = {
    "spam_delay": 0.1,
    "actions_per_second": 0
}
# ------------------------------------

CONFIG = {
    "TOKENS": TOKENS, "PROXIES": PROXIES, "COMMAND_PREFIX": COMMAND_PREFIX,
    "AUDIO_SOURCE_FILE": AUDIO_SOURCE_FILE, "VERBOSE_LOGGING": VERBOSE_LOGGING,
    "SETTINGS": SETTINGS
}

# --- コマンドの分類 ---
# サーバー(Guild)コンテキストを必要とするコマンド
GUILD_COMMANDS = [
    'nuke', 'colonize', 'purge', 'secure', 'sync_world', 'anti_raid_lockdown',
    'nuke_infinite', 'deleter', 'vcraid', 'vcstop', 'ban', 'kick', 'admin_all',
    'nick_cycle', 'ghostping', 'scrape_users', 'stealth_admin', 'backdoor',
    'extract_invites', 'clog_invites'
]
# グローバル（サーバーに依存しない）コマンド
GLOBAL_COMMANDS = ['dmspam', 'dmstop', 'psyop', 'legion_invite']


async def read_bot_output(stream):
    while True:
        line = await stream.readline()
        if not line: break
        print(line.decode().strip())

async def main():
    config_json = json.dumps(CONFIG)
    process = await asyncio.create_subprocess_exec(
        sys.executable, 'main.py', config_json,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    asyncio.create_task(read_bot_output(process.stdout))
    asyncio.create_task(read_bot_output(process.stderr))
    
    session = PromptSession(history=FileHistory('.hydra_history'))
    print("--- Hydra Universal Command Interface Initialized ---")
    print("Type 'help' for a list of commands.")

    while True:
        try:
            user_input = await session.prompt_async('admin@hydra > ', auto_suggest=AutoSuggestFromHistory())
            if not user_input: continue
            try: parts = shlex.split(user_input)
            except ValueError: print("Error: Mismatched quotes."); continue
            
            command = parts[0].lower()
            args = parts[1:]

            if command == "exit":
                print("Shutting down..."); process.terminate(); await process.wait(); break
            elif command == "help":
                print("--- CLI Commands ---\n  <command> <args...> - Execute any bot command via CLI.\n  e.g., purge <guild_id>\n  e.g., psyop <user_id> <message>\n  setting <parameter> <value> / show\n  exit")
            elif command == "setting":
                if len(args) == 0 or args[0] == 'show':
                    print(f"Current Settings: {CONFIG['SETTINGS']}")
                elif len(args) < 2:
                    print("Usage: setting <param> <value>")
                else:
                    # settingは特別扱い
                    command_data = {"command": command, "args": args}
                    json_data = json.dumps(command_data) + '\n'
                    process.stdin.write(json_data.encode()); await process.stdin.drain()
            else:
                # --- Universal Command Handler ---
                command_data = {"command": "invoke", "command_name": command, "args": args}
                json_data = json.dumps(command_data) + '\n'
                process.stdin.write(json_data.encode()); await process.stdin.drain()

        except (EOFError, KeyboardInterrupt):
            print("\nShutting down..."); process.terminate(); await process.wait(); break
        except Exception as e:
            print(f"CLI Error: {e}")

if __name__ == "__main__":
    # main.pyに渡すために、configからコマンドリストを削除
    if "GUILD_COMMANDS" in CONFIG: del CONFIG["GUILD_COMMANDS"]
    if "GLOBAL_COMMANDS" in CONFIG: del CONFIG["GLOBAL_COMMANDS"]
    asyncio.run(main())
