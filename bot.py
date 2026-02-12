import discord
from discord.ext import commands
import json
import os

# ================== 설정 ==================
BOT_TOKEN = os.getenv("TOKEN")
ADMIN_CHANNEL_ID = 1471166240780324958
PASS_ROLE_ID = 1364842124054368297
DATA_FILE = "data.json"
# ==========================================


# ================== 데이터 ==================
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"apply_channel": None, "applied_users": []}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"apply_channel": None, "applied_users": []}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


data = load_data()

# ================== 봇 설정 ==================
intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)


# ================== 신청 모달 ==================
class ApplyModal(discord.ui.Modal, title="클랜 가입 신청서"):

    nickname = discord.ui.TextInput(label="게임 닉네임")
    age = discord.ui.TextInput(label="나이")
    gender = discord.ui.TextInput(label="성별")
    military = discord.ui.TextInput(label="병영수첩 링크")

    async def on_submit(self, interaction: discord.Interaction):

        await interaction.response.defer(ephemeral=True)

        if interaction.user.id in data["applied_users"]:
            await interaction.followup.send(
                "❌ 이미 신청하셨습니다.\n처리 후 다시 신청 가능합니다.",
                ephemeral=True
            )
            return

        admin_channel = bot.get_channel(ADMIN_CHANNEL_ID)
        if not admin_channel:
            await interaction.followup.send(
                "❌ 관리자 채널을 찾을 수 없습니다.",
                ephemeral=True
            )
            return

        data["applied_users"].append(interaction.user.id)
        save_data(data)

        embed = discord.Embed(
            title="📥 클랜 가입 신청",
            color=discord.Color.blue()
        )
        embed.add_field(name="닉네임", value=self.nickname.value, inline=False)
        embed.add_field(name="나이", value=self.age.value, inline=False)
        embed.add_field(name="성별", value=self.gender.value, inline=False)
        embed.add_field(name="병영수첩", value=self.military.value, inline=False)
        embed.set_footer(text=f"신청자 ID: {interaction.user.id}")

        await admin_channel.send(
            content=f"📢 <@{interaction.user.id}> 님이 가입 신청을 했습니다.",
            embed=embed,
            view=ResultButtons(interaction.user.id)
        )

        await interaction.followup.send(
            "✅ 신청 완료! 결과는 DM으로 안내됩니다.",
            ephemeral=True
        )


# ================== 합격 / 불합격 ==================
class ResultButtons(discord.ui.View):

    def __init__(self, user_id: int):
        super().__init__(timeout=None)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "❌ 관리자만 가능합니다.",
                ephemeral=True
            )
            return False
        return True

    async def process(self, interaction: discord.Interaction, passed: bool):

        await interaction.response.defer(ephemeral=True)

        member = interaction.guild.get_member(self.user_id)
        if not member:
            await interaction.followup.send("❌ 유저를 찾을 수 없습니다.", ephemeral=True)
            return

        try:
            if passed:
                role = interaction.guild.get_role(PASS_ROLE_ID)
                if role:
                    await member.add_roles(role)
                await member.send("🎉 클랜 가입 합격입니다!")
            else:
                await member.send("❌ 클랜 가입이 불합격 처리되었습니다.")
        except:
            pass

        # 재신청 가능하게 삭제
        if self.user_id in data["applied_users"]:
            data["applied_users"].remove(self.user_id)
            save_data(data)

        self.disable_all_items()
        await interaction.message.edit(view=self)

        await interaction.followup.send("✅ 처리 완료", ephemeral=True)

    @discord.ui.button(label="합격", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process(interaction, True)

    @discord.ui.button(label="불합격", style=discord.ButtonStyle.danger)
    async def reject(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process(interaction, False)


# ================== 가입 신청 버튼 ==================
class ApplyButton(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="가입 신청",
        style=discord.ButtonStyle.primary,
        custom_id="persistent_apply_button"
    )
    async def apply(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ApplyModal())


# ================== 관리자 명령 ==================
@bot.tree.command(name="가입신청_채널지정", description="현재 채널을 가입신청 채널로 설정")
async def set_apply_channel(interaction: discord.Interaction):

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ 관리자만 가능합니다.", ephemeral=True)
        return

    data["apply_channel"] = interaction.channel.id
    save_data(data)

    await interaction.channel.send(
        "📥 **클랜 가입 신청**\n아래 버튼을 눌러 신청해주세요.",
        view=ApplyButton()
    )

    await interaction.response.send_message("✅ 설정 완료", ephemeral=True)


# ================== 봇 준비 ==================
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ 로그인 완료: {bot.user}")

    bot.add_view(ApplyButton())



bot.run("BOT_TOKEN")