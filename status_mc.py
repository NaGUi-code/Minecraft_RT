import requests
import asyncio
import json
import bs4
import time
import base64
import datetime
import discord
import os
from discord.ext import commands

from PIL import Image

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
    message_etat = ""

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

    def update_presence(self):
        server_info = self.get_info()

        if not server_info["online"]:
            presence = discord.Activity(name="SERVEUR HORS LIGNE",
                                        type=discord.ActivityType.playing)
            asyncio.run_coroutine_threadsafe(
                self.change_presence(activity=presence), self.loop)
            return

        players = server_info["players"]["now"]
        max_players = server_info["players"]["max"]

        presence = discord.Activity(name=f"{players}/{max_players} joueurs",
                                    type=discord.ActivityType.playing)
        asyncio.run_coroutine_threadsafe(
            self.change_presence(activity=presence), self.loop)

    def __init__(self, command_prefix, self_bot=False, channel_number=None):
        commands.Bot.__init__(self, command_prefix=command_prefix, self_bot=self_bot,
                              intents=discord.Intents.all())

        @self.event
        async def on_ready():
            print("Bot Online!")
            print("Name: {}".format(self.user.name))
            print("ID: {}".format(self.user.id))

            self.update_presence()

        @self.command()
        async def status(ctx):
            server_info = self.get_info()

            str_etat = f"Le serveur {server_info['server']['name']} est " + (
                "en ligne." if server_info["online"] else "hors ligne.") + " Il y a actuellement " + str(server_info["players"]["now"]) + " joueur(s) sur le serveur."

            if self.message_etat:
                await self.message_etat.edit(content=str_etat)
            else:
                self.message_etat = await ctx.send(str_etat)

        @self.command()
        async def players(ctx):
            server_info = self.get_info()
            message = f"{str(server_info['players']['now'])} joueur(s) en ligne :"
            for player in server_info["players"]["sample"]:
                self.skin_head(player["name"], player["id"])
                message += "\n-" + player["name"]

            size_head = 100
            players_num = server_info['players']['now']
            collage = Image.new(
                'RGB', ((players_num * size_head), size_head))
            for i, player in enumerate(server_info["players"]["sample"]):

                if os.path.exists(f"skin_heads/{player['name']}.png"):

                    img = Image.open(f"skin_heads/{player['name']}.png")
                    if img.size != (size_head, size_head):
                        img = img.resize((size_head, size_head))
                    collage.paste(img, (i * size_head, 0))
                else:
                    img = Image.open("skin_heads/unknown.png")
                    collage.paste(img, (i * size_head, 0))

            collage.save("collage.png")

            embed = discord.Embed(
                title="Etat du serveur Minecraft", color=0x55FF55)
            embed.set_author(name="MC_RT", url='https://github.com/darklouiskil/MC_RT',
                             icon_url='https://cdn.icon-icons.com/icons2/2699/PNG/512/minecraft_logo_icon_168974.png')

            informations = "Etat du serveur : " + ("**En ligne**" if server_info['online'] else "**Hors ligne**") + "\n" + \
                "Nombre de joueurs : **" + str(server_info['players']['now']) + "/" + str(server_info['players']['max']) + "**\n" + \
                "Version du serveur : " + server_info['server']['name'] + "\n" + \
                "Adresse du serveur : " + self.server_name 

            embed.add_field(name="Informations : ",
                            value=informations, inline=False)

            # gather all the players in a string
            players = ""
            for player in server_info["players"]["sample"]:
                players += player["name"] + "\n"

            embed.add_field(name="Joueurs en ligne : ",
                            value=players, inline=False)

            file = discord.File("collage.png", filename="collage.png")
            embed.set_image(url="attachment://collage.png")
            embed.set_footer(
                text="Si vous remarquez une erreur contacter un admin !")

            if self.message_players:
                self.message_players.set_image(url="attachment://collage.png")
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

            with open("whitelist.json", "r") as f:
                whitelist = json.load(f)

                if json_to_add in whitelist:
                    return await ctx.send("Le joueur est déjà whitelisté.", delete_after=10)

                whitelist.append(json_to_add)

            with open("whitelist.json", "w") as f:
                json.dump(whitelist, f)

            print(
                f"Le joueur {username} ({uuid}) a été whitelisté avec succès !")
            await ctx.send(f"Le joueur {username} ({uuid}) a été whitelisté avec succès !", delete_after=10)


with open("token.txt", "r", encoding="utf-8") as f:
    TOKEN = f.read()

bot = MC_RT("->")
bot.run(TOKEN)
