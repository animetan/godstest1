import os
import sys
import glob
from os import walk

sys.path.append(os.path.abspath('../settings'))
from global_sets import *
from async_timeout import timeout
from discord.ext import commands
from github import Github

class VoiceError(Exception):
    pass


class YTDLError(Exception):
    pass


class YTDLSource(discord.PCMVolumeTransformer):
    YTDL_OPTIONS = {
        'format': 'bestaudio/best',
        'extractaudio': True,
        'audioformat': 'mp3',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch',
        'cookiefile': 'cookies.txt',
        'source_address': '0.0.0.0'      
    }

    FFMPEG_OPTIONS = {
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
        'options': '-vn',
    }

    ytdl = youtube_dl.YoutubeDL(YTDL_OPTIONS)

    def __init__(self, ctx: commands.Context, source: discord.FFmpegPCMAudio, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.requester = ctx.author
        self.channel = ctx.channel
        self.data = data

        self.uploader = data.get('uploader')
        self.uploader_url = data.get('uploader_url')
        date = data.get('upload_date')
        self.upload_date = date[6:8] + '.' + date[4:6] + '.' + date[0:4]
        self.title = data.get('title')
        self.thumbnail = data.get('thumbnail')
        self.description = data.get('description')
        self.duration = self.parse_duration(int(data.get('duration')))
        self.tags = data.get('tags')
        self.url = data.get('webpage_url')
        self.views = data.get('view_count')
        self.likes = data.get('like_count')
        self.dislikes = data.get('dislike_count')
        self.stream_url = data.get('url')

    def __str__(self):
        return '**{0.title}** by **{0.uploader}**'.format(self)

    @classmethod
    async def create_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        loop = loop or asyncio.get_event_loop()

        partial = functools.partial(cls.ytdl.extract_info, search, download=False, process=False)
        data = await loop.run_in_executor(None, partial)

        if data is None:
            raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        if 'entries' not in data:
            process_info = data
        else:
            process_info = None
            for entry in data['entries']:
                if entry:
                    process_info = entry
                    break

            if process_info is None:
                raise YTDLError('Couldn\'t find anything that matches `{}`'.format(search))

        webpage_url = process_info['webpage_url']
        partial = functools.partial(cls.ytdl.extract_info, webpage_url, download=False)
        processed_info = await loop.run_in_executor(None, partial)

        if processed_info is None:
            raise YTDLError('Couldn\'t fetch `{}`'.format(webpage_url))

        if 'entries' not in processed_info:
            info = processed_info
        else:
            info = None
            while info is None:
                try:
                    info = processed_info['entries'].pop(0)
                except IndexError:
                    raise YTDLError('Couldn\'t retrieve any matches for `{}`'.format(webpage_url))
        
        return cls(ctx, discord.FFmpegPCMAudio(info['url'], **cls.FFMPEG_OPTIONS), data=info)

    @classmethod
    async def search_source(cls, ctx: commands.Context, search: str, *, loop: asyncio.BaseEventLoop = None):
        channel = ctx.channel
        loop = loop or asyncio.get_event_loop()

        cls.search_query = '%s%s:%s' % ('ytsearch', 10, ''.join(search))

        partial = functools.partial(cls.ytdl.extract_info, cls.search_query, download=False, process=False)
        info = await loop.run_in_executor(None, partial)

        cls.search = {}
        cls.search["title"] = f'Search results for:\n**{search}**'
        cls.search["type"] = 'rich'
        cls.search["color"] = 7506394
        cls.search["author"] = {'name': f'{ctx.author.name}', 'url': f'{ctx.author.avatar_url}', 'icon_url': f'{ctx.author.avatar_url}'}
        
        lst = []

        for e in info['entries']:
            #lst.append(f'`{info["entries"].index(e) + 1}.` {e.get("title")} **[{YTDLSource.parse_duration(int(e.get("duration")))}]**\n')
            VId = e.get('id')
            VUrl = 'https://www.youtube.com/watch?v=%s' % (VId)
            lst.append(f'`{info["entries"].index(e) + 1}.` [{e.get("title")}]({VUrl})\n')

        lst.append('\n**Type a number to make a choice, Type `cancel` to exit**')
        cls.search["description"] = "\n".join(lst)

        em = discord.Embed.from_dict(cls.search)
        await ctx.send(embed=em, delete_after=45.0)

        def check(msg):
            return msg.content.isdigit() == True and msg.channel == channel or msg.content == 'cancel' or msg.content == 'Cancel'
        
        try:
            m = await client.wait_for('message', check=check, timeout=45.0)

        except asyncio.TimeoutError:
            rtrn = 'timeout'

        else:
            if m.content.isdigit() == True:
                sel = int(m.content)
                if 0 < sel <= 10:
                    for key, value in info.items():
                        if key == 'entries':
                            """data = value[sel - 1]"""
                            VId = value[sel - 1]['id']
                            VUrl = 'https://www.youtube.com/watch?v=%s' % (VId)
                            partial = functools.partial(cls.ytdl.extract_info, VUrl, download=False)
                            data = await loop.run_in_executor(None, partial)
                    rtrn = cls(ctx, discord.FFmpegPCMAudio(data['url'], **cls.FFMPEG_OPTIONS), data=data)
                else:
                    rtrn = 'sel_invalid'
            elif m.content == 'cancel':
                rtrn = 'cancel'
            else:
                rtrn = 'sel_invalid'
        
        return rtrn

    @staticmethod
    def parse_duration(duration: int):
        if duration > 0:
            minutes, seconds = divmod(duration, 60)
            hours, minutes = divmod(minutes, 60)
            days, hours = divmod(hours, 24)

            duration = []
            if days > 0:
                duration.append('{}'.format(days))
            if hours > 0:
                duration.append('{}'.format(hours))
            if minutes > 0:
                duration.append('{}'.format(minutes))
            if seconds > 0:
                duration.append('{}'.format(seconds))
            
            value = ':'.join(duration)
        
        elif duration == 0:
            value = "LIVE"
        
        return value

# Each song class
class Song:
    __slots__ = ('source', 'requester')

    def __init__(self, source: YTDLSource):
        self.source = source
        self.requester = source.requester
    
    def create_embed(self):
        embed = (discord.Embed(title='Now playing', description='```css\n{0.source.title}\n```'.format(self), color=discord.Color.magenta())
                .add_field(name='Duration', value=self.source.duration)
                .add_field(name='Requested by', value=self.requester.mention)
                .add_field(name='Uploader', value='[{0.source.uploader}]({0.source.uploader_url})'.format(self))
                .add_field(name='URL', value='[Click]({0.source.url})'.format(self))
                .set_thumbnail(url=self.source.thumbnail)
                .set_author(name=self.requester.name, icon_url=self.requester.avatar_url))
        return embed

# Class for songs in queue
class SongQueue(asyncio.Queue):
    def __getitem__(self, item):
        if isinstance(item, slice):
            return list(itertools.islice(self._queue, item.start, item.stop, item.step))
        else:
            return self._queue[item]

    def __iter__(self):
        return self._queue.__iter__()

    def __len__(self):
        return self.qsize()

    def clear(self):
        self._queue.clear()

    def shuffle(self):
        random.shuffle(self._queue)

    def remove(self, index: int):
        del self._queue[index]

# Bot voice state
class VoiceState:
    def __init__(self, bot: commands.Bot, ctx: commands.Context):
        self.bot = bot
        self._ctx = ctx

        self.current = None
        self.voice = None
        self.next = asyncio.Event()
        self.songs = SongQueue()
        self.exists = True

        self._loop = False
        self._volume = 0.4
        self.skip_votes = set()

        self.audio_player = bot.loop.create_task(self.audio_player_task())

    def __del__(self):
        self.audio_player.cancel()

    @property
    def loop(self):
        return self._loop

    @loop.setter
    def loop(self, value: bool):
        self._loop = value

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, value: float):
        self._volume = value

    @property
    def is_playing(self):
        return self.voice and self.current

    async def audio_player_task(self):
        while True:
            self.next.clear()
            self.now = None

            if self.loop == False:
                # Try to get the next song within 3 minutes.
                # If no song will be added to the queue in time,
                # the player will disconnect due to performance
                # reasons.
                try:
                    async with timeout(180):  # 3 minutes
                        self.current = await self.songs.get()
                except asyncio.TimeoutError:
                    self.bot.loop.create_task(self.stop())
                    self.exists = False
                    return
                
                self.current.source.volume = self._volume
                self.voice.play(self.current.source, after=self.play_next_song)
                await self.current.source.channel.send(embed=self.current.create_embed())
            
            #If the song is looped
            elif self.loop == True:
                self.now = discord.FFmpegPCMAudio(self.current.source.stream_url, **YTDLSource.FFMPEG_OPTIONS)
                self.voice.play(self.now, after=self.play_next_song)
            
            await self.next.wait()

    def play_next_song(self, error=None):
        if error:
            raise VoiceError(str(error))

        self.next.set()

    def skip(self):
        self.skip_votes.clear()

        if self.is_playing:
            self.voice.stop()

    async def stop(self):
        self.songs.clear()

        if self.voice:
            await self.voice.disconnect()
            self.voice = None

