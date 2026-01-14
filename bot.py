import discord
from discord.ext import commands
import json
import os
import asyncio
import random
import time

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

COIN_NAME = "TEXcoin"
COIN_EMOJI = "☢️"

ROLE_IDS = {
    "☢️!TEXUZ!☢️": 0,
    "Текстурик🟪⬛": 0,
    "The owner of the backrooms": 0
}

users_data = {}
active_sessions = {}

def load_data():
    global users_data
    try:
        with open('users_data.json', 'r', encoding='utf-8') as f:
            users_data = json.load(f)
    except FileNotFoundError:
        users_data = {}
        print("✅ Файл данных создан")

def save_data():
    with open('users_data.json', 'w', encoding='utf-8') as f:
        json.dump(users_data, f, indent=4, ensure_ascii=False)

async def auto_save():
    while True:
        await asyncio.sleep(300)
        save_data()
        print("💾 Автосохранение")

RANKS = {
    0: "Медь",
    500: "Медь II",
    1000: "Железо",
    1500: "Железо II",
    2000: "Свинец",
    2500: "Свинец II",
    3000: "Золото",
    4000: "Золото II",
    5000: "Алмаз",
    6000: "Алмаз II",
    7500: "Бриллиант",
    10000: "Бриллиант II",
    12500: "Мега",
    15000: "Мега II",
    17500: "Супер Мега",
    20000: "Титан",
    22500: "Олигарх",
    500000: "Владелец закусья",
    750000: "Микро текстурик",
    1000000: "☢️!TEXUZ!☢️"
}

def get_user_rank(taps):
    current_rank = "Медь"
    sorted_thresholds = sorted(RANKS.items())
    
    for threshold, rank in sorted_thresholds:
        if taps >= threshold:
            current_rank = rank
        else:
            break
    return current_rank

def calculate_upgrade_cost(current_level):
    """Расчет стоимости улучшения в зависимости от уровня"""
    if current_level < 10:
        return 1000  # +1000 за уровень для 1-10
    elif current_level < 20:
        return 3000  # +3000 за уровень для 11-20
    elif current_level < 30:
        return 7000  # +7000 за уровень для 21-30
    elif current_level < 50:
        return 25000  # +25000 за уровень для 31-50
    else:
        return 40000  # +40000 за уровень для 51-100

def calculate_tap_increase(current_level):
    """Расчет увеличения тапа в зависимости от уровня"""
    if current_level < 10:
        return 10  # +10 за уровень для 1-10
    elif current_level < 20:
        return 50  # +50 за уровень для 11-20
    elif current_level < 30:
        return 100  # +100 за уровень для 21-30
    elif current_level < 50:
        return 250  # +250 за уровень для 31-50
    else:
        return 500  # +500 за уровень для 51-100

def get_tap_power_from_level(level):
    """Получить силу тапа на основе уровня"""
    base_power = 10  # Начальная сила тапа
    
    # 1-10 уровень: 10 + (уровень-1)*10
    if level <= 10:
        return base_power + (level - 1) * 10
    
    # 11-20 уровень: 100 + (уровень-10)*50
    elif level <= 20:
        level_10_power = base_power + 9 * 10  # 10 + 90 = 100
        return level_10_power + (level - 10) * 50
    
    # 21-30 уровень: 600 + (уровень-20)*100
    elif level <= 30:
        level_20_power = 100 + 10 * 50  # 100 + 500 = 600
        return level_20_power + (level - 20) * 100
    
    # 31-50 уровень: 1600 + (уровень-30)*250
    elif level <= 50:
        level_30_power = 600 + 10 * 100  # 600 + 1000 = 1600
        return level_30_power + (level - 30) * 250
    
    # 51-100 уровень: 6600 + (уровень-50)*500
    else:
        level_50_power = 1600 + 20 * 250  # 1600 + 5000 = 6600
        return level_50_power + (level - 50) * 500

def init_user_data(user_id, username):
    user_id_str = str(user_id)
    if user_id_str not in users_data:
        users_data[user_id_str] = {
            'taps': 0,
            'level': 1,  # Начинаем с 1 уровня
            'tap_power': 10,  # Начальная сила тапа 10
            'coins': 0,
            'role': 'Новичок',
            'username': username,
            'total_coins_earned': 0,
            'total_taps': 0,
            'last_prize_time': 0,
            'upgrade_cost': 1000  # Начальная стоимость улучшения
        }
        save_data()
        return True
    return False

