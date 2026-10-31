# Changelog – Forecasting (NL)

Versies volgen `jaar.maand.volgnummer`; het volgnummer begint elke maand bij 1. Elke versie vermeldt op welke Gielz-versie hij is gebaseerd. [English](CHANGELOG.md)

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
