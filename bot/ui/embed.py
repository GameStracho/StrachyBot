import discord

from .helpers import load_attachment


def update_field(embed: discord.Embed, name: str, value: str) -> None:
    for i, field in enumerate(embed.fields):
        if field.name == name:
            embed.set_field_at(index=i, name=name, value=value, inline=field.inline)
            return


def remove_field(embed: discord.Embed, name: str) -> None:
    for i, field in enumerate(embed.fields):
        if field.name == name:
            embed.remove_field(index=i)
            return


def extract(
    target: discord.Interaction | discord.Message, index: int, hide_icon: bool
) -> discord.Embed:
    message: discord.Message | None = None

    if isinstance(target, discord.Interaction):
        message = target.message
    else:
        message = target

    assert message is not None
    embed: discord.Embed = message.embeds[index]

    if hide_icon:
        # hide a second icon appearing above the embed
        embed.set_thumbnail(url="attachment://icon.png")

    return embed


def build_warning(message: str) -> tuple[discord.Embed, discord.File]:
    embed: discord.Embed = discord.Embed(
        title="Warning",
        color=discord.Color.yellow(),
        description=message,
    )

    icon, icon_url = load_attachment(path=__file__, filename="warning.png", sub_dir="../images")
    embed.set_thumbnail(url=icon_url)

    return (embed, icon)