async def give_discord_role(member, role_name):
    if role_name in ROLE_IDS and ROLE_IDS[role_name] != 0:
        try:
            role = member.guild.get_role(ROLE_IDS[role_name])
            if role:
                await member.add_roles(role)
                return True
        except Exception as e:
            print(f"❌ Ошибка выдачи роли: {e}")
    return False

class PersonalClickerView(discord.ui.View):
    def __init__(self, owner_id, message_id):
        super().__init__(timeout=None)
        self.owner_id = str(owner_id)
        self.message_id = message_id
        active_sessions[self.owner_id] = message_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) != self.owner_id:
            await interaction.response.send_message(
                f"❌ Это не ваш кликер!\nСоздайте свой командой `!текстап`",
                ephemeral=True
            )
            return False
        return True
    
    @discord.ui.button(label="Тап!", style=discord.ButtonStyle.primary, emoji="👆", row=0)
    async def tap_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = str(interaction.user.id)
        
        init_user_data(interaction.user.id, interaction.user.name)
        
        tap_power = users_data[user_id]['tap_power']
        earned_coins = tap_power
        
        users_data[user_id]['taps'] += 1
        users_data[user_id]['coins'] += earned_coins
        users_data[user_id]['total_taps'] += 1
        users_data[user_id]['total_coins_earned'] += earned_coins
        
        save_data()
        
        current_rank = get_user_rank(users_data[user_id]['taps'])
        if users_data[user_id].get('last_rank') != current_rank:
            users_data[user_id]['last_rank'] = current_rank
            await interaction.response.send_message(
                f"💥 **БАМ!** +{earned_coins} {COIN_EMOJI}\n"
                f"💰 **Баланс:** {users_data[user_id]['coins']:,} {COIN_EMOJI}\n"
                f"🎉 **Новый ранг:** {current_rank}!",
                ephemeral=True,
                delete_after=3
            )
        else:
            await interaction.response.send_message(
                f"💥 **БАМ!** +{earned_coins} {COIN_EMOJI}\n"
                f"💰 **Баланс:** {users_data[user_id]['coins']:,} {COIN_EMOJI}",
                ephemeral=True,
                delete_after=2
            )
    
    @discord.ui.button(label="Меню", style=discord.ButtonStyle.secondary, emoji="📋", row=0)
    async def menu_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PersonalMenuView(self.owner_id, self.message_id)
        
        user_id = self.owner_id
        current_level = users_data[user_id]['level']
        next_cost = calculate_upgrade_cost(current_level)
        
        embed = discord.Embed(
            title=f"📱 Меню {COIN_NAME}",
            description=f"Добро пожаловать, {interaction.user.mention}!",
            color=discord.Color.blurple()
        )
        embed.add_field(name=f"{COIN_EMOJI} Баланс", value=f"**{users_data[user_id]['coins']:,}** {COIN_NAME}", inline=True)
        embed.add_field(name="⚡ Уровень тапа", value=f"**{current_level}**", inline=True)
        embed.add_field(name="💪 Сила тапа", value=f"**{users_data[user_id]['tap_power']:,}** {COIN_EMOJI}/клик", inline=True)
        embed.add_field(name="💰 След. улучшение", value=f"**{next_cost:,}** {COIN_EMOJI}", inline=True)
        embed.add_field(name="🏆 Ранг", value=f"**{get_user_rank(users_data[user_id]['taps'])}**", inline=True)
        
        await interaction.response.edit_message(embed=embed, view=view)

