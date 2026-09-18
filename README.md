# Orderrapport

Ett Pythonprojekt som läser en CSV-fil med orders, tvättar datan, räknar
ut försäljning och returer och sparar fyra rapporter som CSV-filer.

Projektet är en refaktorering av ett skript där all kod låg på toppnivå i ett
stort `try`-block. Samma beräkningar och samma rapporter finns kvar, men koden är
uppdelad i funktioner, använder `logging` i stället för `print()`, har tydligare
felhantering och automatiska tester.

## Vad programmet gör

1. Läser `data/orders.csv`.
2. Kontrollerar att filen finns, att den innehåller rader och att alla
   obligatoriska kolumner finns.
3. Tvättar datan: normaliserar `region` och `product_category`, gör
   `quantity`, `unit_price` och `discount` numeriska och gör om `returned` till
   `True`/`False`.
4. Räknar ut `order_value = quantity * unit_price` och
   `discounted_value = order_value * (1 - discount)`.
5. Sammanställer total försäljning, antal orders och antal returer.
6. Bygger rapporter per produktkategori, per region och över returer per
   kategori.
7. Sparar rapporterna i `output/`:
   - `overview.csv` – totalsiffror
   - `sales_by_category.csv` – försäljning per produktkategori
   - `sales_by_region.csv` – försäljning per region
   - `returns_by_category.csv` – returer och returandel per kategori

## Projektstruktur

```
.
├── data/
│   └── orders.csv          # datasetet som läses in
├── output/                 # här sparas rapporterna
├── order_report/           # programmets Pythonmoduler
│   ├── config.py           # sökvägar och dataclass
│   ├── validation.py       # inläsning och validering
│   ├── processing.py       # datatvätt och beräkningar
│   ├── reporting.py        # rapporter och filsparande
│   └── pipeline.py         # håller ihop hela flödet
├── tests/
│   └── test_order_report.py
├── order_report.ipynb      # jobbläge steg för steg
├── main.py                 # startpunkt för vanlig körning
├── code_review.md          # granskning av originalkoden
├── reflection.md           # reflektion över arbetet
├── README.md
└── requirements.txt
```

Modulerna följer programmets flöde:

| Steg | Funktion |
| --- | --- |
| Inställningar och sökvägar | `ReportConfig` (dataclass) |
| CSV-filen läses | `load_orders` |
| Datan valideras | `validate_orders` |
| Datan tvättas | `clean_orders` |
| Ordervärden räknas ut | `add_order_values` |
| Totalsiffror | `summarize_orders` |
| Rapporterna skapas | `build_reports`, `build_sales_report`, `build_returns_report`, `build_overview` |
| Filerna sparas | `save_reports` |
| Programmet startar | `main.py` eller `order_report.ipynb` |

## Installation

Kräver Python 3.10 eller senare.

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Beroenden

- `pandas` – inläsning, gruppering och beräkningar
- `pytest` – automatiska tester

## Köra programmet

Från projektets rotmapp:

```bash
python main.py
```

### Köra i Jupyter Notebook

Öppna `order_report.ipynb`, välj projektets Pythonmiljö som kernel och kör
cellerna uppifrån och ned. Notebooken visar varje steg och använder samma
funktioner som programmet och testerna. Därmed finns logiken bara på ett ställe.

Rapporterna hamnar i `output/` (mappen skapas automatiskt om den saknas). Vill
man använda andra sökvägar ändrar man standardvärdena i `ReportConfig`.

Om något är fel med indatan skrivs ett felmeddelande på ERROR-nivå och
programmet avslutas med felkod 1.

## Köra testerna

Från projektets rotmapp:

```bash
python -m pytest
```

Testerna täcker beräkningarna (`order_value`, `discounted_value`, returandel),
sammanställningarna per kategori och region, tvättreglerna, samt felfall som
saknad kolumn, tomt dataset, saknad fil och ogiltiga värden.

## Skillnader mot originalprogrammet

Beräkningarna är oförändrade – de fyra CSV-filerna blev identiska med
originalets när båda versionerna kördes på `data/orders.csv`. Följande är
medvetet ändrat:

- **Tomt dataset ger nu ett fel.** Originalet skapade rapporter med nollor för en
  fil som bara innehöll rubrikraden.
- **Felmeddelanden pekar ut vad som är fel**, till exempel vilka kolumner som
  saknas, i stället för `"Fel data"`.
- **Output-mappen skapas automatiskt.** Originalet misslyckades tyst om `output/`
  saknades.
- **Programmet avslutas med felkod 1** när en rapport inte kunde skapas.
  Originalet avslutades alltid med 0.
- **Varningar loggas** när värden har ersatts (saknade eller icke-numeriska
  värden) eller ser orimliga ut (`quantity` som är noll eller negativ, negativt
  `unit_price`, `discount` utanför 0–1). Värdena ändras inte.
- **Sökvägarna räknas ut från programmets mapp**, så det fungerar även om
  programmet körs från en annan katalog.
