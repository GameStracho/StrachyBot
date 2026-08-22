## Songless

- přejmenovat atribut `match_id` v tabulce `match` na `id`
- automaticky aktualizovat všechny `PENDING` hry na `TIMEOUT` při vypínání bota
- Zachytit error s nedostupnou databází při startu bota, vypsat jednoduchou chybovou hlášku a bota ukončit

---

## Uživatelské statistiky

---

## Česká lokalizace

- vytvořit české varianty dostupných her a ostatních funkcí jako samostatné příkazy (trivia -> kvíz, wordle -> hádej slovo, tic-tac-toe -> piškvorky, info -> informace)
- tyto české varianty budou sdílet herní logiku a UI, jenom budou mít jiné texty
- kvíz bude mít otázky týkající se české republiky
- hádej slovo bude obsahovat slova místo anglických

---

## Web API

https://share.gemini.google/prmBNFuzUWzR
https://share.gemini.google/WblCzbkuTEP8

- přidat volitelný API bridge (přes aiohttp.web nebo FastAPI), který zprostředkuje backend API bota a bude posílat JSON payload, ve kterém budou informace o UI (embedy, views, atd.)
- do projektu `strachy.win` přidat stránku používající @derockdev/discord-components-react knihovnu s chatovacím oknem, ve kterém se zobrazí UI bota a bude možné používat jeho commandy
- do projektu `strachy.win` navíc přidat stránky pro minihry s vlastním webovým rozhraním, které bude používat `StrachBot` (python) backend

---

## Automatické testy
- přidat chybějící testy pro moduly: Wordle, Trivia a Shared + zkontrolovat testy pro Tic-Tac-Toe a Wordle

---

## Další mini-hry
- Songless
- Spoj 4 (Connect 4)
- Kámen-nůžky-papír(-spock-lizard)
- 2048
- Sudoku
- Šachy
- Lodě
- Blackjack
- Poker

--

## Další příkazy
- `/f1`, který vypíše náhodnou hlášku z Formule 1
- `/web` nebo `/website`, který bude odkazovat na mojí webovou stránku `strachy.win`
- `/coin-toss`, který hodí mincí