class PersonalMenuView(discord.ui.View):
    def __init__(self, owner_id, message_id):
        super().__init__(timeout=120)
        self.owner_id = str(owner_id)
        self.message_id = message_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) != self.owner_id:
            await interaction.response.send_message("❌ Это меню не для вас!", ephemeral=True)
            return False
        return True
    
    @discord.ui.button(label="Улучшить тап ⚡", style=discord.ButtonStyle.primary, emoji="⚡", row=0)
    async def upgrade_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = self.owner_id
        current_level = users_data[user_id]['level']
        
        # Максимальный уровень 100
        if current_level >= 100:
            embed = discord.Embed(
                title="🎖️ Максимальный уровень!",
                description="Вы достигли максимального 100 уровня!",
                color=discord.Color.gold()
            )
            await interaction.response.edit_message(embed=embed, view=self)
            return
        
        cost = calculate_upgrade_cost(current_level)
        tap_increase = calculate_tap_increase(current_level)
        
        if users_data[user_id]['coins'] >= cost:
            users_data[user_id]['coins'] -= cost
            users_data[user_id]['level'] += 1
            users_data[user_id]['tap_power'] += tap_increase
            save_data()
            
            new_level = users_data[user_id]['level']
            next_cost = calculate_upgrade_cost(new_level)
            next_increase = calculate_tap_increase(new_level)
            
            embed = discord.Embed(title="✅ Улучшение куплено!", color=discord.Color.green())
            embed.add_field(name="🎯 Новый уровень", value=f"**{new_level}**", inline=True)
            embed.add_field(name="⚡ Новая сила тапа", value=f"**{users_data[user_id]['tap_power']:,}** {COIN_EMOJI}/клик", inline=True)
            embed.add_field(name="💸 Потрачено", value=f"**{cost:,}** {COIN_EMOJI}", inline=True)
            embed.add_field(name="⬆️ Увеличение", value=f"**+{tap_increase:,}** к силе тапа", inline=True)
            embed.add_field(name="💰 Осталось", value=f"**{users_data[user_id]['coins']:,}** {COIN_EMOJI}", inline=True)
            
            # Если не максимальный уровень, показываем следующее улучшение
            if new_level < 100:
                embed.add_field(name="🎯 Следующее улучшение", value=f"Уровень **{new_level + 1}**: **{next_cost:,}** {COIN_EMOJI} (+{next_increase:,})", inline=False)
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            embed = discord.Embed(title="❌ Недостаточно средств", color=discord.Color.red())
            embed.add_field(name="Нужно", value=f"**{cost:,}** {COIN_EMOJI}", inline=True)
            embed.add_field(name="У вас", value=f"**{users_data[user_id]['coins']:,}** {COIN_EMOJI}", inline=True)
            embed.add_field(name="Не хватает", value=f"**{cost - users_data[user_id]['coins']:,}** {COIN_EMOJI}", inline=True)
            
            await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Магазин ролей 👑", style=discord.ButtonStyle.success, emoji="👑", row=0)
    async def roles_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = RoleShopView(self.owner_id, self.message_id)
        
        embed = discord.Embed(
            title="👑 МАГАЗИН ЭЛИТНЫХ РОЛЕЙ",
            description=f"Купите роль за {COIN_EMOJI} {COIN_NAME}\n*Роли выдаются на Discord сервере*",
            color=discord.Color.gold()
        )
        
        embed.add_field(name="👁️ The owner of the backrooms", value="**500,000** ☢️", inline=True)
        embed.add_field(name="🟪⬛ Текстурик", value="**750,000** ☢️", inline=True)
        embed.add_field(name=f"☢️ !TEXUZ! ☢️", value="**1,000,000** ☢️", inline=True)
        
        embed.set_footer(text="При покупке роль будет отображаться в вашем профиле")
        
        await interaction.response.edit_message(embed=embed, view=view)
    
    @discord.ui.button(label="Статистика 📊", style=discord.ButtonStyle.secondary, emoji="📊", row=1)
    async def stats_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = self.owner_id
        data = users_data[user_id]
        taps = data['taps']
        current_level = data['level']
        
        embed = discord.Embed(title=f"📊 Статистика {interaction.user.name}", color=discord.Color.blue())
        
        embed.add_field(name=f"{COIN_EMOJI} Баланс", value=f"**{data['coins']:,}** {COIN_NAME}", inline=True)
        embed.add_field(name="👆 Всего тапов", value=f"**{data['total_taps']:,}**", inline=True)
        embed.add_field(name="⚡ Уровень тапа", value=f"**{current_level}**", inline=True)
        embed.add_field(name="💪 Сила тапа", value=f"**{data['tap_power']:,}** {COIN_EMOJI}/клик", inline=True)
        embed.add_field(name="💰 Всего заработано", value=f"**{data['total_coins_earned']:,}** {COIN_NAME}", inline=True)
        embed.add_field(name="👑 Роль", value=f"**{data['role']}**", inline=True)
        
        # Ранг
        current_rank = get_user_rank(taps)
        embed.add_field(name="🏆 Текущий ранг", value=f"**{current_rank}**", inline=True)
        
        # Следующий ранг
        sorted_ranks = sorted(RANKS.items())
        next_rank = None
        next_threshold = None
        
        for i, (threshold, rank) in enumerate(sorted_ranks):
            if taps < threshold:
                next_threshold = threshold
                next_rank = rank
                break
        
        if next_rank:
            needed = next_threshold - taps
            progress = min(100, int((taps / next_threshold) * 100)) if next_threshold > 0 else 0
            progress_bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))
            
            embed.add_field(
                name="🎯 До следующего ранга",
                value=f"**{next_rank}**\n{progress_bar} {progress}%\nОсталось: **{needed:,}** тапов",
                inline=False
            )
        
        # Информация об улучшениях
        if current_level < 100:
            next_cost = calculate_upgrade_cost(current_level)
            next_increase = calculate_tap_increase(current_level)
            
            embed.add_field(
                name="⚡ Следующее улучшение",
                value=f"Уровень **{current_level + 1}**\nСтоимость: **{next_cost:,}** {COIN_EMOJI}\nУвеличение: **+{next_increase:,}** к силе тапа",
                inline=False
            )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Рейтинг 🏆", style=discord.ButtonStyle.secondary, emoji="🏆", row=1)
    async def rating_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not users_data:
            embed = discord.Embed(title="🏆 Рейтинг", description="Пока никто не играет 😢", color=discord.Color.light_gray())
            await interaction.response.edit_message(embed=embed, view=self)
            return
        
        # Топ по тапам
        top_by_taps = sorted(users_data.items(), key=lambda x: x[1].get('taps', 0), reverse=True)[:10]
        
        embed = discord.Embed(title=f"🏆 ТОП-10 ИГРОКОВ ({COIN_NAME})", color=discord.Color.gold())
        
        taps_text = ""
        for i, (uid, data) in enumerate(top_by_taps, 1):
            username = data.get('username', f'Игрок {uid[:6]}')
            taps = data.get('taps', 0)
            rank = get_user_rank(taps)
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
            taps_text += f"{medal} **{username}** - {taps:,} тапов ({rank})\n"
        
        embed.add_field(name="👆 ТОП ПО ТАПАМ", value=taps_text[:1024] or "Нет данных", inline=False)
        
        # Позиция текущего пользователя
        user_id = self.owner_id
        if user_id in users_data:
            all_users_taps = sorted(users_data.items(), key=lambda x: x[1].get('taps', 0), reverse=True)
            user_position_taps = next((i+1 for i, (uid, _) in enumerate(all_users_taps) if uid == user_id), None)
            
            if user_position_taps:
                embed.add_field(
                    name="🎯 Ваша позиция",
                    value=f"**По тапам:** #{user_position_taps}\n"
                          f"**Тапы:** {users_data[user_id]['taps']:,}\n"
                          f"**Ранг:** {get_user_rank(users_data[user_id]['taps'])}",
                    inline=False
                )
        
        await interaction.response.edit_message(embed=embed, view=self)
    
    @discord.ui.button(label="Назад ↩️", style=discord.ButtonStyle.danger, emoji="↩️", row=1)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PersonalClickerView(self.owner_id, self.message_id)
        
        user_id = self.owner_id
        data = users_data.get(user_id, {})
        
        embed = discord.Embed(
            title=f"{COIN_NAME} Кликер",
            description=f"Владелец: {interaction.user.mention}",
            color=discord.Color.green()
        )
        
        if data:
            embed.add_field(name=f"{COIN_EMOJI} Баланс", value=f"**{data.get('coins', 0):,}** {COIN_NAME}", inline=True)
            embed.add_field(name="⚡ Уровень", value=f"**{data.get('level', 1)}**", inline=True)
            embed.add_field(name="💪 Сила тапа", value=f"**{data.get('tap_power', 10):,}** {COIN_EMOJI}/клик", inline=True)
            embed.add_field(name="👑 Роль", value=f"**{data.get('role', 'Новичок')}**", inline=True)
            embed.add_field(name="🏆 Ранг", value=f"**{get_user_rank(data.get('taps', 0))}**", inline=True)
            embed.add_field(name="👆 Тапы", value=f"**{data.get('taps', 0):,}**", inline=True)
            
            # Стоимость следующего улучшения
            if data.get('level', 1) < 100:
                next_cost = calculate_upgrade_cost(data.get('level', 1))
                embed.add_field(name="💰 След. улучшение", value=f"**{next_cost:,}** {COIN_EMOJI}", inline=False)
        
        embed.set_footer(text="Ваши коины сохраняются навсегда! 💾")
        
        await interaction.response.edit_message(embed=embed, view=view)

