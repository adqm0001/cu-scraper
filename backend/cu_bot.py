import discord
from discord.ext import commands

from dotenv import load_dotenv
import os
load_dotenv()

# run using: python -u cu_bot.py

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)
BOT_TOKEN = os.getenv("CU_BOT_TOKEN")

class Setup(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def setup(self, ctx):
        if await self.existing_creds(ctx.author):
            await ctx.send("Setup was already completed (use !updateCreds to update them or !forget to delete your current creds).")
            return

        await ctx.send("Enter your credentials")

    @commands.command()
    async def updateCreds(self, ctx):
        pass
        
    async def existing_creds(self, author):
        # for now always return false
        return False 

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged on as {self.bot.user}!')

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        print(f'Message from {message.author}: {message.content}')

async def main():
    await bot.add_cog(Setup(bot))
    await bot.add_cog(Test(bot))
    await bot.start(BOT_TOKEN)

import asyncio
asyncio.run(main())
