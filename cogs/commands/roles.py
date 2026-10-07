import discord
from discord import Embed, ButtonStyle
from discord.ui import Button, View
from discord.ext import commands
from utils.Tools import *


class RolesPaginator(View):
    def __init__(self, ctx, roles_data, per_page=10):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.roles_data = roles_data
        self.per_page = per_page
        self.page = 0
        self.total_pages = max(1, (len(roles_data) + per_page - 1) // per_page)
        self.message = None
        self.update_buttons()

    def update_buttons(self):
        self.first_btn.disabled = self.page == 0
        self.prev_btn.disabled = self.page == 0
        self.next_btn.disabled = self.page >= self.total_pages - 1
        self.last_btn.disabled = self.page >= self.total_pages - 1

    def build_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        chunk = self.roles_data[start:end]

        embed = Embed(
            title="▸ SERVER ROLES",
            color=0x1E40AF,
            description=f"Total: **{len(self.roles_data)}** roles",
        )

        lines = []
        for role in chunk:
            count = len(role.members)
            lines.append(f"✦ {role.mention} — **{count}** member{'s' if count != 1 else ''}")

        embed.add_field(name=f"Page {self.page + 1}/{self.total_pages}", value="\n".join(lines), inline=False)
        embed.set_footer(text=f"SHEET {self.page + 1}/{self.total_pages} · admin ✦ rev. 01")
        return embed

    async def interaction_check(self, interaction):
        if interaction.user != self.ctx.author:
            await interaction.response.send_message("Only the command author can use these buttons.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    @discord.ui.button(label="⏪", style=ButtonStyle.secondary)
    async def first_btn(self, interaction, button):
        self.page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="◀️", style=ButtonStyle.secondary)
    async def prev_btn(self, interaction, button):
        self.page = max(0, self.page - 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="▶️", style=ButtonStyle.secondary)
    async def next_btn(self, interaction, button):
        self.page = min(self.total_pages - 1, self.page + 1)
        self.update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    @discord.ui.button(label="⏩", style=ButtonStyle.secondary)
    async def last_btn(self, interaction, button):
        self.page = self.total_pages - 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)


class Roles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.color = 0x1E40AF

    @commands.hybrid_command(
        name="roles",
        aliases=["serverroles", "allroles", "rl"],
        help="List all roles in the server with member counts."
    )
    @blacklist_check()
    @ignore_check()
    @commands.cooldown(1, 7, commands.BucketType.user)
    @commands.guild_only()
    async def roles(self, ctx):
        try:
            roles = [r for r in ctx.guild.roles if r.name != "@everyone"]
            roles.sort(key=lambda r: r.position, reverse=True)

            if not roles:
                embed = Embed(title="▸ SERVER ROLES", description="This server has no roles.", color=self.color)
                embed.set_footer(text="SHEET 1/1 · admin ✦ rev. 01")
                return await ctx.reply(embed=embed)

            # Few roles → single embed
            if len(roles) <= 15:
                embed = Embed(title="▸ SERVER ROLES", color=self.color, description=f"Total: **{len(roles)}** roles")
                lines = [f"✦ {r.mention} — **{len(r.members)}** member{'s' if len(r.members) != 1 else ''}" for r in roles]
                value = "\n".join(lines)[:1024]
                embed.add_field(name="Roles", value=value, inline=False)
                embed.set_footer(text="SHEET 1/1 · admin ✦ rev. 01")
                return await ctx.reply(embed=embed)

            # Many roles → paginated
            view = RolesPaginator(ctx, roles, per_page=10)
            msg = await ctx.reply(embed=view.build_embed(), view=view)
            view.message = msg

        except Exception as e:
            import traceback
            traceback.print_exc()
            await ctx.reply(f"⚠️ Error: `{type(e).__name__}: {e}`")


async def setup(bot):
    await bot.add_cog(Roles(bot))