class RoleShopView(discord.ui.View):
    def __init__(self, owner_id, message_id):
        super().__init__(timeout=120)
        self.owner_id = str(owner_id)
        self.message_id = message_id
    
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) != self.owner_id:
            await interaction.response.send_message("❌ Это не ваш магазин!", ephemeral=True)
            return False
        return True
    
    # Только 3 элитные роли
    @discord.ui.button(label="The owner of the backrooms - 500,000 ☢️", style=discord.ButtonStyle.primary, row=0)
    async def elite1_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.buy_role(interaction, "The owner of the backrooms", 500000)
    
    @discord.ui.button(label="Текстурик - 750,000 ☢️", style=discord.ButtonStyle.primary, row=1)
    async def elite2_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.buy_role(interaction, "Текстурик🟪⬛", 750000)
    
    @discord.ui.button(label="!TEXUZ! - 1,000,000 ☢️", style=discord.ButtonStyle.danger, row=2)
    async def elite3_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.buy_role(interaction, "☢️!TEXUZ!☢️", 1000000)
    
    @discord.ui.button(label="Назад ↩️", style=discord.ButtonStyle.secondary, emoji="↩️", row=3)
    async def back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = PersonalMenuView(self.owner_id, self.message_id)
        embed = discord.Embed(title="📱 Меню", description="Возвращаемся в меню...", color=discord.Color.blurple())
        await interaction.response.edit_message(embed=embed, view=view)
    
    async def buy_role(self, interaction: discord.Interaction, role_name, cost):
        user_id = self.owner_id
        
        if users_data[user_id]['coins'] >= cost:
            users_data[user_id]['coins'] -= cost
            users_data[user_id]['role'] = role_name
            save_data()
            
            role_given = await give_discord_role(interaction.user, role_name)
            
            embed = discord.Embed(title="✅ Покупка успешна!", color=discord.Color.green())
            embed.add_field(name="Приобретено", value=f"**{role_name}**", inline=True)
            embed.add_field(name="Стоимость", value=f"**{cost:,}** {COIN_EMOJI}", inline=True)
            embed.add_field(name="Новый баланс", value=f"**{users_data[user_id]['coins']:,}** {COIN_EMOJI}", inline=True)
            
            if role_given:
                embed.add_field(name="🎮 Роль на сервере", value=f"Роль **{role_name}** выдана на Discord сервере!", inline=False)
            else:
                embed.add_field(name="ℹ️ Информация", value=f"Роль будет отображаться только в игре", inline=False)
            
            await interaction.response.edit_message(embed=embed, view=self)
        else:
            embed = discord.Embed(title="❌ Недостаточно средств!", color=discord.Color.red())
            embed.add_field(name="Нужно", value=f"**{cost:,}** {COIN_EMOJI}", inline=True)
            embed.add_field(name="У вас", value=f"**{users_data[user_id]['coins']:,}** {COIN_EMOJI}", inline=True)
            embed.add_field(name="Не хватает", value=f"**{cost - users_data[user_id]['coins']:,}** {COIN_EMOJI}", inline=True)
            
            await interaction.response.edit_message(embed=embed, view=self)

