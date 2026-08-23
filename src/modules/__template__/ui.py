import discord
from typing_extensions import override

from shared import logger, models, types, ui

from .game import Game


class View(discord.ui.View):
    _game: Game
    message: discord.Message | None

    def __init__(self, game: Game, timeout: float = 180):
        super().__init__(timeout=timeout)
        self._game = game
        logger.debug(f"New View created for game {self._game.match_id} with {timeout}s timeout.")

        self.add_item(Button(parent_view=self))

    @property
    def game(self) -> Game:
        return self._game

    def build_embed(self) -> tuple[discord.Embed, discord.File]:
        title: str = "Game"
        user: types.User = self._game.player

        embed: discord.Embed = discord.Embed(title=title, color=discord.Color.blue())
        embed.set_author(name=user.display_name, icon_url=user.display_avatar)

        embed.add_field(name="Status", value="Game started.", inline=True)
        embed.add_field(name="Timeout", value=ui.get_timeout_timestamp(self), inline=True)

        icon, icon_url = ui.load_attachment(path=__file__, filename="icon.png")
        embed.set_thumbnail(url=icon_url)

        return (embed, icon)

    def update_embed(self, embed: discord.Embed, default_status: str) -> None:
        match self._game.status:
            case models.EMatchStatus.PENDING:
                ui.embed.update_field(embed=embed, name="Status", value=default_status)
                ui.embed.update_field(
                    embed=embed, name="Timeout", value=ui.get_timeout_timestamp(self)
                )
                return
            case models.EMatchStatus.WIN:
                embed.color = discord.Color.green()
                ui.embed.update_field(
                    embed=embed, name="Status", value="You won! " + ui.EMOJIS["game_win"]
                )
            case models.EMatchStatus.LOSS:
                embed.color = discord.Color.red()
                ui.embed.update_field(
                    embed=embed,
                    name="Status",
                    value=(f"You lost! {ui.EMOJIS['game_loss']}"),
                )
            case models.EMatchStatus.SURRENDER:
                embed.color = ui.COLORS["white"]
                ui.embed.update_field(
                    embed=embed,
                    name="Status",
                    value=(f"You gave up! {ui.EMOJIS['game_surrender']}"),
                )
            case _:
                raise ValueError(self._game.status)

        self.disable_buttons()
        ui.embed.remove_field(embed=embed, name="Timeout")
        self.stop()

    def disable_buttons(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        logger.debug(f"Buttons disabled for game {self._game.match_id}.")

    @override
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if interaction.user.id != self._game.player.id:
                logger.warning(
                    f"Ineligible user {interaction.user.display_name} "
                    f"({interaction.user.id}) "
                    f"responded to game {self._game.match_id}."
                )

                embed, icon = ui.embed.build_warning(message="You cannot respond to this game.")

                await interaction.response.send_message(embed=embed, file=icon, ephemeral=True)
                return False  # Aborts processing and DOES NOT reset/extend the view timeout

            return True  # Authorized click; allow execution
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
            return False

    @override
    async def on_timeout(self) -> None:
        if self._game.status != models.EMatchStatus.PENDING or self.message is None:
            return

        await self._game.handle_timeout()
        self.disable_buttons()

        embed: discord.Embed = ui.embed.extract(target=self.message, index=0, hide_icon=True)
        ui.embed.remove_field(embed=embed, name="Timeout")
        ui.embed.update_field(
            embed=embed,
            name="Status",
            value=(f"Game timed out! {ui.EMOJIS['game_timeout']}"),
        )

        # Edit the original message to show disabled buttons
        await self.message.edit(embed=embed, view=self)

    @discord.ui.button(
        label="Send modal",
        style=discord.ButtonStyle.primary,
        emoji="😉",
    )
    async def click_me_button(
        self, interaction: discord.Interaction, button: discord.ui.Button["View"]
    ) -> None:
        try:
            logger.debug(
                f"User {interaction.user.display_name} ({interaction.user.id}) "
                f"pressed the 'Send modal' button for game {self._game.match_id}."
            )

            assert self.message is not None
            embed: discord.Embed = ui.embed.extract(target=self.message, index=0, hide_icon=True)
            ui.embed.update_field(embed=embed, name="Timeout", value=ui.get_timeout_timestamp(self))
            await self.message.edit(embed=embed, view=self)

            modal: Modal = Modal(parent_view=self)
            await interaction.response.send_modal(modal)

            logger.debug(
                f"Modal for game {self._game.match_id} "
                f"sent to User {interaction.user.display_name} ({interaction.user.id})."
            )
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)

    @discord.ui.button(
        label="Give up", style=discord.ButtonStyle.secondary, emoji=ui.EMOJIS["game_surrender"]
    )
    async def give_up_button(
        self, interaction: discord.Interaction, button: discord.ui.Button["View"]
    ) -> None:
        try:

            async def handle_surrender(confirm_interaction: discord.Interaction) -> None:
                logger.debug(
                    f"User {confirm_interaction.user.display_name} "
                    f"({confirm_interaction.user.id}) "
                    f"pressed the 'Give up' button for game {self._game.match_id}."
                )

                assert self.message is not None
                embed: discord.Embed = ui.embed.extract(
                    target=self.message, index=0, hide_icon=True
                )

                await self._game.handle_surrender()
                self.update_embed(embed=embed, default_status="You gave up!")
                await self.message.edit(embed=embed, view=self)

            assert self.message is not None
            message_embed: discord.Embed = ui.embed.extract(
                target=self.message, index=0, hide_icon=True
            )
            ui.embed.update_field(
                embed=message_embed, name="Timeout", value=ui.get_timeout_timestamp(self)
            )
            await self.message.edit(embed=message_embed, view=self)

            timeout: float = min(self.timeout, 30.0) if self.timeout else 30.0
            confirm_view: ui.ConfirmView = ui.ConfirmView(
                interaction=interaction,
                on_confirm=handle_surrender,
                confirm_label="Yes",
                cancel_label="No",
                timeout=timeout,
            )
            confirm_embed, confirm_icon = confirm_view.build_embed(
                question="Are you sure you want to give up?"
            )

            await interaction.response.send_message(
                embed=confirm_embed, view=confirm_view, file=confirm_icon, ephemeral=True
            )
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)


