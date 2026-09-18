# Kodgranskning av originalkoden

Granskningen gäller originalprogrammet `order_report.py`, alltså versionen innan
refaktoreringen (den som ligger i den bifogade zip-filen).

Originalet är cirka 220 rader där så gott som all kod ligger på toppnivå inuti
ett enda `try`-block. Det fungerar (det producerar fyra korrekta CSV-filer), men
det är svårt att läsa, testa och bygga vidare på. Nedan är de problem jag tycker
är viktigast.

---

## 1. Nästan all kod ligger på toppnivå i en enda fil

**Observation**
Filen innehåller inte en enda funktion eller klass. Inläsning, tvätt av data,
beräkningar, gruppering, avrundning och filskrivning ligger efter varandra på
toppnivå, inuti ett `try`-block som sträcker sig över nästan hela filen.

**Konsekvens**
Man måste läsa hela filen för att förstå vad som händer, eftersom det inte finns
några namn som förklarar delarna. Ingenting kan återanvändas – vill man bara
räkna ut försäljning per region måste man köra hela skriptet. Dessutom blir
`try`-blocket så stort att det är svårt att se var ett fel egentligen kan uppstå.

**Förslag**
Dela upp koden i funktioner med tydliga namn (`load_orders`, `clean_orders`,
`build_sales_report`, `save_reports`) och gruppera dem i avsnitt efter ansvar, så
att man kan läsa en funktion i taget.

---

## 2. Koden körs som en sidoeffekt vid import

**Observation**
Det finns ingen `main()` och ingen `if __name__ == "__main__":`. Raden
`print("Startar orderrapport")` och hela beräkningen körs direkt när filen läses
in.

**Konsekvens**
Så fort någon skriver `import order_report` läses CSV-filen in och fyra filer
skrivs till disk. Det gör det i praktiken omöjligt att testa koden med pytest,
och det är ett oväntat beteende för den som bara vill återanvända en del av
logiken.

**Förslag**
Lägg körningen i en `main()`-funktion som anropas från
`if __name__ == "__main__":`. Då gör en import ingenting annat än att göra
funktionerna tillgängliga.

---

## 3. Otydlig ansvarsfördelning

**Observation**
Samma kodstycke blandar olika slags arbete. Ett exempel är att rapporten byggs
och skrivs till fil direkt efter varandra (`result1 = data.groupby(...)` följt av
`result1.to_csv(...)`), och att tvätt av data sker mitt bland beräkningarna.

**Konsekvens**
Det går inte att räkna ut en rapport utan att också skriva en fil, vilket är
precis det man vill kunna göra i ett test. Det blir också svårare att se var ett
fel ska letas: är det inläsningen, tvätten eller rapporten som är fel?

**Förslag**
Skilj på "bygga rapport" (returnerar en DataFrame) och "spara rapport" (skriver
till disk). Låt inläsning, bearbetning och rapportering vara egna funktioner så
att varje steg kan köras och kontrolleras för sig.

---

## 4. Duplicerad kod för kategori- och regionrapporten

**Observation**
Blocken som skapar `result1` (per `product_category`) och `result2` (per
`region`) är i praktiken identiska – cirka 30 rader var, där enda skillnaden är
vilken kolumn som grupperas på. Beräkningen av `return_rate` upprepas dessutom
en tredje gång i returrapporten.

**Konsekvens**
En ändring, till exempel att avrunda `return_rate` till två decimaler i stället
för tre, måste göras på flera ställen. Glömmer man ett ställe blir rapporterna
inkonsekventa, och den typen av fel är lätt att missa.

**Förslag**
Bryt ut en funktion som tar grupperingskolumnen som argument, till exempel
`build_sales_report(data, group_column)`, och en liten hjälpfunktion för
`return_rate`.

---

## 5. Variabelnamnen `result1` och `result2` säger ingenting

**Observation**
De två viktigaste rapporterna heter `result1` och `result2`. Namnet `data`
används för allt från rådata till färdigt bearbetat dataset.

**Konsekvens**
Läsaren måste hålla i huvudet att `result1` är kategori och `result2` är region,
och det går inte att se på en rad kod vad som är vad. Risken att blanda ihop dem
när koden ändras är stor, och `data` som byter innehåll under filens gång gör det
svårt att veta vilket tillstånd datan är i på en given rad.

**Förslag**
Namn som beskriver innehållet: `sales_by_category`, `sales_by_region`,
`raw_orders`/`orders`. Namnet bör svara på frågan "vad innehåller den här?".

---

## 6. `print()` används för körinformation

