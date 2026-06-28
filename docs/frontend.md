# Frontend

## Vereiste HACS-kaarten

Installeer onder HACS → Frontend:

- auto-entities
- multiple-entity-row

Herlaad de browser nadat beide resources zijn geïnstalleerd.

## Kaart toevoegen

1. Open het gewenste dashboard.
2. Kies **Dashboard bewerken**.
3. Kies **Kaart toevoegen**.
4. Kies **Handmatig**.
5. Plak `examples/lovelace-door-card.yaml`.
6. Sla de kaart op.

De kaart zoekt dynamisch naar Paxton Net2-binary sensors met `device_class: lock` en koppelt vervolgens de beschikbare deurknop op hetzelfde Home Assistant-device.

Wanneer een deur in de integratie wordt uitgesloten of opnieuw wordt opgenomen, wordt de kaart automatisch bijgewerkt.
