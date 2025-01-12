import discord
from discord.ext import commands
import random

#bot制作はほぼchat gptだお

# Intentsの設定
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True

# Botのセットアップ
bot = commands.Bot(command_prefix="!", intents=intents)
ERROR_CHANNEL_ID = 1279733083138162748

class GiveawayButton(discord.ui.View):
    def __init__(self, timeout, prize, content):
        super().__init__(timeout=timeout)
        self.participants = []
        self.prize = prize
        self.content = content
        self.message = None  # メッセージを格納するための変数

    @discord.ui.button(label="参加", style=discord.ButtonStyle.primary)
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.participants:
            self.participants.append(interaction.user.id)
            await interaction.response.send_message(f"{interaction.user.name} さんが参加しました！", ephemeral=True)
            
            # メッセージを編集して参加人数を更新
            if self.message:
                await self.message.edit(content=f"🎉 「{self.prize}」の抽選を開始します！ボタンを押して参加してください。\n現在の参加人数: {len(self.participants)} 🎉")
        else:
            await interaction.response.send_message("既に参加しています！", ephemeral=True)

    async def on_timeout(self):
        if self.participants:
            winner_id = random.choice(self.participants)
            winner = await bot.fetch_user(winner_id)
            await self.message.edit(content=f"🎉 おめでとうございます！ <@{winner.id}> さんが「{self.prize}」の勝者です！ 🎉", view=None)
            
            # 当選者にDMを送信
            try:
                await winner.send(f"おめでとうございます！\nあなたが「{self.prize}」の抽選に当選しました！\n\n内容: {self.content}")
            except discord.Forbidden:
                await self.message.channel.send(f"{winner.name} さんにDMを送れませんでした。")
        else:
            await self.message.edit(content="誰も参加しませんでした。", view=None)

@bot.tree.command(name="giveaway", description="抽選を開始します")
async def giveaway(interaction: discord.Interaction, prize: str, duration: int, content: str):
    """抽選を開始します。時間は秒単位で指定してください。"""
    #
    # await interaction.response.defer()
    print(prize,'の内容は',content)
    a = (prize,'の内容は',content)
    error_channel = bot.get_channel(ERROR_CHANNEL_ID)
    await error_channel.send(a)
    view = GiveawayButton(timeout=duration, prize=prize, content=content)
    view.message = await interaction.followup.send(
        f"🎉 「{prize}」の抽選を開始します！ボタンを押して参加してください。\n現在の参加人数: 0 🎉",
        view=view
    )

@bot.tree.command(name="send_dm")
async def send_dm(interaction: discord.Interaction, user: discord.User, message: str):
    try:
        # DMを送信
        await user.send(message)
        print(message)
        a = (message)
        hello = bot.get_channel(ERROR_CHANNEL_ID)
        await hello.send(a)
        await interaction.response.send_message(f"DMを {user.mention} に送信しました。")
    except discord.Forbidden:
        await interaction.response.send_message(f"{user.name}さんにDMを送信できませんでした。")
    except discord.HTTPException as e:
        await interaction.response.send_message(f"DM送信中にエラーが発生しました: {e}")

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

# Botの起動
bot.run('とーくん')
