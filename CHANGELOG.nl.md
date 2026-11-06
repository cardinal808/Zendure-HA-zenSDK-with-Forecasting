# Changelog – Forecasting (NL)

Versies volgen `jaar.maand.volgnummer`; het volgnummer begint elke maand bij 1. Elke versie vermeldt op welke Gielz-versie hij is gebaseerd. [English](CHANGELOG.md)

## 2026.11.3 — gebaseerd op Gielz v20261007

**Nieuw: elektrische auto** *(optioneel pakket)*
- Nieuw pakket `packages/zendure_ev.yaml` en een blok **Configuratie (EV)** op de tab Configuratie. Voor een lader zonder eigen aansturing (grannylader, of een wallbox achter een slimme schakelaar) met een vermogensmeting, bv. een Shelly 1PM of Pro 1PM in de groep van de lader.
- **Accu niet in de auto ontladen:** de NOM-ontlaadblokken trekken het laadvermogen van de auto (`sensor.ev_ontlaad_correctie`, boven een drempel van standaard 300 W) af van de P1-meter. De accu voedt dan alleen het huis; de auto laadt uit het net of de zon. Geldt altijd, ook zonder laadsessie.
- **Planner:** het laden van de auto telt niet meer mee in het verbruiksprofiel (per uur en per kwartier), het gemiddelde dagverbruik en het zelfverbruik van de zon. Een laaddag trekt de verwachting voor de accu dus niet scheef.
- **Laadsessie** (met een ingevulde schakelaar): kies het laadmoment en de benodigde kWh. *Nacht (goedkoopste uren)* zet de lader alleen aan in de goedkoopste prijsslots tot *Klaar om* (prijzen van morgen nog onbekend: patroon van vandaag, rond 14:00 opnieuw gepland). *Overdag (zon)* laadt zolang de zon op is; de planner haalt die kWh van het zon-overschot voor de accu af en laadt het tekort op het goedkoopste moment uit het net. Klaar of tijd voorbij: laadmoment terug naar Uit en de lader weer aan.

**HVAC nu in de publieke set** *(optioneel pakket)*
- `packages/zendure_hvac.yaml` (en `zendure_hvac_global.yaml`) staat nu ook in de publieke set: niet ontladen terwijl de airco draait. Er is geen aparte complete set meer.
- De automation controleert de airco met een template, zodat alles ook zonder het HVAC-pakket blijft werken.
- De schakelaar *HVAC Instellingen Tonen* is vervallen (zie hieronder).
- **Instellen per modus in plaats van per uur:** de tijden *Alleen laden vanaf/tot* zijn vervallen. Nieuw `sensor.hvac_modus` (Uit, Stand-by, Verwarmen, Koelen, Drogen, Ventileren, Auto) uit de modus en `hvac_action` van de climate-entiteit. Per modus zet je aan of ontladen toch mag, bv. Koelen aan (zomer, zon genoeg) en Verwarmen uit (winter, geen zon). Standaard is elke modus geblokkeerd.
- **Stand-by telt niet:** staat de airco op temperatuur (`hvac_action` idle), dan ontlaadt de accu gewoon.
- `binary_sensor.hvac_ontladen_geblokkeerd` heeft een attribuut `reden`, ook zichtbaar in Forecasting Configuratie (HVAC).

