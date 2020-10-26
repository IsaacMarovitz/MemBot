import discord, nacl, youtube_dl, os, shutil, urllib.parse, urllib.request, re, tracemalloc
from discord.ext import commands
from discord.utils import get

TOKEN = "NzY5NzA1NzcwMzA3NTUxMjg0.X5S6XA.TmHgVOZ0ofIKtACV4G5gB0vCPcg"
COMMAND_PREFIX = "$"

bot = commands.Bot(command_prefix=COMMAND_PREFIX)
song_queue = []
tracemalloc.start()
play_thread_started = False

@bot.event
async def on_ready():
    print('Ready')
    await bot.change_presence(activity=discord.Game(name="with Python"))

@bot.command(pass_context=True)
async def join(ctx):
    global voice
    channel = ctx.message.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected():
        await voice.move_to(channel)
    else:
        try:
            voice = await channel.connect()
            print(f"Joined the {channel} channel")
        except discord.errors.ClientException:
            print("Already in voice channel")

    await ctx.send(f"Joined {channel}")

@bot.command(pass_context=True)
async def leave(ctx):
    channel = ctx.message.author.voice.channel
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected():
        await voice.disconnect()
        print(f"Left the {channel} channel")
        await ctx.send(f"Left {channel}")

@bot.command(pass_context=True)
async def play(ctx, *, search):
    query_string = urllib.parse.urlencode({
        'search_query': search
    })
    html_content = urllib.request.urlopen(
        'https://www.youtube.com/results?' + query_string
    )
    search_results = re.findall(r'watch\?v=(\S{11})', html_content.read().decode())
    song_queue.append(search_results[0])
    print(f"Added https://www.youtube.com/watch?v={search_results[0]} to the queue")
    await ctx.send(f"Added https://www.youtube.com/watch?v={search_results[0]} to the queue")
    start_play_next_thread(ctx)

@bot.command(pass_context=True)
async def pause(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_playing():
        print("Song paused")
        voice.pause()
        await ctx.send("Song paused")

@bot.command(pass_context=True)
async def resume(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_paused():
        print("Song resumed")
        voice.resume()
        await ctx.send("Song resumed")

@bot.command(pass_context=True)
async def stop(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)

    if voice and voice.is_playing():
        print("Song stopped")
        voice.stop()
        await ctx.send("Song stopped")

@bot.command(pass_context=True)
async def queue(ctx):
    counter = 0
    for song in song_queue:
        counter += 1
        await ctx.send(f"{counter}. https://www.youtube.com/watch?v={song}")

@bot.command(pass_context=True, aliases=['next'])
async def skip(ctx):
    voice = get(bot.voice_clients, guild=ctx.guild)
    voice.stop()
    start_play_next_thread(ctx)

def play_next(ctx):
    global play_thread_started
    voice = get(bot.voice_clients, guild=ctx.guild)

    if len(song_queue) > 0 and voice and not voice.is_playing():
        try:
            if os.path.isfile("song.mp3"):
                os.remove("song.mp3")
                print("Removed old song")
        except PermissionError:
            print("Failed to delete song file")
            return

        voice = get(bot.voice_clients, guild=ctx.guild)
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading song")
            try:
                ydl.download([f'https://www.youtube.com/watch?v={song_queue[0]}'])
            except youtube_dl.utils.DownloadError:
                print("Failed to download song")
                discord.Client().loop.create_task(ctx.send("Failed to download song"))
                return

        for files in os.listdir("./"):
            if files.endswith(".mp3"):
                os.rename(files, "song.mp3")

        voice.play(discord.FFmpegPCMAudio("./song.mp3"), after=lambda e: start_play_next_thread(ctx))
        voice.source = discord.PCMVolumeTransformer(voice.source)
        voice.source.volume = 0.07
        print("Playing song")
        discord.Client().loop.create_task(ctx.send(f"Playing https://www.youtube.com/watch?v={song_queue[0]}"))
        song_queue.pop(0)
    play_thread_started = False

bot.run(TOKEN)