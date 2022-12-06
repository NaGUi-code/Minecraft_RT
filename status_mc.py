import requests
import asyncio
import json
import bs4
import time
import base64
import datetime
import discord
import datetime
import os
from discord.ext import tasks, commands

# """
# {'status': 'success',
# 'online': True,
# 'motd': 'A Minecraft Server',
# 'motd_json': {'text': 'A Minecraft Server'},
# 'favicon': None,
# 'error': None,
# 'players': {'max': 20, 'now': 0, 'sample': []},
# 'server': {'name': '1.19.2', 'protocol': 760},
# 'last_updated': '1669810099', 'duration': '956689942'}
# """


class MC_RT(commands.Bot):
    message_players = ""

    channel_etat_id = 1049637913530466315

    path_to_whitelist = "/craftbukit/whitelist.json"

    server_name = "cybertim.fr"

    def get_info(self):
        r = requests.get(
            f'https://mcapi.us/server/status?ip={self.server_name}&port=25565')
        if r.status_code == 200:
            server_info = r.json()
            return server_info

    def get_uuid(self, username):
        r = requests.get(f'https://api.minetools.eu/uuid/{username}')
        if r.status_code == 200:
            data = r.json()
            if data["status"] == "ERR":
                r = requests.get(
                    f'https://minecraft-api.com/api/uuid/{username}')
                if r.status_code == 200:
                    data = r.content.decode()
                    return data if data != "Player not found !" else None

            return data["id"]

    def server_running(self):
        server_info = self.get_info()
        if not server_info["online"]:
            return False

        return True

    def skin_head(self, username, uuid):

        url = f"https://crafatar.com/avatars/{uuid}"

        r = requests.get(url)

        if r.status_code == 200:
            # save head_base64 to a file
            with open(f"skin_heads/{username}.png", "wb") as f:
                f.write(r.content)

        return "r.content"

    def generate_embed(self):
        server_info = self.get_info()

        embed = discord.Embed(
            title="Etat du serveur Minecraft", color=0x55FF55)
        embed.set_author(name="MC_RT", url='https://github.com/darklouiskil/MC_RT',
                         icon_url='https://cdn.icon-icons.com/icons2/2699/PNG/512/minecraft_logo_icon_168974.png')

        etat_serv = "**En ligne**" if server_info['online'] else "**Hors ligne**"
        nb_joueur = (str(server_info['players']['now']) if server_info['players']
                     ['now'] else "0") + "/" + str(server_info['players']['max'])
        version_serv = server_info['server']['name']

        informations = f"Etat du serveur : {etat_serv}\n" + \
            f"Nombre de joueurs : {nb_joueur}\n" + \
            f"Version du serveur : {version_serv}\n" +\
            f"Adresse du serveur : {self.server_name}\n"

        embed.add_field(name="Informations : ",
                        value=informations, inline=False)

        players = server_info["players"]["sample"]
        
        if not players:
            players = "Pas de joueurs en ligne."
        else:
            for player in server_info["players"]["sample"]:
                players += player["name"] + "\n"

        embed.add_field(name="\nJoueurs en ligne : ",
                        value=players, inline=False)
        embed.set_footer(
            text="Mise à jour le " + datetime.datetime.now().strftime("%d/%m/%Y à %H:%M:%S"))

        image_embed = "wallpaper.jpg"
        file = discord.File(image_embed, filename=image_embed)
        embed.set_image(url="attachment://"+image_embed)

        return embed, file

    def __init__(self, command_prefix, self_bot=False, channel_number=None):
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot,
                              intents=discord.Intents.all())

        async def presence_loop():
            while True:

                server_info = self.get_info()

                if not server_info["online"]:
                    presence = discord.Activity(name="SERVEUR HORS LIGNE",
                                                type=discord.ActivityType.playing)
                    asyncio.run_coroutine_threadsafe(
                        self.change_presence(activity=presence), self.loop)
                    await asyncio.sleep(10)
                    return

                players = server_info["players"]["now"]
                max_players = server_info["players"]["max"]

                presence = discord.Activity(name=f"{players}/{max_players} joueurs",
                                            type=discord.ActivityType.playing)
                asyncio.run_coroutine_threadsafe(
                    self.change_presence(activity=presence), self.loop)

                embed, file = self.generate_embed()

                if self.message_players:
                    await self.message_players.edit(embed=embed)

                await asyncio.sleep(10)

        @self.event
        async def on_ready():
            self.loop.create_task(presence_loop())

            print("Bot Online!")
            print("Name: {}".format(self.user.name))
            print("ID: {}".format(self.user.id))

            self.message_players = await ctx.fetch_message(1049722332031225856)

        @self.command()
        async def players(ctx):
            if ctx.message.channel.id == self.channel_etat_id:
                embed, file = self.generate_embed()

                if self.message_players:
                    await self.message_players.edit(embed=embed)
                    embed, file = self.generate_embed()

                if self.message_players:
                    await self.message_players.edit(embed=embed)
                else:
                    self.message_players = await ctx.send(embed=embed, file=file)

        @self.command()
        async def whitelist(ctx, username):
            print("Whitelisting " + username)

            username = username.strip()

            uuid = self.get_uuid(username)

            if not uuid:
                await ctx.send("Le joueur n'existe pas et/ou l'API est hors ligne.", delete_after=10)
                return

            json_to_add = {"uuid": uuid, "name": username}

            with open(self.path_to_whitelist, "r") as f:
                whitelist = json.load(f)

                if json_to_add in whitelist:
                    return await ctx.send("Le joueur est déjà whitelisté.", delete_after=10)

                whitelist.append(json_to_add)

            with open(self.path_to_whitelist, "w") as f:
                json.dump(whitelist, f)

            print(
                f"Le joueur {username} ({uuid}) a été whitelisté avec succès !")
            await ctx.send(f"Le joueur {username} ({uuid}) a été whitelisté avec succès !", delete_after=10)


with open("token.txt", "r", encoding="utf-8") as f:
    TOKEN = f.read()

bot = MC_RT("->")
bot.run(TOKEN)