**Negatieve prijs**
- Nieuwe schakelaar **Zendure Pro PV-export uitschakelen** (`input_boolean.negatieve_prijs_zendure_pv_export`): kies of de functie bij een negatieve prijs ook de PV-export van de Zendure Pro (zon-ingangen) uitschakelt via Gielz' *PV Export Uitgeschakeld*. Gaat vanzelf aan zodra je *Niet terugleveren* aanzet; uit = alleen de externe omvormers begrenzen, bv. bij een Zendure zonder zonnepanelen.
- De instellingen voor de Zendure Pro en de externe omvormer staan nu samen in één kaart.
- **Nieuw: vooraf ontladen** (schakelaar *Vooraf ontladen*, modus Dynamisch NOM + Forecasting, zon-detailvoorspelling zoals Solcast nodig). Komt er een venster met een negatieve terugleverprijs en verwacht zon-overschot, dan zorgt de planner dat de accu bij het begin leeg genoeg is voor 75% van dat overschot. Zo kan meer zon de accu in en hoeft de omvormer minder te knijpen.
  - De accu ontlaadt daarvoor alleen voor het huis (geen teruglevering), in de duurste kwartieren vóór het venster: daar vervalt het vasthouden (goedkoop dal, slim vasthouden). Haalt hij het doel ook met overal ontladen niet, dan ontlaadt hij in alle kwartieren.
  - Netladen vóór het venster blijft alleen staan als het binnen de ruimte past (goedkoopste slots eerst), bv. 's nachts laden voor een dure ochtendpiek.
  - Laadt de zon de accu vóór het venster toch weer vol, dan doet hij niets. Min. SOC blijft altijd staan. Opslag en bonus teruglevering uit Forecasting Configuratie (Besparing) tellen mee in de terugleverprijs.
  - *Plan vandaag* legt uit wat hij doet; nieuwe attributen `vooraf_ontladen`, `vooraf_ontladen_nu`, `vooraf_venster_start`/`_eind`, `vooraf_zon_overschot_kwh`, `vooraf_doel_kwh`, `vooraf_verwacht_kwh`, `vooraf_grensprijs` en `vooraf_netladen_vervallen`.

**Nieuw: diagnose-export** *(optioneel pakket)*
- Nieuw pakket `packages/zendure_export.yaml` en een blok **Diagnose-export** op de tab Configuratie. Met *Export maken* schrijf je één JSON-bestand met versies, actieve pakketten, alle instellingen, de stand van alle sensoren, de details van de planner, de ingevulde externe sensoren en de status van de Zendure-automatiseringen. Je krijgt een melding met een downloadlink; na 1 uur (en bij een herstart) wordt het bestand weer verwijderd.
- Het pakket verzamelt ook drie logs: elke regel die de automation in het logboek zet (laatste 50), elk kwartier een momentopname van modus, SOC, P1, vermogen, prijs en plan (laatste 24 uur) en waarschuwingen en fouten uit het HA-log die over deze set gaan (laatste 20). Daarvoor zet het pakket `system_log: fire_event: true` aan.
- IP-adressen en serienummers worden weggelaten. De automation hoeft niet aangepast te worden.

**Nieuw: verbruiksgegevens resetten**
- Knop **Verbruiksgegevens resetten** in Forecasting Configuratie (Basis), met een bevestigingsvenster. Wist het geleerde verbruiksprofiel (per uur en per kwartier) en de historie van 7 dagen (zonproductie, net, accu, gemiddeld gebruik, zelfverbruik; ook de auto als het EV-pakket geladen is). De planner rekent daarna eerst met startwaarden en leert alles opnieuw. De besparing en het gemeten laadvermogen blijven bewaard.
- Werkt via `input_button.forecast_verbruiksgegevens_resetten`: het profiel reset zichzelf, een nieuwe automation wist de tellerhistorie (`recorder.purge_entities`) en laadt de statistieken opnieuw (`statistics.reload`).

**Zonproductie: geen sprongen meer**
- `sensor.forecast_teller_zon_productie` telt nu de toename van je productiesensor op in plaats van de stand over te nemen, net als de P1-tellers. Een andere sensor invullen, een teller die even 0 meldt of terugspringt, of een vervangen omvormer telt niet meer als productie. Daardoor kon de zonproductie over 7 dagen (en dus het gemiddelde dagverbruik) veel te hoog uitvallen. Een genegeerde sprong staat in het attribuut `laatste_sprong`.
- Net na een reset (nog geen historie) rekent de planner niet meer met 7 dagen historie maar met de startwaarden.

