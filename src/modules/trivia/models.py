from enum import Enum as PyEnum

class ETriviaCategory(PyEnum):
    ANY = "Any"
    GENERAL_KNOWLEDGE = "General Knowledge"
    BOOKS = "Books"
    FILM = "Film"
    MUSIC = "Music"
    MUSICALS = "Musicals & Theaters"
    TELEVISION = "Television"
    VIDEO_GAMES = "Video Games"
    BOARD_GAMES = "Board Games"
    SCIENCE_NATURE = "Science & Nature"
    COMPUTERS = "Computers"
    MATHEMATICS = "Mathematics"
    MYTHOLOGY = "Mythology"
    SPORTS = "Sports"
    GEOGRAPHY = "Geography"
    HISTORY = "History"
    POLITICS = "Politics"
    ART = "Art"
    CELEBRITIES = "Celebrities"
    ANIMALS = "Animals"
    VEHICLES = "Vehicles"
    COMICS = "Comics"
    GADGETS = "Gadgets"
    ANIME_MANGA = "Anime & Manga"
    CARTOON_ANIMATION = "Cartoon & Animations"


    def __int__(self) -> int:
        match self:
            case ETriviaCategory.ANY:
                return 0
            case ETriviaCategory.GENERAL_KNOWLEDGE:
                return 9
            case ETriviaCategory.BOOKS:
                return 10
            case ETriviaCategory.FILM:
                return 11
            case ETriviaCategory.MUSIC:
                return 12
            case ETriviaCategory.MUSICALS:
                return 13
            case ETriviaCategory.TELEVISION:
                return 14
            case ETriviaCategory.VIDEO_GAMES:
                return 15
            case ETriviaCategory.BOARD_GAMES:
                return 16
            case ETriviaCategory.SCIENCE_NATURE:
                return 17
            case ETriviaCategory.COMPUTERS:
                return 18
            case ETriviaCategory.MATHEMATICS:
                return 19
            case ETriviaCategory.MYTHOLOGY:
                return 20
            case ETriviaCategory.SPORTS:
                return 21
            case ETriviaCategory.GEOGRAPHY:
                return 22
            case ETriviaCategory.HISTORY:
                return 23
            case ETriviaCategory.POLITICS:
                return 24
            case ETriviaCategory.ART:
                return 25
            case ETriviaCategory.CELEBRITIES:
                return 26
            case ETriviaCategory.ANIMALS:
                return 27
            case ETriviaCategory.VEHICLES:
                return 28
            case ETriviaCategory.COMICS:
                return 29
            case ETriviaCategory.GADGETS:
                return 30
            case ETriviaCategory.ANIME_MANGA:
                return 31
            case ETriviaCategory.CARTOON_ANIMATION:
                return 32
            case _:
                raise ValueError(f"No API integer code mapped for {self}")


class ETriviaDifficulty(PyEnum):
    ANY = "Any"
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"
