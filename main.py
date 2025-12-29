import discord
from discord.ext import commands
import asyncio
import sys
import json
import random
import shlex
import traceback # エラー追跡用
from commands import CommandsCog

# --- グローバル変数 ---
bots = []
SETTINGS = {}
COMMAND_PREFIX = '!'
TOKENS = []
PROXIES = []
VERBOSE_LOGGING = False

class Colors:
    HEADER, BLUE, CYAN, GREEN, WARNING, FAIL, ENDC, BOLD, YELLOW = '\033[95m', '\033[94m', '\033[96m', '\033[92m', '\033[93m', '\033[91m', '\033[0m', '\033[1m', '\033[93m'

def log(tag, message, color=Colors.ENDC, force=False):
    if VERBOSE_LOGGING or force:
        # flush=Trueを追加して即時出力を保証
        print(f"{color}[{tag}] {message}{Colors.ENDC}", file=sys.stderr, flush=True)

class HydraBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.legion = []
        self.active_tasks = {}
        self.last_retry_after = 5.0
        self.pause_event = kwargs.get('pause_event')
        self.pause_lock = kwargs.get('pause_lock')
        self.nuke_lock = kwargs.get('nuke_lock')

    async def setup_hook(self):
        async def initiate_manual_override_in_bot():
            async with self.pause_lock:
                if self.pause_event.is_set():
                    log("RATE-LIMIT", "IP BAN DETECTED! Pausing all operations...", Colors.FAIL, force=True)
                    self.pause_event.clear()
                    log("SYSTEM", f"Waiting for {self.last_retry_after:.2f}s...", Colors.YELLOW, force=True)
                    await asyncio.sleep(self.last_retry_after + 2.0)
                    log("SYSTEM", "Resuming...", Colors.GREEN, force=True)
                    self.pause_event.set()
        await self.add_cog(CommandsCog(self, SETTINGS, log, Colors, initiate_manual_override_in_bot))

    async def on_ready(self):
        proxy_msg = f" [Proxy: {self.proxy_url}]" if self.proxy_url else " [Direct]"
        log("HYDRA", f"HEAD {self.user} READY{proxy_msg}", Colors.GREEN, force=True)

def create_bot(token, proxy_url=None, pause_event=None, pause_lock=None, nuke_lock=None):
    intents = discord.Intents.all()
    bot = HydraBot(
        command_prefix=COMMAND_PREFIX,
        intents=intents,
        help_command=None,
        proxy=proxy_url,
        pause_event=pause_event,
        pause_lock=pause_lock,
        nuke_lock=nuke_lock
    )
    bot.token = token
    bot.proxy_url = proxy_url
    return bot

