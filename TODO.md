## [2.0.0] Harder, Better, Faster, Stronger

### Polishing
- přesunout volání databázových funkcí z `ui.py` do `game.py` u všech mini-her
- přidat do všech views metodu `build_embed` a `update_embed`, která vytvoří základní embed
- zastavit timeout timery v `Trivia` a `Tic-Tac-Toe` zavoláním self.stop na konci hry
- odstranit `/announcement` command
- přejmenovat `utils` modul na `info`
- přebarvit `/info` command na barvu `teal`
- FIX: zmenšit počet Trivia API requestů
- vylepšit vzhled informačních zpráv (reakce na hru cizího hráče a další ephemeral zprávy)
- přidat skripty setup.sh a setup.ps1 pro nastavení ENV proměnných
- aktualizovat README - přidat zmínku o existujících skriptech a co dělají, zjednodušit setup a zmínit adminer
- přidat chybějící testy pro moduly: Wordle, Trivia a Shared + zkontrolovat testy pro Tic-Tac-Toe a Wordle
- přidat příkaz `/web` nebo `/website`, který bude odkazovat na mojí webovou stránku `strachy.win`

### Better Console Logs

- logovat zprávy přímo do databáze
- přidat možnosti pro vypnutí logování do databáze, vypnutí vypisování logů do konzole, nastavení log levelu (debug, info, success, atd.) - přidat ke každé zprávě parametr "module" (ten bude značit, ke kterému modulu zpráva patří)
- přidat více info a debug logů ke stávajícím modulům
- zlepšit error handling (pomocí override 'on_error' metod v custom button a view třídách)

--

## [2.1.0] Česká lokalizace

- vytvořit české varianty dostupných her a ostatních funkcí jako samostatné příkazy (trivia -> kvíz, wordle -> hádej slovo, tic-tac-toe -> piškvorky, info -> informace)
- tyto české varianty budou sdílet herní logiku a UI, jenom budou mít jiné texty
- kvíz bude mít otázky týkající se české republiky
- hádej slovo bude obsahovat slova místo anglických

--

## [2.2.0] Web API

https://share.gemini.google/prmBNFuzUWzR
https://share.gemini.google/WblCzbkuTEP8

- přidat volitelný API bridge (přes aiohttp.web nebo FastAPI), který zprostředkuje backend API bota a bude posílat JSON payload, ve kterém budou informace o UI (embedy, views, atd.)
- do projektu `strachy.win` přidat stránku používající @derockdev/discord-components-react knihovnu s chatovacím oknem, ve kterém se zobrazí UI bota a bude možné používat jeho commandy
- do projektu `strachy.win` navíc přidat stránky pro minihry s vlastním webovým rozhraním, které bude používat `StrachBot` (python) backend

--

## [2.3.0] Uživatelské statistiky

--

## Nové mini-hry
- Songless
- Sudoku
- Šachy
- Lodě
- Blackjack
- Poker
- Kámen-nůžky-papír(-spock-lizard)
