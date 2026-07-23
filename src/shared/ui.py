import discord

TIMEOUT_COLOR: discord.Color = discord.Color.darker_grey()
DRAW_COLOR: discord.Color = discord.Color.light_grey()


def update_embed_field(embed: discord.Embed, name: str, value: str) -> None:
    for i, field in enumerate(embed.fields):
        if field.name == name:
            embed.set_field_at(index=i, name=name, value=value, inline=field.inline)
            return