**Netmeter: eigen kWh-tellers invullen**
- Twee nieuwe invoervelden in Forecasting Configuratie (Basis): **Net import teller** en **Net export teller** (`input_text.forecast_net_import_teller_sensor` / `..._export_...`). Voor meters die niet automatisch herkend worden, bv. een Shelly Pro 3EM (stroomtangen), P1 Monitor of DSMR Reader. Meerdere sensoren met een komma worden opgeteld (bv. tarief 1 en 2); Wh en MWh worden omgerekend. Leeg = automatisch herkennen zoals voorheen (SlimmeLezer, HomeWizard, DSMR-integratie).
- Zonder herkende of ingevulde teller rekent de set import en export uit het vermogen. Dat is minder nauwkeurig; *Verzamelde gegevens* toont dan *Berekend uit vermogen (geen kWh-teller gevonden of ingevuld)*.
- Een wissel van bron (automatisch ↔ ingevuld, of een andere sensor) geeft geen sprong in de net-tellers: het nieuwe attribuut `meter_sensoren` onthoudt welke sensoren de stand leverden.

**Planner: pad-check kijkt voorbij de nacht**
- Zodra de prijzen van morgen bekend zijn (rond 14:00), kijkt de pad-check niet meer alleen tot het begin van de goedkope uren van morgen (bv. 00:45), maar tot de zon van morgen het verbruik dekt. Een dure ochtendpiek telt daardoor al 's middags mee: is laden nu (na laad- en ontlaadverlies) goedkoper dan inkopen in die piek én goedkoper dan laden in de nacht, dan wordt nu bijgeladen. Is de nacht goedkoper, dan plant hij de nacht.
- Dekt de zon morgen het verbruik niet (winter), dan kijkt hij tot zonsopkomst + 3 uur: het gaat om de ochtendpiek, niet om de avond van morgen. Zonder detailvoorspelling (bv. Forecast.Solar) geldt zonsopkomst + 3 uur als zon-dekking.
- Bij het doorkijken telt de zon van vandaag mee voor het moment dat de accu leeg is (direct verbruik en overschot naar de accu).
- De energiebalans (overbrugging, scenario A/B) verandert niet; na middernacht en zolang de prijzen van morgen onbekend zijn, rekent de planner precies als voorheen. Rendementsfilter en minimale spread gelden ook hier.
- Nieuwe attributen `padcheck_horizon`, `padcheck_voorbij_nacht` en `padcheck_zon_dekt_morgen_vanaf`; *Plan vandaag* toont *voorbij de nacht*.

**Dashboard**
- **Optionele pakketten tonen zich vanzelf:** Forecasting Configuratie (Besparing), (EV), (HVAC) en Diagnose-export staan alleen op de tab Configuratie als het pakket geladen is. Ontbreekt `zendure_besparing.yaml`, dan toont de tab Besparing alleen een melding in plaats van lege kaarten.
- Nieuwe kaart **Optionele pakketten** op de tab Configuratie: per optioneel pakket of het geladen is (✅/➖), het bestand en wat het doet, met een link naar de uitleg.
- **Plan Tijdlijn** weer in de eerste kolom onder PV, als één kaart (`custom:mod-card`, card-mod nodig), zonder de losse kleurenregel eronder.
- Plan vandaag: regel over de kWh die de auto overdag nog van de zon vraagt.
- `sensor.forecasting_versie`: attribuut `pakketten` (welke optionele pakketten actief zijn) vervangt `set`.

**Duidelijker wat optioneel is**
- Vereist zijn `zendure_gielz1986_nl.yaml`, `zendure_forecasting.yaml` en `zendure_negatieve_prijs.yaml`. Optioneel zijn `zendure_besparing.yaml`, `zendure_ev.yaml`, `zendure_hvac.yaml` en `zendure_export.yaml`.
- De README heeft een tabel **Pakketten**: per bestand vereist of optioneel, wat het doet, wat het nodig heeft en wat je mist zonder.
- Elk pakket heeft bovenaan, onder de versiekop, de regel `# OPTIONEEL PAKKET` (met wat het nodig heeft) of `# VEREIST PAKKET`.