class Modal(discord.ui.Modal):
    _parent_view: View

    def __init__(self, parent_view: View):
        super().__init__(title="Template Modal")

        self._parent_view = parent_view
        logger.debug(f"New WordleGuessModal created for game {self._parent_view.game.match_id}.")

    text_input: discord.ui.TextInput["Modal"] = discord.ui.TextInput(
        label="Text",
        style=discord.TextStyle.short,
        placeholder="Enter some text",
        min_length=5,
        max_length=20,
        required=True,
    )

    @override
    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            embed: discord.Embed = ui.embed.extract(target=interaction, index=0, hide_icon=True)
            embed.description = self.text_input.value

            self._parent_view.update_embed(embed=embed, default_status="Updated status.")
            await interaction.response.edit_message(embed=embed, view=self._parent_view)
            self._parent_view.message = await interaction.original_response()
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)


class Button(discord.ui.Button[View]):
    _parent_view: View

    def __init__(self, parent_view: View) -> None:
        super().__init__(label="Custom Button", emoji="⬛", style=discord.ButtonStyle.secondary)

        self._parent_view = parent_view

        logger.debug(f"New Button created for game {parent_view.game.match_id}.")

    @override
    async def callback(self, interaction: discord.Interaction) -> None:
        try:
            success: bool = False

            if not success:
                warning_embed, warning_icon = ui.embed.build_warning(message="Invalid move! ☹️")

                await interaction.response.send_message(
                    embed=warning_embed, file=warning_icon, ephemeral=True
                )
                return

            embed: discord.Embed = ui.embed.extract(target=interaction, index=0, hide_icon=True)
            self._parent_view.update_embed(embed=embed, default_status="Embed updated.")

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=self._parent_view)
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
