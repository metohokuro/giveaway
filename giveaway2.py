import discord
from discord.ext import commands
import random
import datetime

# Intentsの設定
intents = discord.Intents.default()
intents.message_content = True
intents.dm_messages = True




# Botのセットアップ
bot = commands.Bot(command_prefix="!", intents=intents)

# 管理者専用のパスワード
ADMIN_PASSWORD = "ぱすわーど"  # ここに自分だけのパスワードを設定

class GiveawayButton(discord.ui.View):
    def __init__(self, end_time, prize, content, winners_count):
        super().__init__(timeout=None)  # タイムアウトを明示的に管理
        self.participants = []
        self.prize = prize
        self.content = content
        self.winners_count = winners_count
        self.end_time = end_time
        self.message = None  # メッセージを格納するための変数

    async def start_timer(self):
        # 現在時刻と終了時刻の差を計算し、タイマーを設定
        now = datetime.datetime.now()
        remaining_time = (self.end_time - now).total_seconds()
        await asyncio.sleep(remaining_time)
        await self.on_timeout()

    @discord.ui.button(label="参加", style=discord.ButtonStyle.primary)
    async def enter_giveaway(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in self.participants:
            self.participants.append(interaction.user.id)
            await interaction.response.send_message(f"{interaction.user.name} さんが参加しました！", ephemeral=True)
            
            # メッセージを編集して参加人数を更新
            if self.message:
                await self.message.edit(content=f"🎉 「{self.prize}」の抽選を開始します！ボタンを押して参加してください。\n現在の参加人数: {len(self.participants)} 🎉\n抽選終了時刻: {self.end_time.strftime('%H時%M分%S秒までです！')}")
        else:
            await interaction.response.send_message("既に参加しています！", ephemeral=True)

    async def on_timeout(self):
        if self.participants:
            winners = random.sample(self.participants, min(self.winners_count, len(self.participants)))
            winner_mentions = ', '.join(f"<@{winner_id}>" for winner_id in winners)
            await self.message.channel.send(f"🎉 おめでとうございます！ {winner_mentions} さんが「{self.prize}」の勝者です！ 🎉")
            
            # 当選者にDMを送信
            for winner_id in winners:
                winner = await bot.fetch_user(winner_id)
                try:
                    await winner.send(f"おめでとうございます！\nあなたが「{self.prize}」の抽選に当選しました！\n\n内容: {self.content}")
                except discord.Forbidden:
                    await self.message.channel.send(f"{winner.name} さんにDMを送れませんでした。")
        else:
            await self.message.channel.send("誰も参加しませんでした。")

@bot.tree.command(name="giveaway", description="抽選を開始します")
@discord.app_commands.describe(
    景品="景品を入力してください",
    制限時間="制限時間を分単位で入力してください",
    内容="DMに送る内容を入力してください",
    人数="当選者の人数を入力してください"
)
@discord.app_commands.checks.has_permissions(administrator=True)
async def giveaway(interaction: discord.Interaction, 景品: str, 制限時間: int, 内容: str, 人数: int):
    """抽選を開始します。"""
    await interaction.response.defer()
    
    # 分を秒に変換して終了時刻を計算
    end_time = datetime.datetime.now() + datetime.timedelta(minutes=制限時間)

    # 履歴をテキストファイルに書き込む
    with open("giveaway_history.txt", "a", encoding="utf-8") as file:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{now} - 景品: {景品}, 内容: {内容}\n")
    
    view = GiveawayButton(end_time=end_time, prize=景品, content=内容, winners_count=人数)
    view.message = await interaction.followup.send(
        f"🎉 「{景品}」の抽選を開始します！ボタンを押して参加してください。\n現在の参加人数: 0 🎉\n抽選終了時刻: {end_time.strftime('%H時%M分%S秒までです！')}",
        view=view
    )
    
    # タイマーを開始
    bot.loop.create_task(view.start_timer())

@giveaway.error
async def giveaway_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("管理者だけが実行できます。", ephemeral=True)
    else:
        await interaction.response.send_message("エラーが発生しました。", ephemeral=True)

@bot.tree.command(name="develop", description="開発者専用コマンドで履歴を送信")
@discord.app_commands.checks.has_permissions(administrator=True)
async def develop(interaction: discord.Interaction, パスワード: str):
    """開発者専用コマンド"""
    if パスワード == ADMIN_PASSWORD:
        try:
            # giveaway_history.txtを開いてDMで送信
            with open("giveaway_history.txt", "r", encoding="utf-8") as file:
                history_content = file.read()

            # DMで送信
            await interaction.user.send(f"Giveaway 履歴:\n{history_content}")
            await interaction.response.send_message("履歴をDMに送信しました！", ephemeral=True)

        except FileNotFoundError:
            await interaction.response.send_message("履歴ファイルが見つかりませんでした。", ephemeral=True)

    else:
        await interaction.response.send_message("パスワードが間違っています。", ephemeral=True)

@develop.error
async def develop_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("管理者だけが実行できます。", ephemeral=True)
    else:
        await interaction.response.send_message("エラーが発生しました。", ephemeral=True)
@bot.tree.command(name="senddm", description="指定したユーザーにDMを送信します")
@discord.app_commands.describe(
    user="DMを送信するユーザーを指定してください",
    message="送信するメッセージを入力してください"
)
@discord.app_commands.checks.has_permissions(administrator=True)
async def send_dm(interaction: discord.Interaction, user: discord.User, message: str):
    """指定したユーザーに商品配達をします。"""
    try:
        embed = discord.Embed(
            title="商品配達のおしらせ",
            description=message,
            color=discord.Color.blue())  # 色の設定
        await user.send(embed=embed)
        await interaction.response.send_message(f"{user.name} さんにメッセージを送信しました。", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("指定したユーザーにDMを送れませんでした。", ephemeral=True)

@send_dm.error
async def send_dm_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, discord.app_commands.MissingPermissions):
        await interaction.response.send_message("管理者だけが実行できます。", ephemeral=True)
    else:
        await interaction.response.send_message("エラーが発生しました。", ephemeral=True)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

# Botの起動
bot.run('とーくん')