**Upgraden**
- Vervang alle bestanden en **herstart** Home Assistant.
- Staat `zendure_negatieve_prijs.yaml` nog niet in je map `packages`, zet hem er dan bij: hij hoort nu bij de basis. De functie staat pas aan als je *Niet terugleveren bij negatieve prijs* aanzet.
- `zendure_besparing.yaml` is optioneel: wil je de tab Besparing niet, dan mag je hem weghalen. *Niet terugleveren bij negatieve prijs* rekent dan met de kale marktprijs (geen opslag of bonus teruglevering).
- Optioneel: zet `zendure_ev.yaml`, `zendure_hvac.yaml` en/of `zendure_export.yaml` (NL) of `zendure_ev_global.yaml`, `zendure_hvac_global.yaml` en/of `zendure_export_global.yaml` (Global) in de map `packages`. Heb je zelf al `system_log:` in `configuration.yaml`, haal dan het blok `system_log` uit het exportpakket en zet daar `fire_event: true`. Gebruikte je de complete set: `input_boolean.hvac_tonen_op_dashboard` bestaat niet meer en kan weg.
- Gebruik je *Niet terugleveren bij negatieve prijs*: **Zendure Pro PV-export uitschakelen** gaat na de herstart vanzelf één keer aan. Zet hem uit als je Zendure geen zonnepanelen heeft.
- Optioneel: zet in Forecasting Configuratie (Negatieve Prijs) **Vooraf ontladen** aan (staat standaard uit).
- Test eerst of je auto het laden hervat als de stroom terugkomt, voordat je de lader laat schakelen.
- Is je zonproductie of gemiddeld gebruik over 7 dagen te hoog door een eerdere sprong: druk na de update één keer op **Verbruiksgegevens resetten**.
- Staat bij *Verzamelde gegevens → Net* "Berekend uit vermogen", vul dan je eigen net-tellers in bij Forecasting Configuratie (Basis).

## 2026.11.2 — gebaseerd op Gielz v20261007

**Nieuw: niet terugleveren bij negatieve prijs** (optioneel)
- Nieuw pakket `packages/zendure_negatieve_prijs.yaml` en een blok **Configuratie (Negatieve Prijs)** op de tab Configuratie. Terugleverprijs per kwartier = marktprijs + bonus % (alleen bij een positieve marktprijs) + opslag teruglevering, met de tarieven uit Configuratie (Besparing) (`sensor.zendure_terugleverprijs_nu`).
- Is die negatief, dan zet de module Gielz' **PV Export Uitgeschakeld** aan en daarna weer uit. Laden uit zon en ontladen naar het huis blijven werken.
- **Externe omvormers (0, 1 of 2):** *Productielimiet* (SolarEdge, OpenDTU/Hoymiles, APsystems, Fronius) regelt elke 10 s op de P1-meter, alleen als de Zendure het overschot niet kan opnemen; *Exportlimiet* (GoodWe, Growatt) gaat naar 0; een `switch.*` gaat uit, een `script.*` krijgt `blokkeren: true/false`. Een tweede omvormer gaat helemaal naar het minimum. Alles wordt teruggezet zoals het was.

**Planner**
- **Verbruik per kwartier:** het verbruiksprofiel leert nu ook hoe het verbruik binnen elk uur over de vier kwartieren verdeeld is (werkdag en weekend apart, langzaam lerend). De planner gebruikt die vorm voor zon-dekking, *accu leeg*, pad-check, slim vasthouden, de indicatie van morgen en de tijdlijn; het totaal per uur en de energiebalans veranderen niet. Zolang de vorm nog weinig metingen heeft, rekent hij gelijk verdeeld zoals voorheen. Nieuwe attributen `verbruik_per_kwartier_bron` en `vorm_kwartier_aandeel_pct`; de profielsensor meet nu elk kwartier.
- **Slim vasthouden:** haalt de accu het einde van het gat niet en is er geen laadmoment meer, dan bewaart hij de lading voor de duurste kwartieren (via *Niet ontladen in goedkoop dal*). Nieuwe attributen `slim_vasthouden` en `vasthouden_grensprijs`.
- **Laadmarge in de pad-check:** de accu telt als leeg zodra alleen de marge over is, en is de accu leger dan de marge, dan wordt het tekort vóór de dure kwartieren bijgeladen (als dat loont).
- **Verbruiksprofiel tijdens het leren:** uren met nog te weinig metingen mengen de metingen die er zijn met het daggemiddelde, zodat een duidelijke avondpiek al meetelt.

