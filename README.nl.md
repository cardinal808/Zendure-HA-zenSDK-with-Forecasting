#  Zendure Home Assistant Integratie

 [![English 🌍 Global](https://img.shields.io/badge/English-Global-blue?style=for-the-badge)](README.md) [![Dutch 🇳🇱 NL](https://img.shields.io/badge/Dutch-NL-orange?style=for-the-badge)](README.nl.md)<br><br>

## 🔮 Deze fork: Forecasting-modus

> **Dit is een fork van [Gielz1986/Zendure-HA-zenSDK](https://github.com/Gielz1986/Zendure-HA-zenSDK)** van Michiel Hofker (Gielz1986). Alle eer voor de integratie, de automation en het dashboard gaat naar het oorspronkelijke project. Deze fork voegt **één extra modus toe: Dynamisch NOM + Forecasting** (Engels: *Dynamic Smart Matching + Forecasting*). Voor al het andere (modussen, wiki, ondersteuning, updates) zie je de oorspronkelijke repository. De originele README staat onder deze sectie.

**Versie:** `2026.11.4` · gebaseerd op Gielz-configuratie `v20261007` · beschikbaar in het Nederlands (NL) en Engels (Global) · [Changelog](CHANGELOG.nl.md)

Versies volgen `jaar.maand.volgnummer` (het volgnummer begint elke maand bij 1). In Home Assistant zie je de versie in gebruik en de nieuwste versie op GitHub (`sensor.forecasting_versie`, `sensor.forecasting_releasecheck`) op het tabblad Configuratie, en de releasenotes onder Releasenotes.

### Wat de modus doet

De accu laadt op de goedkoopste momenten, maar **alleen zoveel als nodig is**, rekening houdend met je zonvoorspelling, je verbruik en de prijzen van morgen.

- Berekent elk kwartier (en bij elke wijziging) een laadplan (`sensor.zendure_forecast_plan`) met status *Laden / Wachten / Niet nodig / Niet gunstig*.
- **Scenario A** (morgen goedkoper of gelijk, of prijzen nog onbekend): laadt genoeg om te overbruggen tot het goedkope moment van morgen of tot er voldoende zon is, plus een instelbare marge.
- **Scenario B** (morgen duurder): laadt zo vol mogelijk, mits de prijs nu lager is dan het laadmoment van morgen.
- Houdt rekening met zon die je nog verwacht (vandaag en morgen), met een betrouwbaarheidspercentage.
- **Zelfverbruik zon** wordt vanaf dag 1 automatisch berekend: de eerste dag als percentage van de productie, daarna in kWh per dag over maximaal 7 dagen (op een sombere dag is het percentage hoger dan op een zonnige). Geen invoerveld nodig.
- **Gemiddeld dagverbruik** komt uit je eigen historie (import, export, productie, accu in/uit): vanaf ongeveer 2 uur na installatie al berekend en elke dag nauwkeuriger, tot 7 dagen. Geen invoerveld nodig.
- **Net-import en -export uit de P1-meter:** de kWh-tellers van de meter worden automatisch herkend (SlimmeLezer/ESPHome DSMR: `energy_consumed/produced_tariff_1/2`, HomeWizard P1, DSMR-integratie) en gebruikt, net als in het energiedashboard. Zonder meter wordt het berekend uit het vermogen (methode left). Valt de meter even weg, dan wordt het gemiste stuk later bijgeteld.
- **Rendementsfilter:** een laadslot moet goedkoper zijn dan de waarde van de opgeslagen energie na round-trip-verlies, en in scenario A onder het daggemiddelde. Het round-trip-rendement komt uit **RTE totaal** (alle kWh eruit / alle kWh erin), gelijk verdeeld over laden en ontladen. De 24-uurs momentmetingen van de efficiëntie vallen te laag uit (ongewogen, elke stop telt als 0%) en worden alleen gebruikt als RTE totaal nog niet bruikbaar is.
- **Pad-check:** berekent wanneer de accu leeg raakt en kijkt van daar tot het moment dat de zon het verbruik dekt (uit de Solcast-detailvoorspelling, anders zonsopkomst + 3 uur) of tot het einde van de overbrugging, wat eerder is. Dure kwartieren in dat gat krijgen de goedkoopste laadslots ervóór, ook als er verder niets geladen hoeft te worden, en alleen als die na round-trip-verlies goedkoper zijn. Staat *niet ontladen in een goedkoop dal* aan, dan rekent de pad-check ermee dat de accu in die dalen niets levert.
- **Verbruiksprofiel per uur**, apart voor werkdag en weekend: elk heel uur wordt je werkelijke huisverbruik gemeten en verwerkt in een voortschrijdend gemiddelde per uur van de dag (`sensor.forecast_verbruiksprofiel`). Daarnaast leert hij per uur hoe het verbruik over de vier kwartieren verdeeld is (bijv. koken vanaf half zes); die vorm leert langzaam en verdeelt alleen het uurtotaal. De planner gebruikt dat per kwartier voor de pad-check, het moment dat de accu leeg is, de zon-dekking en de overbrugging. Zolang een uur nog niet genoeg metingen heeft (werkdag 3, weekend 2), geldt het daggemiddelde. Feestdagen volgen `binary_sensor.workday_sensor` (Workday-integratie) als die bestaat.
- **Gemeten laadvermogen** wordt gebruikt voor het aantal slots.
- **Slim vasthouden** (standaard aan): haalt de accu het einde van het gat niet en is er geen laadmoment meer, dan bewaart hij de lading voor de duurste kwartieren. Tussen twee laadslots levert hij niet als de prijs nu lager is dan het volgende laadslot na verlies.
- Optioneel: **niet ontladen in een goedkoop dal** (accu sparen), als er nog uit het net bijgeladen moet worden.
- **Laadblokken in gewone taal:** per blok wanneer, hoe lang, hoeveel kWh en tegen welke gemiddelde prijs, voor vandaag en (indicatief) voor morgen.
- **Besparing** *(optioneel pakket `zendure_besparing.yaml`)*: elk kwartier wordt je verbruik verrekend tegen een vast en een dynamisch tarief, met en zonder zon en accu. Op een eigen tab zie je per dag, maand, jaar en totaal wat je bespaart en waardoor (zon, dynamisch tarief, accu en slim laden), plus de terugverdientijd van de accu. De tabellen worden mooier opgemaakt met [card-mod](https://github.com/thomasloven/lovelace-card-mod) (optioneel).
- **Niet terugleveren bij negatieve prijs** (`zendure_negatieve_prijs.yaml`, hoort bij de basis): is de terugleverprijs (marktprijs + bonus + opslag) negatief, dan zet hij PV-export van de Zendure uit. Optioneel begrenst hij ook één of twee externe omvormers (productielimiet op de P1-meter, exportlimiet, schakelaar of script). Zet alleen terug wat hij zelf heeft omgezet.
- **Elektrische auto** *(optioneel pakket `zendure_ev.yaml`)*: voor een lader zonder eigen aansturing (grannylader, of een wallbox achter een slimme schakelaar) met een vermogensmeting, bv. een Shelly 1PM. De accu ontlaadt dan niet meer in de auto, en het laden van de auto telt niet mee in het verbruiksprofiel, het dagverbruik en het zelfverbruik van de planner. Met een schakelaar kun je ook een laadsessie plannen: *Nacht* laadt de benodigde kWh in de goedkoopste prijsslots tot een ingestelde tijd, *Overdag* laadt op zon en de planner laadt de accu dan extra uit het net op het goedkoopste moment.
- **Airco (HVAC)** *(optioneel pakket `zendure_hvac.yaml`)*: de airco niet uit de accu laten draaien, per modus in te stellen (bv. verwarmen niet, koelen wel) en optioneel wel in een duur uur. Kies of de accu dan helemaal niet ontlaadt, of alleen het airco-vermogen van de P1-meter aftrekt (met vermogensmeting); dat airco-verbruik telt dan ook niet mee in het verbruiksprofiel. Laden blijft werken.
- **Diagnose-export** *(optioneel pakket `zendure_export.yaml`)*: met één knop een JSON-bestand rechtstreeks op je eigen apparaat, met je instellingen, sensorstanden, plannerdetails en de logs van de afgelopen 24 uur, om mee te sturen bij een vraag of issue. IP-adressen en serienummers worden weggelaten. De knop gebruikt [button-card](https://github.com/custom-cards/button-card) (HACS); zonder button-card kan het via Ontwikkelhulpmiddelen → Acties.
- **Optionele pakketten tonen zich vanzelf:** de blokken Forecasting Configuratie (Besparing), (EV), (HVAC) en Diagnose-export staan alleen op het dashboard als het bijbehorende pakket geladen is. De kaart **Optionele pakketten** op de tab Configuratie laat zien welke geladen zijn en wat de andere doen. Zie [Pakketten](#pakketten).
- **Plan Tijdlijn** op het dashboard: voor de komende 36 uur per prijsslot in vier compacte rijen de prijs (kleuren zoals Gielz: groen = gepland laden, rood = duur), zon en huisverbruik, laden en ontladen van de accu met het verwachte laadpercentage, en net-import en -export. Als één kaart via `custom:mod-card`, dus card-mod (HACS) is nodig. Tip: sluit `sensor.zendure_forecast_grafiek` uit van de recorder (`recorder: exclude: entities:`), de attributen zijn groter dan de 16 kB-limiet van de recorder.
- Dashboard: sectie Forecasting op tab Zendure (plan vandaag en morgen, verbruiksprofiel, verzamelde 7-daagse gegevens, herbereken-knop), een tab Besparing en een blok Forecasting Configuratie (Basis) met alle invoervelden. Beide zijn te tonen of te verbergen met **Forecasting Tonen Op Dashboard**.

### Pakketten

De set bestaat uit een basis die je altijd nodig hebt en vijf optionele pakketten. De basis staat in de map `packages`, de optionele pakketten in de map `optional packages`. Kopieer je alleen de map `packages`, dan heb je dus precies de basis. Een optioneel pakket zet je erbij door het bestand uit `optional packages` in je eigen map `packages` te zetten en Home Assistant te herstarten; weghalen en herstarten zet de functie weer uit. De automation en het dashboard werken met en zonder de optionele pakketten.

| Pakket | Bestand (NL / Global) | | Wat het doet | Nodig | Zonder dit pakket |
|---|---|---|---|---|---|
| Gielz | `zendure_gielz1986_nl.yaml` / `zendure_gielz1986_global.yaml` | **Vereist** | De oorspronkelijke integratie, met één extra modus in de keuzelijst. | – | Niets werkt. |
| Forecasting | `zendure_forecasting.yaml` / `zendure_forecasting_global.yaml` | **Vereist** | De modus Dynamisch NOM + Forecasting: tellers, statistieken, planner. | Zon-forecast, P1-meter, Nord Pool | Geen forecasting-modus. |
| Negatieve prijs | `zendure_negatieve_prijs.yaml` / `zendure_negative_price_global.yaml` | **Vereist** | Niet terugleveren als teruglevering geld kost; optioneel externe omvormers begrenzen. | – | Teruglevering gaat door, ook bij een negatieve prijs. |
| Besparing | `zendure_besparing.yaml` / `zendure_savings_global.yaml` | Optioneel | Tab Besparing: wat zon, accu en dynamisch contract opleveren, terugverdientijd van de accu. | card-mod voor de opmaak (aanbevolen) | Tab Besparing toont een melding. Opslag en bonus teruglevering staan dan in Forecasting Configuratie (Negatieve Prijs). |
| EV | `zendure_ev.yaml` / `zendure_ev_global.yaml` | Optioneel | Auto laden zonder dat de accu erin ontlaadt; laadsessie nacht of overdag. | Vermogensmeting van de lader (bv. Shelly 1PM); voor een laadsessie een schakelaar | De accu kan in de auto ontladen; het laden telt mee in het verbruiksprofiel. |
| HVAC | `zendure_hvac.yaml` / `zendure_hvac_global.yaml` | Optioneel | Airco niet uit de accu, per airco-modus: niet ontladen of het airco-vermogen aftrekken; airco-verbruik dan apart van het verbruiksprofiel. | `climate.*`, vermogenssensor of schakelaar van de airco; voor aftrekken een vermogensmeting | Ontladen gaat gewoon door als de airco draait. |
| Nordpool | `zendure_nordpool.yaml` / `zendure_nordpool_global.yaml` | Optioneel | Twee Nord Pool-sensoren: all-in prijs voor levering (marktprijs + energiebelasting + opslag, met btw) en kale marktprijs met btw voor teruglevering, met invoervelden voor de bedragen. | Nord Pool-integratie (HACS); haal je eigen Nord Pool-YAML met dezelfde instellingen weg | Je stelt de Nord Pool-sensor(en) zelf in. |
| Diagnose-export | `zendure_export.yaml` / `zendure_export_global.yaml` | Optioneel | Eén JSON-bestand met instellingen, sensoren en logs, om mee te sturen bij een vraag of issue. | button-card (HACS) voor de downloadknop; zet zelf `system_log: fire_event: true` aan | Geen export; meesturen van gegevens gaat handmatig. |

Elk optioneel bestand heeft direct onder de versiekop de regel `# OPTIONEEL PAKKET`, de vereiste `# VEREIST PAKKET`, zodat je in de map meteen ziet welke je mag weglaten.

### Wat er veranderd is ten opzichte van het origineel

| Bestand (NL / Global) | Wijziging |
|---|---|
| `packages/zendure_forecasting.yaml` / `packages/zendure_forecasting_global.yaml` | **Nieuw.** Helpers, tellers, 7-daagse statistieken, de planner en afgeleide sensoren. |
| `optional packages/zendure_besparing.yaml` / `optional packages/zendure_savings_global.yaml` | **Nieuw, optioneel.** Invoervelden voor tarieven en accuprijs, en de besparings- en terugverdientijdsensoren. |
| `packages/zendure_negatieve_prijs.yaml` / `packages/zendure_negative_price_global.yaml` | **Nieuw.** Terugleverprijs, niet terugleveren bij een negatieve prijs, begrenzing van externe omvormers. Gebruikt de opslag en bonus teruglevering uit het besparingspakket als dat geladen is. |
| `optional packages/zendure_ev.yaml` / `optional packages/zendure_ev_global.yaml` | **Nieuw, optioneel.** Laadvermogen en ontlaadcorrectie van de auto, kWh-tellers, laadplan (nacht/overdag) en de aansturing van de lader. |
| `optional packages/zendure_hvac.yaml` / `optional packages/zendure_hvac_global.yaml` | **Nieuw, optioneel.** Airco-helpers, `binary_sensor.hvac_ontladen_geblokkeerd` / `binary_sensor.hvac_discharge_blocked`, `sensor.hvac_ontlaad_correctie` / `sensor.hvac_discharge_correction` en de aparte airco-tellers. |
| `optional packages/zendure_nordpool.yaml` / `optional packages/zendure_nordpool_global.yaml` | **Nieuw, optioneel.** Nord Pool-sensoren voor levering (all-in) en teruglevering (kale marktprijs met btw), met invoervelden voor energiebelasting, opslag en btw. |
| `optional packages/zendure_export.yaml` / `optional packages/zendure_export_global.yaml` | **Nieuw, optioneel.** Beslissingslog, momentopnames, foutlog en het exportscript. Zet `system_log: fire_event: true` aan. |
| `packages/zendure_gielz1986_nl.yaml` / `packages/zendure_gielz1986_global.yaml` | Alleen één extra optie in de modus-keuzelijst. |
| `automation_nl.yaml` / `automation_global.yaml` | De nieuwe modus in de modus-keuze en in de 6 bestaande NOM-lijsten (nul-op-de-meter, SOC-bescherming, noodstop), een eigen laadblok dat alleen laadt als het plan *Laden* zegt, een ontlaad-blokkade voor het goedkope dal en voor de airco, en in de NOM-ontlaadblokken het laadvermogen van de auto en (optioneel) de airco van de P1-meter af. Zonder de optionele pakketten werkt alles zoals voorheen. Bestaande modi zijn verder niet gewijzigd. |
| `dashboard_nl.yaml` / `dashboard_global.yaml` | Nieuwe sectie Forecasting, nieuwe tab Besparing, nieuwe blokken Forecasting Configuratie (Basis) en (Negatieve Prijs), de optionele blokken Forecasting Configuratie (Besparing), (EV), (HVAC) en Diagnose-export (alleen zichtbaar als het pakket geladen is), de kaart Optionele pakketten en een schakelaar in Configuratie (Dashboard). |

Elk gewijzigd bestand begint met een kop van twee regels met de versie, de Gielz-versie waarop hij is gebaseerd en de oorspronkelijke auteur.

### Installatie

Installeer eerst de oorspronkelijke integratie zoals hieronder beschreven (packages-bestand, automation, dashboard). Daarna:

1. Zet de **vereiste** bestanden `zendure_forecasting.yaml` en `zendure_negatieve_prijs.yaml` (NL) of `zendure_forecasting_global.yaml` en `zendure_negative_price_global.yaml` (Global) in dezelfde `packages`-map als het Gielz-pakket, en vervang het Gielz-pakket door de versie uit deze fork.
   Kies daarna welke **optionele** pakketten je wilt (zie [Pakketten](#pakketten)) en kopieer die uit de map `optional packages` naar dezelfde `packages`-map: `zendure_besparing.yaml`, `zendure_ev.yaml`, `zendure_hvac.yaml`, `zendure_export.yaml` (NL) of `zendure_savings_global.yaml`, `zendure_ev_global.yaml`, `zendure_hvac_global.yaml`, `zendure_export_global.yaml` (Global). Kopieer alleen de bestanden die je wilt; wat in `packages` staat, wordt geladen.
2. Vervang de automation en het dashboard door de versies uit deze fork (of voeg de wijzigingen samen met je eigen versie).
3. Herstart Home Assistant.
4. Vul in tab Configuratie bij **Forecasting Configuratie (Basis)** in: de sensor voor zon resterend vandaag, zon morgen (kWh, bijv. Forecast.Solar of Solcast) en een totaalteller van je zonnepanelen (kWh). Zet eventueel de laadmarge. Met het besparingspakket vul je bij **Forecasting Configuratie (Besparing)** je tarieven en de aanschafprijs van de accu in.
5. Kies de modus **Dynamisch NOM + Forecasting**.

**Vereist:** het Gielz-pakket, Nord Pool (zoals al ingesteld in Gielz), een P1-meter, een zon-forecast integratie en apexcharts-card voor het Gielz-dashboard en card-mod (voor de Plan Tijdlijn en, met het besparingspakket, de opmaak van de tabellen op de tab Besparing). Wat de optionele pakketten nodig hebben, staat in de tabel [Pakketten](#pakketten). De planner wordt na ongeveer een week historie nauwkeuriger.

> **Status:** persoonlijk project. De Nederlandse versie is in gebruik bij de auteur. De Engelse (Global) versie is een vertaling van de Nederlandse set: offline gecontroleerd (de planner geeft in 400 gesimuleerde situaties dezelfde uitkomst als de Nederlandse versie), maar nog niet in een echte Home Assistant gedraaid. Geen garantie: begin met een lage laadmarge en controleer het plan op het dashboard.

### Voor- en nadelen

**Ten opzichte van de oorspronkelijke modus Dynamisch NOM**

| ➕ Voordelen | ➖ Nadelen |
|---|---|
| Laadt alleen wat nodig is in plaats van een vast aantal goedkope periodes: minder onnodige kWh uit het net en minder cycli. | Meer in te stellen: een zon-forecast integratie en een totaalteller van je zonnepanelen. |
| Gebruikt je zonvoorspelling: een zonnige dag erna betekent minder netladen. | Heeft ongeveer een week historie nodig voordat verbruik en zelfverbruik gemeten zijn; tot die tijd gebruikt het standaardwaarden. |
| Kijkt naar de prijzen van morgen (scenario A/B) en controleert of de accu het eerste laadslot haalt. | Zo goed als je zonvoorspelling; de betrouwbaarheidsinstelling helpt, maar maakt een slechte voorspelling niet goed. |
| Past zich aan op je systeem: gemeten rendement, gemeten laadvermogen, 7-daags zelfverbruik. | Extra sensoren en een planner die elk kwartier herberekent. |
| Het plan is volledig zichtbaar op het dashboard, met een herbereken-knop. | Regelgebaseerd: een goed plan, geen wiskundig bewezen optimum. |

**Ten opzichte van een volledige optimizer zoals [Day Ahead Optimizer (DAO)](https://github.com/corneel27/day-ahead)**

| Deze fork | DAO |
|---|---|
| Geen extra software: alles is YAML in Home Assistant, geen add-on of Docker. | Een Home Assistant add-on (of Docker-container) met een eigen configuratie. |
| Een extra modus op je bestaande Gielz-opzet, geen apart systeem dat de Zendure aanstuurt. | Een apart systeem dat je apparaten plant. |
| Gebruikt je eigen zon-forecast sensoren. | Gebruikt weerdata van Meteoserver. |
| Alleen de batterij. | Batterij, warmtepomp, boiler, EV en meer. |
| Regelgebaseerd plan (scenario A/B, pad-check, rendementsfilter). | Wiskundige optimalisatie over alle uren tegelijk. |
| Jong project, nog weinig getest. | Gevestigd project met een community en een wiki. |

Kort gezegd: wil je alleen je Zendure-batterij optimaliseren zonder extra add-on, dan past deze modus goed. Wil je batterij, warmtepomp/boiler en EV samen plannen met een echte optimizer, dan is DAO de logischere route. Ze sluiten elkaar niet uit: deze modus kan als terugvaloptie blijven staan.

### Licentie

Deze fork valt onder dezelfde licentie als het origineel ([LICENSE](LICENSE)): **alleen persoonlijk en strikt niet-commercieel gebruik**, delen en aanpassen toegestaan mits de volledige licentietekst wordt meegegeven en de wijzigingen worden vermeld (zie de tabel hierboven). Commercieel gebruik vereist toestemming van de oorspronkelijke auteur.

---

*Hieronder: de originele README van Gielz1986.*



![Preview](Images/NL-Dashboard-290526.gif) <br>
<a href="https://github.com/Gielz1986/Zendure-HA-zenSDK/wiki/NL-%E2%80%90-Beschikbare-entiteiten">
Ga naar de uitleg over alle entiteiten en het dashboard
</a>

<br>

**Om in slechts 2️⃣ simpele stappen je batterij volledig lokaal werkend te krijgen in Home Assistant.**

Gebaseerd op de zenSDK RESTful API voor Home Assistant. Deze package maakt lokaal verbinding met één **Zendure Solarflow 2400 (AC, AC+ of AC Pro) / Zendure Solarflow 1600 AC+ / Zendure Solarflow 800 (Pro(2) of Plus) / Zendure Solarflow 3000 Mix AC+ / Zendure Solarflow 4000 Mix (AC+ of Pro)**. Perfect voor iedereen die zijn batterij **100% lokaal** en volledig onder eigen controle wil draaien in Home Assistant. Inmiddels zijn er **11 voorgeprogrammeerde modussen**  — van heerlijk NOMen op basis van de grote vuurbal tot energieboer spelen met dynamisch handelen voor een paar stuivers.

Voor deze integratie zijn diverse uitbreidingen beschikbaar, waaronder ondersteuning voor meerdere omvormers en oudere modellen zoals de SolarFlow Hyper 2000. Zie [Integratie add-ons](#-optioneel-integratie-add-ons) voor een volledig overzicht.

Vind je dit project nuttig en wil je verdere ontwikkeling supporten? <br>
Trakteer mij op een kopje koffie ☕️ en volg deze GitHub repository ⭐⭐⭐.

<a href="https://www.buymeacoffee.com/gielz" target="_blank">
  <img src="https://github.com/Gielz1986/Zendure-zenSDK-HA/blob/main/Images/bmc.png?raw=true" width="120" alt="Buy Me a Coffee">
</a><br><br>


## 1️⃣ Entiteiten beschikbaar maken

#### ℹ️ Benodigde hardware

- Homewizard P1 (of een andere P1/CT-meter die data per seconden levert (+watt afname / -watt teruglevering).
- één Solarflow 2400 (AC, AC+ of AC Pro) / Solarflow 1600 AC+ / Solarflow 800 (Pro(2) of Plus) / Solarflow 3000 Mix AC+ / Solarflow 4000 Mix (AC+ of Pro).
- Of meerdere dezelfde omvormers in combinatie met de [Node-RED proxy van Gast777](https://github.com/gast777/Zendure-zenSDK-proxy)

---

### #️⃣ Configuratie en herstart

1. Zorg ervoor dat **HEMS is uitgeschakeld** in de Zendure-app.
2. Plaats [Zendure_gielz1986_nl.yaml](./Dutch%20(NL)%20Integration/packages/zendure_gielz1986_nl.yaml) uit de map packages van GitHub in de map packages van Home Assistant. Mocht de map packages niet bestaan maak deze dan aan.
3. Maak nu een **backup** van je `configuration.yaml`.
4. Pas daarna je `configuration.yaml` aan door de onderstaande regel toe te voegen.

```
homeassistant:
  packages: !include_dir_named packages
```

| ![Preview](Images/packages2.png) |
|-----------------------------------|

5. Herstart Home Assistant.
6. Optioneel kun je nu het plug-n-play dashboard aanmaken [Ga naar Plug-N-Play Dashboard](#-optioneel-plug-n-play-dashboard). Of vul nu bij de onderstaande entiteiten in Home Assistant de juiste gegevens in en herstart Home Assistant nogmaals.
7. Ga naar [deel 2](#2️⃣-zendure-zensdk-gielz-automatisering) zodat je niet alleen data kunt uitlezen maar ook de batterij kunt aansturen met een enkele automatisering.

---


<img  alt="image" src="https://github.com/user-attachments/assets/c395c122-3bc4-4969-99f1-28dbabf89a77" />
*plug-n-play dashboard

<br>
<br>

| Uitleg per configuratie item | |  
|-|-|
| **Gielz Configuratie (Basis)** | **Informatie**|  
| `zendure_2400_ac_ip_adres`       | **bijvoorbeeld 192.168.0.172** – In de Zendure app onder device Information. |  
| `homewizard_p1_ip_adres`    | **(Instellingsadvies: gebruik een Homewizard P1) bijvoorbeeld 192.168.0.192** – In de Homewizard app (lokale API aanzetten).  |  
| `zendure_2400_ac_standby_vertraging` | **(Instellingsadvies: 15 minuten) 5-30 minuten** – Geef hier aan hoe snel de omvormer 100% in standby gaat bij 0 activiteit. Dit voorkomt sluipverbruik van +/- 19 watt. | 
| `zendure_2400_ac_advies_instellingen_overnemen` | Zodra de batterij draait kun je met deze knop de onderstaande instellingsadviezen direct overnemen. | 
| **Gielz Configuratie (Opladen)** |**Informatie**|  
| `zendure_2400_ac_max_oplaadvermogen`    | **400 t/m 2400 watt** – Geef hier aan met hoeveel vermogen hij maximaal mag laden. Bij meerdere omvormers via Node-RED kan dit tot 7200 watt.  |  
| `zendure_2400_ac_opladen_starten_bij` | **(Instellingsadvies: -300 watt) -1000 t/m -80 watt** – hier geef je aan wanneer de batterij exact begint met opladen. Daarna balanceert de batterij naar 0 - de extra oplaadmarge.  | 
| `zendure_2400_ac_oplaadmarge` | **(Instellingsadvies: 50 watt) 0 t/m 250 watt** – Geef hier aan hoeveel minder je wilt meenemen tijdens opladen. Als je wat minder wilt opladen, in de zomer met voldoende opwek zou je dit zelfs op 200 kunnen zetten om import overdag 100% te voorkomen. (Zendure zelf hanteert hier 50 watt in HEMS).  | 
| **Gielz Configuratie (Ontladen)** |**Informatie**|  
| `zendure_2400_ac_max_ontlaadvermogen`    | **400 t/m 2400 watt** – Geef hier aan met hoeveel vermogen hij maximaal mag ontladen. Bij meerdere omvormers via Node-RED kan dit tot 7200 watt. |  
| `zendure_2400_ac_ontladen_starten_bij` | **(Instellingsadvies: 100 watt) 80 t/m 500 watt** – hier geef je aan wanneer de batterij exact begint met ontladen. Daarna balanceert de batterij naar 0 - de extra ontlaadmarge. | 
| `zendure_2400_ac_ontlaadmarge` | **(Instellingsadvies: 5 watt) 0 t/m 250 watt** – Geef hier aan hoeveel je extra wilt meenemen tijdens ontladen. Als je wat meer wilt ontladen dan noodzakelijk is. |
| **Gielz Configuratie (Laadpercentage)** |**Informatie**|  
| `zendure_2400_ac_soc_bescherming_uitgeschakeld`    | Vink dit aan om de dubbele SOC bescherming uit te schakelen. Wanneer de batterij onder het minimaal toegestaan laadpercentage zakt zal er niet meer automatisch bijgeladen worden. Er word gewacht tot de BMS (batterij management systeem) zelf actie onderneemt. |  
| `zendure_2400_ac_minimaal_toegestaan_laadpercentage` | **(Instellingsadvies: 10%) 5% t/m 50%** – Geef hier het minimaal toegestaan laadpercentage aan. | 
| `zendure_2400_ac_maximaal_toegestaan_laadpercentage` | **(Instellingsadvies: 100%) 70% t/m 100%** – Geef hier het maximaal toegestaan laadpercentage aan. Bij 100% vind er een SOC kalibratie plaats om het laadpercentage goed te kunnen inschatten. | 
| **Gielz Configuratie (PV)** |**Informatie**|  
| `zendure_2400_ac_pv_export_uitgeschakeld` | Vink dit aan om PV export uit te schakelen. Als de batterij vol is zal er niet langer energie geexporteerd worden van de verbonden zonnepanelen. | 
| **Gielz Configuratie (Optioneel)** |**Informatie**|  
| `afwijkende_p1_sensor` | **bijvoorbeeld `sensor.eigen_P1`** – je eigen afwijkende P1 sensor toevoegen waarbij +watt afname is en -watt teruglevering (vul je hier je eigen sensor in dan is deze altijd leidend). [Ga naar WIKI](https://github.com/Gielz1986/Zendure-HA-zenSDK/wiki/Global-and-NL-%E2%80%90-P1-CT-meters-(API's))) voor afwijkende P1/CT API's. |  
| `zendure_2400_ac_batterij_volgorde` | **bijvoorbeeld 1;5;3;4;2** – hiermee bepaal je zelf een afwijkende volgorde van de batterijen. De juiste volgorde bepaal je mede aan de hand van `sensor.zendure_2400_ac_batterij_serienummers` en de sticker op de batterij(en). Op deze manier zullen de batterijtemperaturen en het laadpercentage de juiste volgorde hebben zoals die van de batterij(en) in de stapel. | 
| **Gielz Configuratie (Dynamisch)** |**Informatie**|  
| `dynamisch_nordpool_sensor` | **bijvoorbeeld `sensor.nordpool_kwh_nl_eur_3_09_0`** – je eigen sensor van Nordpool (HACS) toevoegen. Wanneer je het Dynamisch Nordpool gedeelte in gebruik gaat nemen moet je voor dat je deze in gebruik neemt bij `dynamisch_handmatige_periode` en `dynamisch_handmatige_periode_morgen` even **unknown** weghalen. Hierna zal het dynamisch gedeelte werken. Alles wat in de forecast (morgen) gezet word zal overgenomen worden om 00:00 via de automatisering en verschijnen in vandaag. |  
| `dynamisch_export_correctie` | Stel het aantal cent in dat tijdens het exporteren wordt afgetrokken. Deze waarde wordt gebruikt in de spreadberekening. |
| `dynamisch_minimale_spread` | **bijvoorbeeld 25%** - Hiermee geef je aan vanaf hoeveel spread de batterij dynamisch gaat laden en opladen op hoog vermogen.  |  
| `dynamisch_15_minuten` | Vink dit aan wanneer je gebruik wilt maken van 15 minuten periodes.  |  
| **Configuratie (Dashboard)** |**Informatie**|  
| `help_tonen_op_dashboard` | Vink dit aan om de helpteksten te tonen bij de meest relevante onderdelen.  | 
| `pv_tonen_op_dashboard` | Vink dit aan om de verbonden (offgrid/mppt) PV te tonen op het dashboard.  |  
| `dynamisch_tonen_op_dashboard` | Vink dit aan om de dynamische sturing te tonen op het dashboard.  |  

---

## 2️⃣ Zendure zenSDK (Gielz) automatisering
De motor van alles: hij laadt slim op, ontlaadt slim, en zorgt dat alles samenwerkt. Kies uit 11 verschillende modi om hem precies zo te laten werken als jij wilt. Heb je bij het bovenstaande geen namen aangepast dan is het een kwestie van deze nieuwe automatisering aanmaken.

1. Maak een nieuwe automatisering aan.
2. Klik rechtsboven op **Bewerken in YAML**.
3. Plak de YAML-code uit het [Automation_nl.yaml](./Dutch%20(NL)%20Integration/automation_nl.yaml) bestand van deze GitHub.   
4. Sla op, en start de automatisering.

![Preview](Images/Automation1.gif)   
![Preview](Images/Automation2.gif) 

---

## ✅ Batterij mag aan de slag
Het moment is aangebroken: de batterij mag nu bewijzen dat hij meer is dan alleen een dure decoratie met kabels.

1. Open het plug-n-play dashboard of voeg de entiteit **Zendure 2400 AC Modus Selecteren** toe aan je eigen dashboard.
3. De modus zal op **Standby** staan.
4. Kies hier je gewenste modus om de **Zendure zenSDK (Gielz) automatisering** te activeren.
5. De batterij zal nu aan de slag gaan.

![Preview](Images/Modus-16022026.gif)  
<a href="https://github.com/Gielz1986/Zendure-HA-zenSDK/wiki/NL-%E2%80%90-Modussen">
Ga naar de uitleg over alle verschillende modussen
</a>


---

## 🔃 (Optioneel) Plug-N-Play Dashboard
Vanaf nu is het ook mogelijk om direct een volledig plug-n-play dashboard in gebruik te nemen.

1. Voor dit dashboard is [Apexcharts HACS](https://github.com/RomRider/apexcharts-card) vereist. En (optioneel) [Graphite HACS](https://github.com/TilmanGriesel/graphite).
2. Maak een nieuw leeg dashboard aan via links onderin op ⚙️ te klikken en ga dan naar **Dashboards**.
3. Klik vervolgens op **Dashboard toevoegen** en kies voor **leeg nieuw dashboard**.
4. Open het nieuwe dashboard.
5. Klik rechtsboven op de 3 puntjes en kies **Dashboard bewerken**
6. Klik rechtsboven op de 3 puntjes en kies **Ruwe configuratie-editor**.
7. Plak de YAML-code uit het [Dashboard_nl.yaml](./Dutch%20(NL)%20Integration/dashboard_nl.yaml) bestand van deze GitHub.
8. Sla op en het dashboard is volledig bruikbaar.
9. [Ga naar de WIKI](https://github.com/Gielz1986/Zendure-HA-zenSDK/wiki/NL-%E2%80%90-Beschikbare-entiteiten) om uitleg te krijgen over alle entiteiten.

![Preview](Images/Plug-N-Play-Dashboard.gif) 

---

## 🔃 (Optioneel) Integratie add-ons

Diverse gebruikers hebben aanvullende code ontwikkeld die direct met deze integratie werkt. Hieronder staan deze vermeld.

| Extra Add-ons | Use case |Informatie |
|-|-|-|
| [Node-RED proxy](https://github.com/gast777/Zendure-zenSDK-proxy) van [@gast777](https://github.com/gast777) | Meerdere omvormers in gebruik | Dan kun je dit uitbreiden met deze Node-RED proxy. Deze proxy zorgt ervoor dat alles binnen deze automatisering naadloos samenwerkt, waardoor meerdere identieke omvormers slim worden aangestuurd met een optimale vermogensverdeling.  |
| [Node-RED proxy (Hyper 2000)](https://github.com/twoenter/Zendure-zenSDK-Hyper-proxy) van [@twoenter](https://github.com/twoenter) | SolarFlow Hyper 2000 gebruiker | Dan kun je deze add-on gebruiken om Zendure Home Assistant (MQTT/Cloud) via een Node-RED-proxy te koppelen en gebruik te maken van alle functies van deze integratie. |
