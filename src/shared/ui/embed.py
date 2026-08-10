import discord


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


def extract(interaction: discord.Interaction, index: int, hide_icon: bool) -> discord.Embed:
    message: discord.Message | None = interaction.message
    assert message is not None

    return extract_from_message(message=message, index=index, hide_icon=hide_icon)


def extract_from_message(message: discord.Message, index: int, hide_icon: bool) -> discord.Embed:
    embed: discord.Embed = message.embeds[index]

    if hide_icon:
        # hide a second icon appearing above the embed
        embed.set_thumbnail(url="attachment://icon.png")

    return embed
