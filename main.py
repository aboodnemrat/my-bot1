import discord
from discord.ext import commands, tasks
import asyncio
import os

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
PREFIX = "!"
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.voice_states = True
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

class PlayerManager:
    def __init__(self):
        self.voice_clients = {}
        self.stay_in_channels = set()

player = PlayerManager()

class RateLimiter:
    def __init__(self):
        self.cooldowns = {}
        self.global_cooldown = 2

    async def wait_before_command(self, ctx):
        now = asyncio.get_event_loop().time()
        user_id = ctx.author.id
        if user_id in self.cooldowns:
            remaining = self.cooldowns[user_id] - now
            if remaining > 0:
                await asyncio.sleep(remaining)
        self.cooldowns[user_id] = now + self.global_cooldown

    def set_global_cooldown(self, seconds):
        self.global_cooldown = seconds

rate_limiter = RateLimiter()

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    adjust_rate_limit.start()

@bot.command(aliases=['join', 'دخول'])
async def connect(ctx):
    try:
        await rate_limiter.wait_before_command(ctx)
        if ctx.author.voice is None:
            return await ctx.send("❗ يجب أن تكون في قناة صوتية أولاً")
        channel = ctx.author.voice.channel
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.move_to(channel)
        else:
            voice = await channel.connect()
        player.voice_clients[channel.id] = voice
        await ctx.send(f"✅ تم الاتصال بـ **{channel.name}**")
    except Exception as e:
        await ctx.send(f"❌ خطأ: {e}")

@bot.command(aliases=['leave', 'مغادرة'])
async def disconnect(ctx):
    try:
        await rate_limiter.wait_before_command(ctx)
        voice = discord.utils.get(bot.voice_clients, guild=ctx.guild)
        if voice and voice.is_connected():
            await voice.disconnect()
            channel_id = ctx.author.voice.channel.id
            player.voice_clients.pop(channel_id, None)
            player.stay_in_channels.discard(channel_id)
            await ctx.send("👋 تم قطع الاتصال")
        else:
            await ctx.send("❗ البوت غير متصل بأي قناة صوتية")
    except Exception as e:
        await ctx.send(f"❌ خطأ: {e}")

@bot.command(aliases=['stay', 'ثبات', 'ابقاء'])
async def stay_in_channel(ctx, action: str = None):
    try:
        await rate_limiter.wait_before_command(ctx)
        if ctx.author.voice is None:
            return await ctx.send("❗ يجب أن تكون في قناة صوتية")
        channel_id = ctx.author.voice.channel.id
        if action is None:
            status = "ON" if channel_id in player.stay_in_channels else "OFF"
            return await ctx.send(f"🔄 وضع الثبات حالياً **{status}**")
        action = action.lower()
        if action in ['on', 'تشغيل', 'نعم']:
            player.stay_in_channels.add(channel_id)
            await ctx.send("✅ تم تفعيل وضع الثبات")
        elif action in ['off', 'ايقاف', 'لا']:
            player.stay_in_channels.discard(channel_id)
            await ctx.send("✅ تم تعطيل وضع الثبات")
        else:
            await ctx.send("❗ خيار غير صالح")
    except Exception as e:
        await ctx.send(f"❌ خطأ: {e}")

@bot.command(aliases=['connections', 'الاتصالات', 'ات'])
async def show_connections(ctx):
    try:
        await rate_limiter.wait_before_command(ctx)
        if not player.voice_clients:
            return await ctx.send("📡 لا يوجد اتصالات حالياً")
        embed = discord.Embed(title="📡 الاتصالات", color=discord.Color.green())
        for channel_id, voice_client in player.voice_clients.items():
            channel = bot.get_channel(channel_id)
            if channel:
                status = "✅ مثبت" if channel_id in player.stay_in_channels else "❌ غير مثبت"
                embed.add_field(name=channel.name, value=status, inline=False)
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ خطأ: {e}")

@tasks.loop(minutes=5)
async def adjust_rate_limit():
    try:
        rate_limiter.set_global_cooldown(2)
    except:
        pass

bot.run(TOKEN)
