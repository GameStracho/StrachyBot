import discord

from shared import console, messages
import modules.tic_tac_toe.view as view

class TicTacToeButton(discord.ui.Button["view.TicTacToeView"]):
    def __init__(self, game_id: int, row: int) -> None:
        super().__init__(label="⬛", style=discord.ButtonStyle.secondary, row=row)

        console.log_debug((
            f"/tic-tac-toe: New TicTacToeButton created for game {game_id}: "
            f"row = {row}."
        ))

    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            self.label = "⚪"
            self.disabled = True

            parent_view = self.view
            assert isinstance(parent_view, view.TicTacToeView)

            message: discord.Message | None = interaction.message
            assert message is not None

            embed: discord.Embed = message.embeds[0]

            # hide a second icon appearing above the embed
            embed.set_thumbnail(url="attachment://icon.png")

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=parent_view)
        except Exception:
            await messages.handle_error(command="/tic-tac-toe", interaction=interaction, use_followup=False)
