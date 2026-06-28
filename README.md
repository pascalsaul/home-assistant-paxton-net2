<p align="center">
  <img src="custom_components/paxton_net2/brand/logo.png" alt="Paxton Net2 for Home Assistant" width="500">
</p>

# Paxton Net2 voor Home Assistant

Een custom Home Assistant-integratie voor de lokale Paxton Net2 API.

De integratie leest deuren en deurstatussen uit Net2 en biedt per deur Home Assistant-entiteiten voor status en bediening. Deuren kunnen als normale deur, toggledeur of alleen-lezen deur worden geconfigureerd.

> Dit project is onafhankelijk ontwikkeld en is niet officieel verbonden aan of ondersteund door Paxton Access.

## Functionaliteit

- Lokale communicatie met Paxton Net2 via HTTPS
- Configuratie via de Home Assistant-interface
- Automatische ontdekking van Net2-deuren
- Statussensoren per deur
- Eenmalig openen via `door/open`
- Openhouden en sluiten via `door/holdopen` en `door/close`
- Toggleprofiel voor deuren waarbij dezelfde actie afwisselend opent en sluit
- Uitsluiten van deuren die niet betrouwbaar via de API bediend kunnen worden
- Deurselectie op naam in de configuratie
- Serverversie en Net2-servermetadata als diagnostische sensoren
- Dynamische Lovelace-kaart met bevestiging en wisselende tekst `Openen`/`Sluiten`
- Branding voor de integratie met eigen icon en logo

## Geteste omgeving

- Paxton Net2 6.9
- Net2 Local API V1
- Home Assistant OS

Andere versies kunnen werken, maar zijn niet gevalideerd.

## Belangrijke beperking: PaxLock Pro

Bij de geteste PaxLock Pro-deuren accepteert Net2 de netwerkopdracht en registreert Net2 een deur-openevent, terwijl het fysieke slot niet opent. De API geeft daarbij geen betrouwbaar hardwaretype of duidelijke fout terug.

Daarom kunnen dergelijke deuren onder **Configureren** worden toegevoegd aan **Deuren uitsluiten van HA-bediening**. De statussensoren blijven dan bestaan, maar Home Assistant maakt geen bedieningsknop en geen Hold Open-schakelaar aan.

## Vereisten

- Een werkende Paxton Net2 Local API
- Een Net2 API-account met voldoende rechten
- Netwerktoegang vanaf Home Assistant naar de Net2-server, standaard via poort `8443`
- Een voor Home Assistant vertrouwd TLS-certificaat, of uitgeschakelde certificaatvalidatie tijdens het testen

Voor de voorbeeldkaart zijn daarnaast via HACS nodig:

- `auto-entities`
- `multiple-entity-row`

## Installatie via HACS als custom repository

1. Open HACS in Home Assistant.
2. Ga naar **Integraties**.
3. Open het menu rechtsboven.
4. Kies **Aangepaste repositories**.
5. Vul de URL van deze GitHub-repository in.
6. Selecteer categorie **Integratie**.
7. Installeer **Paxton Net2**.
8. Herstart Home Assistant volledig.

## Handmatige installatie

1. Kopieer:

   ```text
   custom_components/paxton_net2
   ```

   naar:

   ```text
   /config/custom_components/paxton_net2
   ```

2. Verwijder bij een upgrade bij voorkeur eerst de bestaande map.
3. Herstart Home Assistant volledig.
4. Ga naar **Instellingen → Apparaten & diensten → Integratie toevoegen**.
5. Zoek naar **Paxton Net2**.

## Net2 API-configuratie

De Net2 Local API is doorgaans bereikbaar via:

```text
https://<net2-server>:8443
```

De integratie gebruikt onder meer:

```http
GET  /api/v1/doors
GET  /api/v1/doors/status
POST /api/v1/commands/door/open
POST /api/v1/commands/door/holdopen
POST /api/v1/commands/door/close
```

Voorbeeld van een deurcommando:

```json
{
  "doorId": 7864368
}
```

## TLS-certificaat

Wanneer Net2 een intern of zelfondertekend certificaat gebruikt, moet Home Assistant dat certificaat vertrouwen. Tijdens een eerste test kan certificaatvalidatie worden uitgeschakeld in de integratieconfiguratie. Voor productiegebruik verdient een correct vertrouwde certificaatketen de voorkeur.

## Integratie toevoegen

Vul tijdens het toevoegen ten minste in:

- serveradres;
- gebruikersnaam;
- wachtwoord;
- client-ID;
- TLS-validatie;
- API-endpoints wanneer deze afwijken van de standaardwaarden.

De verbinding wordt getest voordat de configuratie wordt opgeslagen.

## Deurprofielen configureren

Ga naar:

```text
Instellingen → Apparaten & diensten → Paxton Net2 → Configureren
```

De configuratie toont deuren als:

```text
middendeur — 7864345
```

### Toggledeuren

Selecteer hier deuren waarbij dezelfde bediening afwisselend open en dicht moet schakelen.

Voor een toggledeur gebruikt de knop de actuele `doorRelayOpen`-status:

- `false` → `door/holdopen`
- `true` → `door/close`

### Toggledeuren die relais 2 gebruiken

Alleen nodig wanneer een toggledeur op relais 2 werkt. Voor de meeste installaties blijft dit leeg.

### Deuren uitsluiten van HA-bediening