@bot.event
async def on_ready():
    print(f'✅ {COIN_NAME} Бот запущен!')
    print(f'🤖 Имя бота: {bot.user}')
    load_data()
    print(f'📊 Загружено {len(users_data)} игроков')
    
    bot.loop.create_task(auto_save())
    
    await bot.change_presence(
        activity=discord.Game(name=f"!текстап | {COIN_NAME}"),
        status=discord.Status.online
    )

# ========== КОМАНДЫ БОТА ==========

@bot.command(name='текстап')
async def tex_tap(ctx):
    user_id = str(ctx.author.id)
    
    is_new = init_user_data(ctx.author.id, ctx.author.name)
    
    if user_id in active_sessions:
        try:
            old_msg = await ctx.channel.fetch_message(active_sessions[user_id])
            await old_msg.delete()
        except:
            pass
    
    embed = discord.Embed(
        title=f"🎮 {COIN_NAME} Кликер",
        description=f"**Владелец:** {ctx.author.mention}\n*Только вы можете использовать эти кнопки!*",
        color=discord.Color.green()
    )
    
    data = users_data[user_id]
    current_rank = get_user_rank(data['taps'])
    next_cost = calculate_upgrade_cost(data['level'])
    
    embed.add_field(name=f"{COIN_EMOJI} Баланс", value=f"**{data['coins']:,}** {COIN_NAME}", inline=True)
    embed.add_field(name="⚡ Уровень", value=f"**{data['level']}**", inline=True)
    embed.add_field(name="💪 Сила тапа", value=f"**{data['tap_power']:,}** {COIN_EMOJI}/клик", inline=True)
    embed.add_field(name="👑 Роль", value=f"**{data['role']}**", inline=True)
    embed.add_field(name="🏆 Ранг", value=f"**{current_rank}**", inline=True)
    embed.add_field(name="💰 След. улучшение", value=f"**{next_cost:,}** {COIN_EMOJI}", inline=True)
    
    if is_new:
        embed.set_footer(text="🎉 Добро пожаловать! Начните с первого тапа!")
    else:
        embed.set_footer(text="Ваши коины сохранены! 💾")
    
    view = PersonalClickerView(user_id, None)
    message = await ctx.send(embed=embed, view=view)
    
    view.message_id = message.id
    active_sessions[user_id] = message.id

