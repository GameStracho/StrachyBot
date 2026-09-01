from typing import Self

from pydantic import BaseModel, model_validator


class APIArtist(BaseModel):
    id: int
    name: str
    link: str
    picture: str
    picture_small: str
    picture_medium: str
    picture_big: str
    picture_xl: str
    tracklist: str
    type: str

    def __str__(self) -> str:
        return f"{self.name} ({self.id})"

    @model_validator(mode="after")
    def validate_type(self) -> Self:
        if self.type != "artist":
            raise ValueError(f"Invalid artist type '{self.type}'.")

        return self


class APIAlbum(BaseModel):
    id: int
    title: str
    upc: str
    cover: str
    cover_small: str | None = None
    cover_medium: str | None = None
    cover_big: str | None = None
    cover_xl: str | None = None
    md5_image: str
    tracklist: str
    type: str

    def __str__(self) -> str:
        return f"{self.title} ({self.id})"

    @model_validator(mode="after")
    def validate_type(self) -> Self:
        if self.type != "album":
            raise ValueError(f"Invalid album type '{self.type}'.")

        return self


class APISong(BaseModel):
    id: int
    readable: bool
    title: str
    title_short: str
    title_version: str | None = None
    isrc: str
    link: str
    duration: int
    rank: int
    explicit_lyrics: bool
    explicit_content_lyrics: int
    explicit_content_cover: int
    preview: str
    md5_image: str
    time_add: int
    artist: APIArtist
    album: APIAlbum
    type: str

    def __str__(self) -> str:
        return (
            f"(id = {self.id}, title = {self.title}, artist = {self.artist}, album = {self.album})"
        )

    @model_validator(mode="after")
    def validate_type(self) -> Self:
        if self.type != "track":
            raise ValueError(f"Invalid song type '{self.type}'.")

        return self


class APIResponse(BaseModel):
    data: list[APISong]
    checksum: str
    total: int
    next: str | None = None
    prev: str | None = None

    def __str__(self) -> str:
        return (
            f"data = {self.data}, checksum: {self.checksum}, total = {self.total}, "
            f"prev = {self.prev}, next = {self.next}"
        )