async def handle_cli_command(command_data):
    # ★★★ 全体をtry-exceptで囲み、クラッシュを防ぐ ★★★
    try:
        global SETTINGS
        command = command_data.get("command")
        
        if command == "setting":
            args = command_data.get("args", [])
            if len(args) >= 2:
                param, value = args[0], args[1]
                if param in SETTINGS:
                    try: SETTINGS[param] = type(SETTINGS[param])(float(value)); log("CORE", f"Setting '{param}' updated to '{value}'.", Colors.GREEN, force=True)
                    except: log("CORE-ERROR", "Invalid value type.", Colors.FAIL, force=True)
            return

        if command == "invoke":
            command_name = command_data.get("command_name")
            args = command_data.get("args", [])
            
            ready_bots = [b for b in bots if b.is_ready()]
            if not ready_bots: log("CORE-ERROR", "No bots are ready.", Colors.FAIL, force=True); return

            commander = None
            guild = None
            
            cog_instance = ready_bots[0].cogs.get('CommandsCog')
            if not cog_instance: log("CORE-ERROR", "CommandsCog not loaded.", Colors.FAIL, force=True); return

            # コマンド判定と司令官選出
            if command_name in cog_instance.GUILD_COMMANDS:
                if not args: log("CORE-ERROR", f"Command '{command_name}' requires Guild ID.", Colors.FAIL, force=True); return
                try: guild_id = int(args[0])
                except ValueError: log("CORE-ERROR", "Guild ID must be a number.", Colors.FAIL, force=True); return
                
                for bot in ready_bots:
                    g = bot.get_guild(guild_id)
                    if g: commander, guild = bot, g; break
                
                if not commander:
                    log("CORE-ERROR", f"No bot found in guild ID {guild_id}.", Colors.FAIL, force=True)
                    return
                command_args = args[1:]
            else:
                commander = random.choice(ready_bots)
                command_args = args

            target_command = commander.get_command(command_name)
            if not target_command: log("CORE-ERROR", f"Command '{command_name}' not found.", Colors.FAIL, force=True); return

            # --- 擬似コンテキスト作成 & 強制注入 ---
            # 引数を文字列に戻す（クォート処理付き）
            arg_str = ' '.join(shlex.quote(str(a)) for a in command_args)
            message_content = f"{COMMAND_PREFIX}{command_name} {arg_str}".strip()

            # ★ 修正: Bot自身にDMを送れない問題を解決するラッパー ★
            class DummyAuthor:
                def __init__(self, user):
                    self._user = user
                
                async def send(self, content=None, file=None, embed=None, **kwargs):
                    # DM送信の代わりにコンソールにログ出力する
                    if content:
                        log("CLI-OUTPUT", f">> {content}", Colors.GREEN, force=True)
                    if file:
                        log("CLI-OUTPUT", f">> File generated: {file.filename} (Saved in bot directory)", Colors.GREEN, force=True)
                    if embed:
                        desc = embed.description if embed.description else "No description"
                        log("CLI-OUTPUT", f">> Embed: {embed.title} / {desc}", Colors.GREEN, force=True)

                def __getattr__(self, name):
                    return getattr(self._user, name)

                @property
                def id(self): return self._user.id
                
                @property
                def mention(self): return self._user.mention

            class DummyMessage:
                def __init__(self):
                    self.id = 0
                    self.content = message_content
                    self.guild = guild
                    self.channel = guild.text_channels[0] if guild and guild.text_channels else None
                    self.author = DummyAuthor(commander.user) # ★ ラッパーを使用
                    self._state = commander._connection
                    self.mentions = []
                    self.mention_everyone = False
                    self.attachments = [] # ★ 前回の修正も維持
                async def delete(self): pass

            ctx = await commander.get_context(DummyMessage())
            
            # 強制執行パッチ
            if not ctx.valid:
                ctx.command = target_command
                # ctx.valid = True <-- 削除済み（自動計算されるため）
                ctx.prefix = COMMAND_PREFIX 
                
            log("CORE", f"Invoking '{command_name}' with {commander.user.name}...", Colors.CYAN, force=True)
            
            try:
                await commander.invoke(ctx)
            except Exception as e:
                log("CORE-ERROR", f"Command invocation failed: {e}", Colors.FAIL, force=True)
                traceback.print_exc()

    except Exception as e:
        log("CRITICAL", f"Error in handle_cli_command: {e}", Colors.FAIL, force=True)
        traceback.print_exc()

async def stdin_reader():
    loop = asyncio.get_running_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    
    while True:
        try:
            line = await reader.readline()
            if not line: break
            line_str = line.decode().strip()
            if not line_str: continue
            
            # JSONデコードと実行を待機
            try:
                data = json.loads(line_str)
                await handle_cli_command(data)
            except json.JSONDecodeError:
                log("CORE-WARN", "Invalid JSON received.", Colors.YELLOW, force=True)
        except asyncio.CancelledError:
            break
        except Exception as e:
            log("CORE-FATAL", f"Stdin reader error: {e}", Colors.FAIL, force=True)
            await asyncio.sleep(1) # 無限ループ防止

async def main(config):
    global bots, SETTINGS, COMMAND_PREFIX, TOKENS, PROXIES, VERBOSE_LOGGING
    SETTINGS = config['SETTINGS']
    COMMAND_PREFIX = config['COMMAND_PREFIX']
    TOKENS = config['TOKENS']
    PROXIES = config['PROXIES']
    VERBOSE_LOGGING = config['VERBOSE_LOGGING']

    pause_event = asyncio.Event(); pause_event.set()
    pause_lock = asyncio.Lock(); nuke_lock = asyncio.Lock()
    bots = [create_bot(token, PROXIES[i % len(PROXIES)] if PROXIES else None, pause_event, pause_lock, nuke_lock) for i, token in enumerate(TOKENS)]
    
    # Legion連携
    for bot in bots: bot.legion = bots

    log("INIT", f"Initializing {len(bots)} Hydra heads...", Colors.CYAN, force=True)
    
    try:
        stdin_task = asyncio.create_task(stdin_reader())
        bot_tasks = [b.start(b.token) for b in bots]
        await asyncio.gather(stdin_task, *bot_tasks)
    except Exception as e:
        log("FATAL", f"Runtime Error: {e}", Colors.FAIL, force=True)
    finally:
        for bot in bots:
            if not bot.is_closed(): await bot.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        try: asyncio.run(main(json.loads(sys.argv[1])))
        except KeyboardInterrupt: pass