**Observation**
All information om körningen skrivs med `print()`: `"Startar orderrapport"`,
`"Läste in", len(data), "rader"`, `"Sparade overview.csv"` och
`"Något gick fel:", error`.

**Konsekvens**
Det går inte att skilja vanlig information från fel, allt hamnar på stdout utan
tidsstämpel och utan att man ser vilken del av programmet som skrev raden. Man
kan inte heller dämpa eller styra utskrifterna, och felmeddelandet blandas med
den vanliga utskriften.

**Förslag**
Använd `logging` med `logger = logging.getLogger(__name__)` i varje modul och
konfigurera loggningen centralt vid programstart. Då får varje rad nivå
(INFO/WARNING/ERROR) och avsändare.

---

## 7. Bred `try/except Exception` som döljer fel

**Observation**
Hela programmet ligger i `try: ... except Exception as error: print("Något gick
fel:", error)`. Valideringen höjer dessutom ett helt generiskt fel:
`raise Exception("Fel data")`.

**Konsekvens**
Alla fel behandlas likadant: en saknad CSV-fil, ett felstavat kolumnnamn, en
skrivskyddad output-mapp och ett rent programmeringsfel (till exempel en
felstavad variabel) ger samma intetsägande utskrift. Programmet avslutas
dessutom med kod 0, alltså "allt gick bra", även när ingen rapport skapades. Det
gör att fel kan passera obemärkt om programmet körs automatiskt.

Meddelandet `"Fel data"` talar inte heller om *vilken* kolumn som saknas, vilket
gör felet svårt att åtgärda.

**Förslag**
Fånga specifika undantag (`FileNotFoundError`, `pd.errors.EmptyDataError`,
`pd.errors.ParserError`, `OSError`) och använd ett eget undantag, till exempel
`OrderDataError`, för fel i indatan. Felmeddelandet ska innehålla sökväg
respektive namnen på de kolumner som saknas, och programmet ska returnera en
felkod.

---

## 8. Hårdkodade relativa sökvägar

**Observation**
`INPUT_FILE = "data/orders.csv"` och `OUTPUT_FOLDER = "output"` är relativa till
den mapp man står i när man kör programmet. Output-mappen skapas aldrig.

**Konsekvens**
Programmet fungerar bara om man råkar stå i projektets rotmapp – körs det från
en annan mapp får man "Något gick fel: ... No such file or directory". Saknas
`output/` misslyckas `to_csv`, men felet sväljs av det breda `except`-blocket, så
det ser ut som att allt gick bra fast inga filer skapades. Det går inte heller
att peka på en annan fil, till exempel ett testdataset.

**Förslag**
Räkna ut sökvägarna från filens egen placering med `pathlib` och samla dem i en
konfiguration som kan bytas ut. Skapa output-mappen med
`mkdir(parents=True, exist_ok=True)` innan filerna skrivs.

---

## 9. Koden går inte att testa

**Observation**
Det finns inga tester, och koden är skriven så att tester är svåra att skriva:
logiken går inte att anropa, den läser en fil med hårdkodad sökväg och den
skriver alltid till disk.

**Konsekvens**
Man kan inte veta om en refaktorering ändrar resultaten. Det enda sättet att
kontrollera programmet är att köra hela skriptet och läsa CSV-filerna med ögonen,
vilket är både långsamt och lätt att göra fel.

**Förslag**
Lägg logiken i funktioner som tar en DataFrame in och returnerar en DataFrame
eller ett resultatobjekt ut, och skriv pytest-tester för beräkningarna,
grupperingarna och felfallen.

---

## 10. Tunn datavalidering

**Observation**
Valideringen består av en enda kontroll: `required.issubset(data.columns)`. Ett
tomt dataset (bara rubrikrad) går igenom. Orimliga värden som negativ `quantity`
eller `discount` större än 1 hanteras inte. Om hela `unit_price`-kolumnen skulle
sakna giltiga tal blir medianen `NaN`, och då fyller `fillna` inte i något alls –
`NaN` sprider sig vidare till `order_value` och `discounted_value` så att total
försäljning blir `NaN` utan att programmet säger till.

**Konsekvens**
Programmet kan producera rapporter som ser färdiga ut men är missvisande – till
exempel noll i försäljning för ett tomt dataset – utan att någon varnas. Det gör
att fel i indatan upptäcks sent, i värsta fall först när någon fattar beslut på
siffrorna.

**Förslag**
Kontrollera att filen finns, att datasetet har rader och att de obligatoriska
kolumnerna finns, med ett felmeddelande som pekar ut exakt vad som är fel. Logga
varningar när värden har ersatts eller ser orimliga ut, så att det syns i
körningen.