Gebruik dit voor deuren die wel in Net2 bestaan, maar niet betrouwbaar via de Local API reageren, zoals de geteste PaxLock Pro-deuren.

Voor uitgesloten deuren:

- blijven statusentiteiten beschikbaar;
- wordt geen `Open once`- of `Toggle access`-knop aangemaakt;
- wordt geen `Hold open`-schakelaar aangemaakt;
- verdwijnen ze automatisch uit de meegeleverde dynamische dashboardkaart.

## Entiteiten

Per deur kunnen onder meer de volgende entiteiten worden aangemaakt:

- `Door open`
- `Unlocked`
- `Alarm`
- `Tamper`
- `Open once` of `Toggle access`
- `Hold open`

De `Unlocked`-sensor is gebaseerd op:

```text
doorRelayOpen
```

Dit is de relaisstatus en niet noodzakelijk een mechanische terugmelding van het slot.

De binary sensors bevatten tevens:

```yaml
door_id: "7864368"
```

## Dynamische frontendkaart

Installeer eerst via HACS:

- `custom:auto-entities`
- `custom:multiple-entity-row`

Voeg daarna een handmatige kaart toe en plak de inhoud van:

```text
examples/lovelace-door-card.yaml
```

De kaart:

- toont alleen deuren met een beschikbare bedieningsknop;
- verwijdert uitgesloten deuren automatisch;
- toont normale deuren met `Open`;
- toont toggledeuren dynamisch met `Openen` of `Sluiten`;
- toont `Locked` of `Unlocked` op basis van de relaisstatus;
- vraagt om bevestiging voordat een deuractie wordt uitgevoerd.

Meer uitleg staat in [`docs/frontend.md`](docs/frontend.md).

## Branding

De integratie bevat eigen brandingbestanden in:

```text
custom_components/paxton_net2/brand/
```

Daar staan onder meer:

```text
icon.png
logo.png
```

Home Assistant en HACS kunnen deze bestanden gebruiken om de integratie herkenbaar weer te geven. Na een wijziging van branding kan een browser-refresh of cacheverversing nodig zijn.

## Statusinterpretatie

### `doorRelayOpen`

Geeft aan of het deurrelais volgens Net2 geopend is. Dit wordt gebruikt voor `Locked`/`Unlocked` en voor de togglelogica.

### `doorContactClosed`

Geeft de status van het fysieke deurcontact. Bij sommige draadloze of afwijkend geconfigureerde deuren kan deze waarde ontbreken of niet betrouwbaar zijn.

### Net2-events

Een netwerkactie kan in Net2 verschijnen als:

```text
Request door open
Door opened
```

Dat betekent dat Net2 de opdracht heeft verwerkt. Bij sommige hardware, met name de geteste PaxLock Pro-deuren, garandeert dit niet dat het fysieke slot ook werkelijk geopend is.

## Upgraden

Bij een handmatige upgrade:

1. Verwijder:

   ```text
   /config/custom_components/paxton_net2
   ```

2. Kopieer de nieuwe map.
3. Herstart Home Assistant volledig.
4. Vernieuw de browser eventueel met `Ctrl+F5`.

Bestaande configuratie en entity-ID's blijven normaal behouden.

## Probleemoplossing

### Integratie verschijnt niet

Controleer:

```text
/config/custom_components/paxton_net2/manifest.json
```

en voer een volledige herstart uit.

### `cannot_connect`

Controleer:

- serveradres en poort;
- gebruikersnaam, wachtwoord en client-ID;
- bereikbaarheid vanuit Home Assistant;
- certificaatvalidatie;
- of `/api/v1/doors/status` beschikbaar is.

### Oude uitgesloten entiteiten blijven zichtbaar

Home Assistant kan eerder aangemaakte entiteiten als `unavailable` in de entiteitenregistry bewaren. De voorbeeldkaart negeert deze automatisch.

### Dashboardkaart blijft leeg

Controleer bij een `Unlocked`-binary sensor onder **Ontwikkelaarstools → Staten**:

```yaml
device_class: lock
door_id: "7864368"
```

Controleer daarnaast of `auto-entities` en `multiple-entity-row` correct zijn geïnstalleerd en geladen.

## Privacy en beveiliging

- Bewaar nooit Net2-wachtwoorden of bearer tokens in screenshots, issues of logbestanden.
- Beperk netwerktoegang tot de Net2 API.
- Gebruik bij voorkeur een afzonderlijk API-account met minimaal noodzakelijke rechten.
- Publiceer geen deur-ID's, gebruikersnamen, tokennummers of toegangslogs uit een productieomgeving.

## Bekende beperkingen

- Het deurhardwaretype is niet betrouwbaar uit de gebruikte deur- en statusendpoints af te leiden.
- PaxLock Pro-bediening kan door Net2 als geslaagd worden geregistreerd zonder fysieke actie.
- `doorRelayOpen` is geen gegarandeerde mechanische slotstatus.
- Eventmonitoring en een sensor voor de laatste toegangsactie zijn nog niet geïmplementeerd.

## Projectstructuur

```text
custom_components/paxton_net2/   Home Assistant-integratie
examples/                        Voorbeeldconfiguratie en Lovelace-YAML
docs/                            Aanvullende documentatie
hacs.json                        HACS-metadata
LICENSE                          MIT-licentie
```

## Licentie

Dit project is beschikbaar onder de [MIT License](LICENSE).