**Dashboard**
- *Indicatie netladen morgen* vermeldt dat de laadmarge er nog niet in zit.
- *Verzamelde gegevens*: regel *Verbruik per kwartier*.
- Tab Besparing: melding *work-in-progress*.

**Upgraden**
- Vervang alle bestanden en **herstart** Home Assistant (nieuwe invoervelden en een sensor die nu elk kwartier meet).
- Optioneel: zet `zendure_negatieve_prijs.yaml` (NL) of `zendure_negative_price_global.yaml` (Global) in de map `packages` en zet in **Configuratie (Negatieve Prijs)** de schakelaar aan. Het blok staat onder Configuratie (PV) en is zichtbaar als *PV Tonen Op Dashboard* aanstaat.
- Het verbruik per kwartier leert vanzelf; in de eerste weken rekent de planner zoals voorheen.

## 2026.11.1 — gebaseerd op Gielz v20261007

**Nieuw: Besparing**
- Nieuw pakket `packages/zendure_besparing.yaml` en een tab **Besparing**. Elk kwartier wordt je verbruik verrekend tegen een vast tarief en tegen de dynamische prijs van dat moment, in zes situaties (zonder zon en accu, alleen zon, zon + accu; elk vast en dynamisch).
- Tegels *Vandaag, Deze maand, Dit jaar, Totaal*, een overzicht van waar de besparing vandaan komt (zon, dynamisch tarief, accu en slim laden), kosten per situatie, grafieken per dag en per maand, en de **terugverdientijd van de accu**.
- Invoervelden in **Configuratie (Besparing)**: vaste tarieven, opslag en bonus voor dynamisch, aanschafprijs van de accu en wat die al had terugverdiend.
- De tabellen worden opgemaakt met [card-mod](https://github.com/thomasloven/lovelace-card-mod) als die is geïnstalleerd; zonder card-mod werkt alles, alleen eenvoudiger opgemaakt.

**Planner**
- **Pad-check** stopte bij het eerste geplande laadslot, waardoor dure kwartieren later op de avond buiten beeld bleven. Hij kijkt nu van *accu leeg* tot de zon het verbruik dekt of tot het einde van de overbrugging.
- **Dal-blokkade in de pad-check:** staat *niet ontladen in een goedkoop dal* aan, dan rekent de pad-check ermee dat de accu in die dalen niets levert (dal per dag bepaald).
- **Indicatie van morgen** volgt dezelfde regels als de pad-check: welke dure kwartieren de accu dekt, wat het huis direct uit het net koopt en welke laadslots daarvoor nodig zijn. Nieuwe attributen `morgen_uit_accu_kwh`, `morgen_direct_net_kwh`, `morgen_netladen_balans_kwh`, `morgen_dure_kwartieren_kwh`; `morgen_laadmomenten` heeft nu ook `minuten` en `kwh`.
- **Laadblokken:** nieuw attribuut `laadblokken` (dag, start, eind, minuten, kWh, gemiddelde prijs) en `gepland_netladen_kwh`.
- De tellers voor import, export, zon en accu bevriezen nu elk kwartier (was elk uur), nodig voor de besparing per kwartier.

**Dashboard**
- Plan in gewone taal en de blokken *Vandaag* en *Morgen* herschreven: per laadblok wanneer, hoe lang, hoeveel kWh en tegen welke prijs; duidelijk wat uit de accu komt en wat direct uit het net; *Overbruggen tot* heet nu *Plan van vandaag loopt tot*.
- **Plan Tijdlijn:** prijskleuren zoals Gielz (groen = gepland laden, rood = de duurste periodes van Gielz, grijs = overig).
- Tegels *Forecast Instellingen* verwijderd; *Verbruiksprofiel* verplaatst naar sectie 2 (Import | Export); *Verzamelde gegevens* is een eigen kaart.

**Upgraden**
- Vervang alle bestanden en zet `zendure_besparing.yaml` (NL) of `zendure_savings_global.yaml` (Global) erbij in de map `packages`. **Herstart** Home Assistant (nieuwe invoervelden).
- Vul daarna bij **Configuratie (Besparing)** je tarieven en de accuprijs in. De besparing telt vanaf dat moment.

## 2026.10.2 — gebaseerd op Gielz v20261007

**Planner**
- **Verbruiksprofiel:** werkdagen onthouden langer (gewicht per nieuwe meting 0,2 → 0,1, geheugen ongeveer 2 weken), zodat één afwijkende dag minder invloed heeft; weekend ongewijzigd (gewicht 0,2, ongeveer 2,5 week).
- **Laadmomenten van morgen** als nieuw attribuut `morgen_laadmomenten`: de indicatieve laadslots van morgen, aaneengesloten kwartieren samengevoegd tot blokken met gemiddelde prijs.

**Dashboard**
- Blok *Morgen*: de laadmomenten staan achter *Indicatie netladen morgen*.
- Blok *Vandaag*: regel *Laadmarge* verwijderd (het is een instelling, zie Forecast Instellingen).
- *Verzamelde gegevens*: regel *Laadvermogen: ingesteld … gemeten …* verwijderd.

**Upgraden**
- Vervang alle bestanden (inhoudelijk zijn alleen `zendure_forecasting.yaml` en het dashboard gewijzigd, in de rest alleen het versienummer); herlaad daarna **Automatiseringen** en **Sjabloon-entiteiten** (Ontwikkelhulpmiddelen → YAML). Een herstart is niet nodig.

## 2026.10.1 — gebaseerd op Gielz v20261007

Eerste genummerde versie. Vervangt referentie `FC-20261027` en bevat alle aanpassingen sindsdien.

**Planner**
- **Pad-check:** berekent wanneer de accu leeg raakt en tot wanneer (eerste laadslot, zon die het verbruik dekt via de Solcast-detailvoorspelling, of einde overbrugging). Laadslots worden alleen gepland vóór het dure slot dat ze vervangen, en alleen als ze na round-trip-verlies goedkoper zijn. Werkt ook als er verder niets geladen hoeft te worden.
- **Verbruiksprofiel per uur**, apart voor werkdag en weekend (`sensor.forecast_verbruiksprofiel`), gebruikt voor overbrugging, accu leeg, zon-dekking en pad-check.
- **Rendement uit RTE totaal** (energiebalans van de accu), gelijk verdeeld over laden en ontladen. De 24-uurs momentmetingen vielen te laag uit.
- **Net-import en -export uit de P1-meter** (automatisch herkend: SlimmeLezer/ESPHome DSMR, HomeWizard P1, DSMR-integratie), net als het energiedashboard. Zonder meter berekend uit vermogen. Alle integratiesensoren van `trapezoidal` naar `left`.
- **Zelfverbruik zon en dagverbruik vanaf dag 1** berekend uit eigen metingen; invoervelden *Zelfverbruik zon (overwrite)* en *Standaard dagverbruik* verwijderd.

**Dashboard**
- **Plan in gewone taal** bovenaan het plan, en een duidelijkere pad-check-regel.
- **Plan Tijdlijn:** 36 uur vooruit per prijsslot in vier rijen (prijs, zon en verbruik, accu en laadpercentage, net), met compacte tooltip.
- Configuratie (Forecasting) opgeschoond (gemeten netlaadvermogen en de statusregel voor het dal eruit); bron van net-gegevens en rendement bij Verzamelde gegevens.
- **Versiebeheer:** `sensor.forecasting_versie`, `sensor.forecasting_releasecheck` en de releasenotes van deze uitbreiding in het dashboard.

**Upgraden**
- Vervang alle bestanden en **herstart** Home Assistant (nieuwe integratiemethode, verwijderde invoervelden en de GitHub-sensor vragen een herstart).
- De 7-daagse cijfers lopen in een week over naar de nieuwe P1-meterbron.
