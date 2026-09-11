import discord
import httpx
from typing_extensions import override

from shared import logger, models, types, ui
from shared.modules.__template__ import GameResponse


class View(discord.ui.View):
    _match_id: int
    _player_id: int
    _status: models.EMatchStatus
    _api_client: httpx.AsyncClient
    message: discord.Message

    def __init__(
        self,
        match_id: int,
        player_id: int,
        status: models.EMatchStatus,
        api_client: httpx.AsyncClient,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout)
        self._match_id = match_id
        self._player_id = player_id
        self._api_client = api_client
        self._status = status

        logger.debug(f"New View created for game {self._match_id} with {timeout}s timeout.")

        self.add_item(Button(parent_view=self))

    @property
    def match_id(self) -> int:
        return self._match_id

    def build_embed(self, player: types.User) -> tuple[discord.Embed, discord.File]:
        title: str = "Game"

        embed: discord.Embed = discord.Embed(title=title, color=discord.Color.blue())
        embed.set_author(name=player.display_name, icon_url=player.display_avatar)

        embed.add_field(name="Moves", value=0, inline=False)
        embed.add_field(name="Status", value="Game started.", inline=True)
        embed.add_field(name="Timeout", value=ui.get_timeout_timestamp(self), inline=True)

        icon, icon_url = ui.load_attachment(path=__file__, filename="icon.png")
        embed.set_thumbnail(url=icon_url)

        return (embed, icon)

    def update_embed(
        self, default_status: str | None = None, moves_count: int | None = None
    ) -> discord.Embed:
        embed: discord.Embed = ui.embed.extract(target=self.message, index=0, hide_icon=True)

        match self._status:
            case models.EMatchStatus.PENDING:
                if default_status:
                    ui.embed.update_field(embed=embed, name="Status", value=default_status)

                if moves_count:
                    ui.embed.update_field(embed=embed, name="Moves", value=str(moves_count))

                ui.embed.update_field(
                    embed=embed, name="Timeout", value=ui.get_timeout_timestamp(self)
                )
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
            case models.EMatchStatus.TIMEOUT:
                ui.embed.update_field(
                    embed=embed,
                    name="Status",
                    value=(f"Game timed out! {ui.EMOJIS['game_timeout']}"),
                )
            case _:
                raise ValueError(self._status)

        if self._status != models.EMatchStatus.PENDING:
            self.disable_buttons()
            ui.embed.remove_field(embed=embed, name="Timeout")
            self.stop()

        return embed

    def disable_buttons(self) -> None:
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        logger.debug(f"Buttons disabled for game {self._match_id}.")

    @override
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        try:
            if interaction.user.id != self._player_id:
                logger.warning(
                    f"Ineligible user {interaction.user.display_name} "
                    f"({interaction.user.id}) "
                    f"responded to game {self._match_id}."
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
        response = await self._api_client.patch(url=f"{self._match_id}/timeout")
        response.raise_for_status()

        self._status = models.EMatchStatus.TIMEOUT
        embed: discord.Embed = self.update_embed()
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
                f"pressed the 'Send modal' button for game {self._match_id}."
            )

            embed: discord.Embed = self.update_embed()
            await self.message.edit(embed=embed, view=self)

            modal: Modal = Modal(parent_view=self)
            await interaction.response.send_modal(modal)

            logger.debug(
                f"Modal for game {self._match_id} "
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
                    f"pressed the 'Give up' button for game {self._match_id}."
                )

                response = await self._api_client.patch(url=f"{self._match_id}/surrender")
                response.raise_for_status()

                self._status = models.EMatchStatus.SURRENDER
                embed: discord.Embed = self.update_embed()
                await self.message.edit(embed=embed, view=self)

            message_embed: discord.Embed = self.update_embed()
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

    @discord.ui.button(
        label="Move",
        style=discord.ButtonStyle.primary,
        emoji="♟️",
    )
    async def move_button(
        self, interaction: discord.Interaction, button: discord.ui.Button["View"]
    ) -> None:
        try:
            logger.debug(
                f"User {interaction.user.display_name} ({interaction.user.id}) "
                f"pressed the 'Move' button for game {self._match_id}."
            )

            response = await self._api_client.post(url=f"{self._match_id}/move")
            response.raise_for_status()
            game_data: GameResponse = GameResponse.model_validate(response.json())

            self._status = game_data.status
            embed: discord.Embed = self.update_embed(
                default_status="Move performed", moves_count=game_data.moves_count
            )
            await self.message.edit(embed=embed, view=self)

            logger.debug(
                f"Move #{game_data.moves_count} in game {self._match_id}"
                f"performed by User {interaction.user.display_name} ({interaction.user.id})."
            )

            await interaction.response.send_message(
                "Move performed.", ephemeral=True, delete_after=0
            )
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)


class Modal(discord.ui.Modal):
    _parent_view: View

    def __init__(self, parent_view: View):
        super().__init__(title="Template Modal")

        self._parent_view = parent_view
        logger.debug(f"New WordleGuessModal created for game {self._parent_view.match_id}.")

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

            self._parent_view.update_embed(default_status="Description updated.")
            await interaction.response.edit_message(embed=embed, view=self._parent_view)
            self._parent_view.message = await interaction.original_response()
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)


class Button(discord.ui.Button[View]):
    _parent_view: View

    def __init__(self, parent_view: View) -> None:
        super().__init__(label="Custom Button", emoji="⬛", style=discord.ButtonStyle.secondary)

        self._parent_view = parent_view

        logger.debug(f"New Button created for game {parent_view.match_id}.")

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
            self._parent_view.update_embed(default_status="Embed updated.")

            # Edit the original message to show disabled buttons
            await interaction.response.edit_message(embed=embed, view=self._parent_view)
        except Exception as error:
            await ui.handle_error(error=error, interaction=interaction)