# Main commands
class Music(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_states = {}

    def get_voice_state(self, ctx: commands.Context):
        state = self.voice_states.get(ctx.guild.id)
        if not state or not state.exists:
            state = VoiceState(self.bot, ctx)
            self.voice_states[ctx.guild.id] = state

        return state

    def cog_unload(self):
        for state in self.voice_states.values():
            self.bot.loop.create_task(state.stop())

    def cog_check(self, ctx: commands.Context):
        if not ctx.guild:
            raise commands.NoPrivateMessage('This command can\'t be used in DM channels.')

        return True

    async def cog_before_invoke(self, ctx: commands.Context):
        ctx.voice_state = self.get_voice_state(ctx)

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await ctx.send('An error occurred: {}'.format(str(error)))

    # Bot will join in author's voice channel
    #########################################
    @commands.command(name='join', invoke_without_subcommand=True)
    async def _join(self, ctx: commands.Context):
        if (right_channel(ctx)):
            destination = ctx.author.voice.channel
            if ctx.voice_state.voice:
                await ctx.voice_state.voice.move_to(destination)
                return

            ctx.voice_state.voice = await destination.connect()

    # Bot will join in author's voice channel
    #########################################
    @commands.command(name='summon')
    @commands.has_permissions(manage_guild=True)
    async def _summon(self, ctx: commands.Context, *, channel: discord.VoiceChannel = None):
        if (right_channel(ctx)):
            if not channel and not ctx.author.voice:
                raise VoiceError('You are neither connected to a voice channel nor specified a channel to join.')

            destination = channel or ctx.author.voice.channel
            if ctx.voice_state.voice:
                await ctx.voice_state.voice.move_to(destination)
                return

            ctx.voice_state.voice = await destination.connect()

    # Bot will leave voice channel
    ##############################
    @commands.command(name='leave', aliases=['disconnect'])
    @commands.has_permissions(manage_guild=True)
    async def _leave(self, ctx: commands.Context):
        if (right_channel(ctx)):
            if not ctx.voice_state.voice:
                return await ctx.send('Вы не подключены к голосовому каналу')

            await ctx.voice_state.stop()
            del self.voice_states[ctx.guild.id]

    # Setup song volume
    ###################
    @commands.command(name='volume')
    @commands.is_owner()
    async def _volume(self, ctx: commands.Context, *, volume: int):
        if (right_channel(ctx)):
            if not ctx.voice_state.is_playing:
                return await ctx.send('Сейчас ничего не играет.')

            if (volume < 0) or (volume > 100):
                return await ctx.send('Громкость должна быть между 0 и 100')

            ctx.voice_state.current.source.volume = volume / 100
            await ctx.send('Громкость плеера установлена на {}%'.format(volume))

    # Get information about current playing song
    ############################################
    @commands.command(name='now', aliases=['current', 'playing'])
    async def _now(self, ctx: commands.Context):
        if (right_channel(ctx)):
            if not ctx.voice_state.is_playing:
                embed = ctx.voice_state.current.create_embed()
                await ctx.send(embed=embed)
            else:
                await ctx.send("Сейчас ничего не играет.")

    # Pause current playing song
    ############################
    @commands.command(name='pause', aliases=['pa'])
    @commands.has_permissions(manage_guild=True)
    async def _pause(self, ctx: commands.Context):
        if (right_channel(ctx)):
            if ctx.voice_state.is_playing and ctx.voice_state.voice.is_playing():
                ctx.voice_state.voice.pause()
                await ctx.message.add_reaction('⏯')

    # Resume current paused song
    ############################
    @commands.command(name='resume', aliases=['re', 'res'])
    @commands.has_permissions(manage_guild=True)
    async def _resume(self, ctx: commands.Context):
        if (right_channel(ctx)):
            if ctx.voice_state.is_playing and ctx.voice_state.voice.is_paused():
                ctx.voice_state.voice.resume()
                await ctx.message.add_reaction('⏯')

    # Bot will stop playing music
    #############################
    @commands.command(name='stop')
    @commands.has_permissions(manage_guild=True)
    async def _stop(self, ctx: commands.Context):
        if (right_channel(ctx)):
            ctx.voice_state.songs.clear()

            if ctx.voice_state.is_playing:
                ctx.voice_state.voice.stop()
                await ctx.message.add_reaction('⏹')

    # Skip current playing song
    ###########################
    @commands.command(name='skip', aliases=['s'])
    async def _skip(self, ctx: commands.Context):
        if (right_channel(ctx)):
            if not ctx.voice_state.is_playing:
                return await ctx.send('Сейчас ничего не играет')

            voter = ctx.message.author
            if voter == ctx.voice_state.current.requester:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()

            elif voter.id not in ctx.voice_state.skip_votes:
                await ctx.message.add_reaction('⏭')
                ctx.voice_state.skip()

            else:
                await ctx.send('You have already voted to skip this song.')

    # Bot will send current song queue
    ##################################
    @commands.command(name='queue')
    async def _queue(self, ctx: commands.Context, *, page: int = 1):
        if (right_channel(ctx)):
            if len(ctx.voice_state.songs) == 0:
                return await ctx.send('В очереди нет треков.')

            items_per_page = 10
            pages = math.ceil(len(ctx.voice_state.songs) / items_per_page)

            start = (page - 1) * items_per_page
            end = start + items_per_page

            queue = ''
            for i, song in enumerate(ctx.voice_state.songs[start:end], start=start):
                queue += '`{0}.` [**{1.source.title}**]({1.source.url})\n'.format(i + 1, song)

            embed = (discord.Embed(description='**{} Треки:**\n\n{}'.format(len(ctx.voice_state.songs), queue))
                     .set_footer(text='Страница {}/{}'.format(page, pages)))
            await ctx.send(embed=embed)
    

    # Bot will shuffle tracks in queue
    ##################################
    @commands.command(name='shuffle')
    async def _shuffle(self, ctx: commands.Context):
        if (right_channel(ctx)):
            if len(ctx.voice_state.songs) == 0:
                return await ctx.send('В очереди нет треков.')

            ctx.voice_state.songs.shuffle()
            await ctx.message.add_reaction('✅')

    # Bot will remove indexed song in queue
    #######################################
    @commands.command(name='remove')
    async def _remove(self, ctx: commands.Context, index: int):
        if (right_channel(ctx)):
            if len(ctx.voice_state.songs) == 0:
                return await ctx.send('В очереди нет треков.')

            ctx.voice_state.songs.remove(index - 1)
            await ctx.message.add_reaction('✅')

    # Bot will loop current playing song
    ####################################
    @commands.command(name='loop')
    async def _loop(self, ctx: commands.Context):
        if (right_channel(ctx)):
            if not ctx.voice_state.is_playing:
                return await ctx.send('Сейчас ничего не играет.')

            # Inverse boolean value to loop and unloop.
            ctx.voice_state.loop = not ctx.voice_state.loop
            await ctx.message.add_reaction('✅')

    # Bot will play linked song
    ###########################
    @commands.command(name='play', aliases=['p'])
    async def _play(self, ctx: commands.Context, *, search: str):      
        #https://rg3.github.io/youtube-dl/supportedsites.html
        if (right_channel(ctx)):
            async with ctx.typing():
                try:
                    source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop)
                except YTDLError as e:
                    await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
                else:
                    if not ctx.voice_state.voice:
                        await ctx.invoke(self._join)

                    song = Song(source)
                    await ctx.voice_state.songs.put(song)
                    await ctx.send('Добавлено в очередь {}'.format(str(source)))


    ########################################################################################
    #################################### PLAYLISTS PART ####################################
    ########################################################################################


    # External playlists update
    ###########################
    

    
    
    # List of all playlists
    #######################
    @commands.command(name='playlists')
    async def _playlists(self, ctx: commands.Context, *, page: int = 1):
        if (right_channel(ctx)):
            playlists_update_ext(ctx)
        
            ff = []
            for (dirpath, dirnames, filenames) in walk("playlists/"):
                ff.extend(filenames)
                break
            
            f = [x[:-5] for x in ff]
            
            if len(f) == 0:
                return await ctx.send('В настоящее времени нет доступных плейлистов!')

            items_per_page = 10
            pages = math.ceil(len(f) / items_per_page)

            start = (page - 1) * items_per_page
            end = start + items_per_page

            playlists_list = ''
            for i, song in enumerate(f[start:end], start=start):
                playlists_list += '`{0}` {1}\n'.format(i + 1, f[i])

            embed = (discord.Embed(description='**{} Плейлисты:**\n\n{}'.format(len(f), playlists_list))
                     .set_footer(text='Страница {}/{}'.format(page, pages)))
            await ctx.send(embed=embed)


    # List of all playlists created by message author
    #################################################
    @commands.command(name='playlists_my')
    async def _playlists_my(self, ctx: commands.Context, page: int = 1):
        if (right_channel(ctx)):
            playlists_update_ext(ctx)
            
            all_p = []
            for (dirpath, dirnames, filenames) in walk("playlists/"):
                all_p.extend(filenames)
                break

            all_p_formatted = [x[:-5] for x in all_p]
            if len(all_p_formatted) == 0:
                return await ctx.send('В настоящее времени нет доступных плейлистов!')
            
            my_plists = []
            for plist in all_p_formatted:
                with open('playlists/{}.json'.format(str(plist))) as f:
                    data = json.load(f)
                    info_list = data['information']  
                    for v in info_list:
                        author_id = str(v)[12:-2]
                        author = client.get_user(int(author_id))
                        if (str(author_id) == str(ctx.author.id)):
                            my_plists += [plist]

            if (len(my_plists) == 0):
                return await ctx.send('У вас нет плейлистов!')

            print(my_plists)

            emb = discord.Embed( title = 'Плейлисты {}'.format(str(ctx.author.name)), description = '', colour = discord.Color.magenta() )
            
            items_per_page = 10
            pages = math.ceil(len(my_plists) / items_per_page)

            start = (page - 1) * items_per_page
            end = start + items_per_page

            playlists_list = ''
            for i, song in enumerate(my_plists[start:end], start=start):
                playlists_list += '`{0}.` {1}\n'.format(i + 1, my_plists[i])

            embed = (discord.Embed(description='**{} Плейлисты:**\n\n{}'.format(len(my_plists), playlists_list))
                     .set_footer(text='Страница {}/{}'.format(page, pages)))
            embed.set_author(name = ctx.author.name, icon_url = ctx.author.avatar_url)
            
            await ctx.send(embed=embed)

    # Information about playlist
    ############################
    @commands.command(name='playlist')
    async def _playlist(self, ctx: commands.Context, p_name):
        if (right_channel(ctx)):
            playlists_update_ext(ctx)
            
            existing = os.path.exists('playlists/{}.json'.format(str(p_name)))
            if not (existing):
                return await ctx.send('Плейлист с таким названием не существует!')

            author = ''
            with open('playlists/{}.json'.format(str(p_name))) as f:
                    data = json.load(f)
                    info_list = data['information']  
                    for v in info_list:
                        author_id = str(v)[12:-2]
                        author = client.get_user(int(author_id))

            emb = discord.Embed( title = '{}'.format(str(p_name)), description = '', colour = discord.Color.magenta() )
            emb.set_author(name = author.name, icon_url = author.avatar_url)

            with open('playlists/{}.json'.format(str(p_name))) as f:
                    data = json.load(f)
                    plist = data[str(p_name)]
                    count = 0
                    for d in plist:
                        count = count + 1
                        temp_str = str(d)[13:-2]
                        emb.add_field( name = '{}'.format(str(temp_str)), value = 'track index: {}'.format(str(count)), inline=False)
            
            emb.set_thumbnail(url = "https://icons.iconarchive.com/icons/graphicloads/100-flat/128/sound-2-icon.png")
            await ctx.send ( embed = emb)


    # Rename playlist
    #################
    @commands.command(name='playlist_rename')
    async def _playlist_rename(self, ctx: commands.Context, p_name, new_name):
        if (right_channel(ctx)):
            playlists_update_ext(ctx)
            
            existing = os.path.exists('playlists/{}.json'.format(str(p_name)))
            if not (existing):
                return await ctx.send('Плейлист с таким названием не существует!')

            existing_new = os.path.exists('playlists/{}.json'.format(str(new_name)))
            if (existing_new):
                return await ctx.send('Плейлист с таким названием уже существует!')

            with open('playlists/{}.json'.format(str(p_name))) as f:
                data = json.load(f)
                info_list = data['information']  
                for v in info_list:
                    temp_author = str(v)[12:-2]
                    
                    if (str(temp_author) != str(ctx.author.id)):
                        return await ctx.send('Вы не можете изменить чужой плейлист!')
                
                data[str(new_name)] = data[str(p_name)]
                del data[str(p_name)]
            
            with open('playlists/{}.json'.format(str(p_name)),'w') as f: 
                json.dump(data, f, indent=4) 
            
            os.rename('playlists/{}.json'.format(str(p_name)), 'playlists/{}.json'.format(str(new_name)))
            
            for rep in g.get_user().get_repos():
                    if rep.name == 'playlists':
                        repo = rep
                
            contents = repo.get_contents('{}.json'.format(str(p_name)), ref="main")
            repo.delete_file(contents.path, "rename", contents.sha, branch="main")
            
            with open('playlists/{}.json'.format(str(new_name)), 'r') as f:
                s = f.read()
                repo.create_file('{}.json'.format(str(new_name)), "rename", s, branch="main")
            
            await ctx.send('Плейлист `{}` переименован на `{}`'.format(str(p_name), str(new_name)))


    # Delete playlist
    #######################
    @commands.command(name='playlist_delete')
    async def _playlist_delete(self, ctx: commands.Context, p_name):
        if (right_channel(ctx)):
            playlists_update_ext(ctx)
            
            existing = os.path.exists('playlists/{}.json'.format(str(p_name)))
            if not (existing):
                return await ctx.send('Плейлист с таким названием не существует!')

            with open('playlists/{}.json'.format(str(p_name))) as f:
                data = json.load(f)
                info_list = data['information']  
                for v in info_list:
                    temp_author = str(v)[12:-2]
                    
                    if (str(temp_author) != str(ctx.author.id)):
                        return await ctx.send('Вы не можете удалить чужой плейлист!')
                    
            os.remove('playlists/{}.json'.format(str(p_name)))
            
            for rep in g.get_user().get_repos():
                    if rep.name == 'playlists':
                        repo = rep
                
            contents = repo.get_contents('{}.json'.format(str(p_name)), ref="main")
            repo.delete_file(contents.path, "delete", contents.sha, branch="main")
            
            await ctx.send('Плейлист `{}` удалён'.format(str(p_name)))
    

    # Create playlist
    #################
    @commands.command(name='playlist_create')
    async def _playlist_create(self, ctx: commands.Context, p_name):
        if (right_channel(ctx)):    
            existing = os.path.exists('playlists/{}.json'.format(str(p_name)))
            if (existing):
                return await ctx.send('Плейлист с таким названием уже существует!')

            text = '{{ "information": [ {{ "author": "{0}" }} ], "{1}": [ ] }}'.format(str(ctx.author.id), str(p_name))

            with open('playlists/{}.json'.format(str(p_name)), 'w') as f:
                f.write(text)
                
            for rep in g.get_user().get_repos():
                    if rep.name == 'playlists':
                        repo = rep
                
            with open('playlists/{}.json'.format(str(p_name)), 'r') as f:
                s = f.read()
                repo.create_file('{}.json'.format(str(p_name)), "create", s, branch="main")
            
            playlists_update_ext(ctx)

            await ctx.send('Плейлист `{}` создан'.format(str(p_name)))


    # Add song in playlist
    ######################
    @commands.command(name='playlist_add')
    async def _playlist_add(self, ctx: commands.Context, p_name, *, link: str):
        if (right_channel(ctx)):
            playlists_update_ext(ctx)
            
            try:
                source = await YTDLSource.create_source(ctx, link, loop=self.bot.loop)
            except YTDLError as e:
                await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
            else:
                merged = { "youtube" : str(link) }

                with open('playlists/{}.json'.format(str(p_name))) as f:
                    data = json.load(f)
                    info_list = data['information']  
                    for v in info_list:
                        temp_author = str(v)[12:-2]
                        
                        if (str(temp_author) != str(ctx.author.id)):
                            return await ctx.send('Вы не можете изменять чужой плейлист!')
                  
                    plist = data[str(p_name)]
                    tracks_count = 0
                    for d in plist:
                        tracks_count = tracks_count + 1
                        if (tracks_count > 14): # == 15
                            return await ctx.send('Нельзя добавить в плейлист больше 15 треков!')

                    plist.append(merged)

                with open('playlists/{}.json'.format(str(p_name)),'w') as f: 
                    json.dump(data, f, indent=4) 
                
                for rep in g.get_user().get_repos():
                    if rep.name == 'playlists':
                        repo = rep
                
                with open('playlists/{}.json'.format(str(p_name)), 'r') as f:
                    contents = repo.get_contents('{}.json'.format(str(p_name)), ref="main")
                    s = f.read()
                    repo.update_file(contents.path, "add", s, contents.sha, branch="main")
                
                await ctx.send('Трек успешно добавлен в плейлист `{}`'.format(str(p_name)))


    # Remove song from playlist
    ###########################
    @commands.command(name='playlist_remove')
    async def _playlist_remove(self, ctx: commands.Context, p_name, index: int):
        if (right_channel(ctx)):
            playlists_update_ext(ctx)
            
            if (index < 1):
                return await ctx.send('index >= 1')
            with open('playlists/{}.json'.format(str(p_name))) as f:
                data = json.load(f)
                info_list = data['information']  
                for v in info_list:
                    temp_author = str(v)[12:-2]
                    
                    if (str(temp_author) != str(ctx.author.id)):
                        return await ctx.send('Вы не можете изменять чужой плейлист!')
              
                plist = data[str(p_name)]
                tracks_count = 0
                for d in plist:
                    tracks_count = tracks_count + 1
                    if (tracks_count < 1):
                        return await ctx.send('В плейлисте нет треков!')
                
                plist.pop(index - 1)

            with open('playlists/{}.json'.format(str(p_name)),'w') as f: 
                json.dump(data, f, indent=4) 
            
            for rep in g.get_user().get_repos():
                if rep.name == 'playlists':
                    repo = rep
            
            with open('playlists/{}.json'.format(str(p_name)), 'r') as f:
                contents = repo.get_contents('{}.json'.format(str(p_name)), ref="main")
                s = f.read()
                repo.update_file(contents.path, "remove", s, contents.sha, branch="main")

            await ctx.send('Трек под номером `{0}` был удалён из плейлиста`{1}`'.format(str(index), str(p_name)))


    # Play playlist
    ###############
    @commands.command(name='playlist_play')
    async def _playlist_play(self, ctx: commands.Context, *, p_name):
        if (right_channel(ctx)):
            playlists_update_ext(ctx)
            
            tracks = []
            with open('playlists/{}.json'.format(str(p_name)), 'r') as f:
                data = json.load(f)       
                plist = data[str(p_name)]  
                for v in plist:
                    temp_str = str(v)[13:-2]
                    tracks += [temp_str]
                    async with ctx.typing():
                        try:
                            source = await YTDLSource.create_source(ctx, temp_str, loop=self.bot.loop)
                        except YTDLError as e:
                            await ctx.send('An error occurred while processing this request: {}'.format(str(e)))
                        else:
                            if not ctx.voice_state.voice:
                                await ctx.invoke(self._join)

                            song = Song(source)
                            await ctx.voice_state.songs.put(song)
                            print('Добавлено в очередь {}'.format(str(source)))

            await ctx.send(('Плейлист `{}` добавлен в очередь!').format(str(p_name)))
            
            
    # Update playlists
    ##################
    @commands.command(name='playlists_update')
    async def _playlists_update(self, ctx: commands.Context):
        if (right_channel(ctx)):
            files = glob.glob('playlists/*')
            for f in files:
                os.remove(f)
                
            for rep in g.get_user().get_repos():
                if rep.name == 'playlists':
                    repo = rep
            contents = repo.get_contents("")
            while contents:
                file_content = contents.pop(0)
                if file_content.type != "dir":
                    with open("playlists/{}".format(file_content.name), 'w') as f:
                        f.write(file_content.decoded_content.decode())
                        
            await ctx.send(('Список плейлистов обновлён!'))
            
            
    @_join.before_invoke
    @_play.before_invoke
    async def ensure_voice_state(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            raise commands.CommandError('Вы не подключены к голосовому каналу')

        if ctx.voice_client:
            if ctx.voice_client.channel != ctx.author.voice.channel:
                raise commands.CommandError('Я уже в голосовом канале')