@bot.command(name='тексбаланс')
async def tex_balance(ctx, member: discord.Member = None):
    target = member or ctx.author
    user_id = str(target.id)
    
    if user_id not in users_data:
        if target == ctx.author:
            await ctx.send(f"❌ У вас еще нет {COIN_NAME}!\nИспользуйте `!текстап` чтобы начать!")
        else:
            await ctx.send(f"❌ У {target.mention} еще нет {COIN_NAME}!")
        return
    
    data = users_data[user_id]
    current_rank = get_user_rank(data['taps'])
    
    embed = discord.Embed(
        title=f"{COIN_EMOJI} Профиль {target.name}",
        color=discord.Color.gold()
    )
    
    embed.add_field(name=f"{COIN_EMOJI} Баланс", value=f"**{data['coins']:,}**", inline=True)
    embed.add_field(name="👆 Всего тапов", value=f"**{data['taps']:,}**", inline=True)
    embed.add_field(name="⚡ Уровень", value=f"**{data['level']}**", inline=True)
    embed.add_field(name="💪 Сила тапа", value=f"**{data['tap_power']:,}** {COIN_EMOJI}/клик", inline=True)
    embed.add_field(name="👑 Роль", value=f"**{data['role']}**", inline=True)
    embed.add_field(name="🏆 Ранг", value=f"**{current_rank}**", inline=True)
    
    # Следующий ранг
    sorted_ranks = sorted(RANKS.items())
    next_rank = None
    next_threshold = None
    
    for i, (threshold, rank) in enumerate(sorted_ranks):
        if data['taps'] < threshold:
            next_threshold = threshold
            next_rank = rank
            break
    
    if next_rank:
        needed = next_threshold - data['taps']
        progress = min(100, int((data['taps'] / next_threshold) * 100)) if next_threshold > 0 else 0
        progress_bar = "█" * (progress // 10) + "░" * (10 - (progress // 10))
        
        embed.add_field(
            name="🎯 До следующего ранга",
            value=f"**{next_rank}**\n{progress_bar} {progress}%\nОсталось: **{needed:,}** тапов",
            inline=False
        )
    
    # Следующее улучшение
    if data['level'] < 100:
        next_cost = calculate_upgrade_cost(data['level'])
        next_increase = calculate_tap_increase(data['level'])
        
        embed.add_field(
            name="⚡ Следующее улучшение",
            value=f"Уровень **{data['level'] + 1}**\nСтоимость: **{next_cost:,}** {COIN_EMOJI}\nУвеличение: **+{next_increase:,}**",
            inline=False
        )
    
    embed.set_thumbnail(url=target.avatar.url if target.avatar else target.default_avatar.url)
    await ctx.send(embed=embed)

@bot.command(name='текстоп')
async def tex_top(ctx):
    if not users_data:
        await ctx.send(f"❌ Никто еще не играет в {COIN_NAME}!")
        return
    
    top_players = sorted(users_data.items(), key=lambda x: x[1].get('taps', 0), reverse=True)[:10]
    
    embed = discord.Embed(
        title=f"🏆 ТОП-10 ИГРОКОВ {COIN_NAME}",
        description="По количеству тапов",
        color=discord.Color.gold()
    )
    
    for i, (uid, data) in enumerate(top_players, 1):
        username = data.get('username', f'Игрок {uid[:6]}')
        taps = data.get('taps', 0)
        rank = get_user_rank(taps)
        
        if i == 1: place = "🥇"
        elif i == 2: place = "🥈"
        elif i == 3: place = "🥉"
        else: place = f"#{i}"
        
        embed.add_field(
            name=f"{place} {username}",
            value=f"{taps:,} тапов | {rank}",
            inline=False
        )
    
    author_id = str(ctx.author.id)
    if author_id in users_data:
        all_players = sorted(users_data.items(), key=lambda x: x[1].get('taps', 0), reverse=True)
        author_position = next((i+1 for i, (uid, _) in enumerate(all_players) if uid == author_id), None)
        
        if author_position:
            author_taps = users_data[author_id]['taps']
            author_rank = get_user_rank(author_taps)
            embed.set_footer(text=f"Ваша позиция: #{author_position} | Тапы: {author_taps:,} | Ранг: {author_rank}")
    
    await ctx.send(embed=embed)

@bot.command(name='тексприз')
async def tex_prize(ctx):
    user_id = str(ctx.author.id)
    init_user_data(ctx.author.id, ctx.author.name)
    
    current_time = time.time()
    last_prize = users_data[user_id].get('last_prize_time', 0)
    
    if current_time - last_prize < 86400:
        hours_left = int((86400 - (current_time - last_prize)) / 3600)
        await ctx.send(f"⏳ Следующий приз через {hours_left} часов!")
        return
    
    prize = random.randint(50, 500)
    users_data[user_id]['coins'] += prize
    users_data[user_id]['last_prize_time'] = current_time
    save_data()
    
    await ctx.send(
        f"🎉 **Ежедневный приз!**\n"
        f"💰 Вы получили: **{prize}** {COIN_EMOJI}\n"
        f"💳 Новый баланс: **{users_data[user_id]['coins']:,}** {COIN_EMOJI}"
    )

@bot.command(name='тексперевод')
async def tex_transfer(ctx, member: discord.Member, amount: int):
    sender_id = str(ctx.author.id)
    receiver_id = str(member.id)
    
    if sender_id == receiver_id:
        await ctx.send("❌ Нельзя перевести самому себе!")
        return
    
    if amount <= 0:
        await ctx.send("❌ Сумма должна быть положительной!")
        return
    
    if sender_id not in users_data:
        await ctx.send(f"❌ У вас нет {COIN_NAME}!")
        return
    
    if users_data[sender_id]['coins'] < amount:
        await ctx.send(f"❌ Недостаточно {COIN_NAME}!")
        return
    
    init_user_data(member.id, member.name)
    
    users_data[sender_id]['coins'] -= amount
    users_data[receiver_id]['coins'] += amount
    save_data()
    
    await ctx.send(
        f"✅ **Успешный перевод!**\n"
        f"📤 От: {ctx.author.mention}\n"
        f"📥 Кому: {member.mention}\n"
        f"💰 Сумма: **{amount:,}** {COIN_EMOJI}\n"
        f"💳 Ваш новый баланс: **{users_data[sender_id]['coins']:,}** {COIN_EMOJI}"
    )

@bot.command(name='тексхелп')
async def tex_help(ctx):
    embed = discord.Embed(
        title=f"📚 {COIN_NAME} - СПИСОК КОМАНД",
        description=f"Играйте и зарабатывайте {COIN_EMOJI}!",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🎮 ОСНОВНЫЕ КОМАНДЫ",
        value="```\n"
              "!текстап - Создать персональный кликер\n"
              "!тексбаланс - Проверить баланс\n"
              "!текстоп - Топ-10 игроков\n"
              "!тексприз - Ежедневный приз (24ч)\n"
              "```",
        inline=False
    )
    
    embed.add_field(
        name="💸 СОЦИАЛЬНЫЕ КОМАНДЫ",
        value="```\n"
              "!тексперевод @игрок сумма - Перевести коины\n"
              "```",
        inline=False
    )
    
    embed.add_field(
        name="🎯 В ИГРЕ (КНОПКИ)",
        value="```\n"
              "Тап! - Заработать коины\n"
              "Меню - Открыть меню\n"
              "Улучшить тап - Увеличить уровень\n"
              "Магазин ролей - Купить элитную роль\n"
              "Статистика - Ваша статистика\n"
              "Рейтинг - Топ игроков\n"
              "```",
        inline=False
    )
    
    embed.add_field(
        name="⚡ СИСТЕМА УРОВНЕЙ",
        value="```\n"
              "1-10 уровень: +1000 ☢️, +10 силы\n"
              "11-20 уровень: +3000 ☢️, +50 силы\n"
              "21-30 уровень: +7000 ☢️, +100 силы\n"
              "31-50 уровень: +25000 ☢️, +250 силы\n"
              "51-100 уровень: +40000 ☢️, +500 силы\n"
              "Макс. уровень: 100\n"
              "```",
        inline=False
    )
    
    embed.add_field(
        name="🏆 СИСТЕМА РАНГОВ",
        value="```\n"
              "Ранг зависит от количества тапов\n"
              "Медь → Медь II → Железо → ...\n"
              "→ ☢️!TEXUZ!☢️ (1,000,000 тапов)\n"
              "```",
        inline=False
    )
    
    await ctx.send(embed=embed)

# ========== АДМИН КОМАНДЫ ==========

@bot.command(name='тексдай')
@commands.has_permissions(administrator=True)
async def tex_give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("❌ Количество должно быть положительным!")
        return
    
    user_id = str(member.id)
    init_user_data(member.id, member.name)
    
    users_data[user_id]['coins'] += amount
    save_data()
    
    await ctx.send(
        f"✅ {member.mention} получил **{amount:,}** {COIN_EMOJI}!\n"
        f"Новый баланс: **{users_data[user_id]['coins']:,}** {COIN_EMOJI}"
    )

@bot.command(name='тексдайуровень')
@commands.has_permissions(administrator=True)
async def tex_give_level(ctx, member: discord.Member, levels: int):
    if levels <= 0:
        await ctx.send("❌ Количество должно быть положительным!")
        return
    
    user_id = str(member.id)
    init_user_data(member.id, member.name)
    
    for _ in range(levels):
        if users_data[user_id]['level'] >= 100:
            break
        
        current_level = users_data[user_id]['level']
        tap_increase = calculate_tap_increase(current_level)
        
        users_data[user_id]['level'] += 1
        users_data[user_id]['tap_power'] += tap_increase
    
    save_data()
    
    await ctx.send(
        f"✅ {member.mention} получил **{levels}** уровней!\n"
        f"Новый уровень: **{users_data[user_id]['level']}**\n"
        f"Новая сила тапа: **{users_data[user_id]['tap_power']:,}** {COIN_EMOJI}/клик"
    )

@bot.command(name='тексрезет')
@commands.has_permissions(administrator=True)
async def tex_reset(ctx, member: discord.Member = None):
    if member:
        user_id = str(member.id)
        if user_id in users_data:
            del users_data[user_id]
            if user_id in active_sessions:
                del active_sessions[user_id]
            save_data()
            await ctx.send(f"✅ Данные {member.mention} сброшены!")
        else:
            await ctx.send(f"❌ У {member.mention} нет данных!")
    else:
        users_data.clear()
        active_sessions.clear()
        save_data()
        await ctx.send("✅ Все данные сброшены!")

# ========== ЗАПУСК БОТА ==========

if __name__ == "__main__":
    TOKEN = os.getenv('DISCORD_TOKEN')
    
    if not TOKEN:
        try:
            with open('token.txt', 'r') as f:
                TOKEN = f.read().strip()
        except FileNotFoundError:
            print("❌ Токен не найден!")
            print("1. Создайте файл token.txt")
            print("2. Вставьте туда токен бота")
            exit(1)
    
    print(f"🚀 Запуск {COIN_NAME} бота...")
    print(f"☢️  Валюта: {COIN_NAME} {COIN_EMOJI}")
    bot.run(TOKEN)
