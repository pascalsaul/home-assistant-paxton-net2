# Configuratie

## Normale deur

Een normale deur gebruikt de knop **Open once**. De integratie verstuurt:

```http
POST /api/v1/commands/door/open
```

De Net2-deurconfiguratie bepaalt hoe lang de deur geopend blijft.

## Toggledeur

Een toggledeur gebruikt **Toggle access**:

- locked → `holdopen`
- unlocked → `close`

De actuele beslissing wordt gebaseerd op `doorRelayOpen` uit Net2. De integratie bewaart dus geen eigen virtuele toggletoestand.

## Uitgesloten deur

Een uitgesloten deur behoudt statussensoren maar krijgt geen bediening. Dit voorkomt dat de frontend een knop toont voor hardware die de API-opdracht wel accepteert maar fysiek niet uitvoert.
