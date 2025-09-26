# IFC Room Schedule - Testing med Referansefil

Denne guiden viser hvordan du tester applikasjonen med IFC-referansefilen `AkkordSvingen 23_ARK.ifc`.

## Referansefil

**Fil:** `tesfiler/AkkordSvingen 23_ARK.ifc`
- **Størrelse:** 2.31 MB
- **Schema:** IFC4
- **Innhold:** 34 rom, 3737 entiteter totalt
- **Bygning:** AkkordSvingen 23 (arkitektmodell)

## Testskript

### 1. Grunnleggende funksjonalitetstest
```bash
python test_ifc_file_handling.py
```

Dette skriptet tester:
- ✅ IFC-fil lasting
- ✅ Rom-ekstrahering (34 rom funnet)
- ✅ Relasjonsanalyse (5 relasjoner per rom i gjennomsnitt)
- ✅ Alle parsere fungerer

### 2. Generer komplett romskjema
```bash
python generate_room_schedule.py
```

Dette skriptet genererer:
- 📊 Detaljert romskjema med alle 34 rom
- 📈 Bygningsstatistikk (417.77 m² total areal)
- 🔗 Relasjonssammendrag
- 💾 JSON-utdata (`room_schedule_output.json`)

### 3. Test hovedapplikasjon
```bash
python test_main_app.py
```

Verifiserer at GUI-applikasjonen kan håndtere filen.

## Romskjema Resultater

### Bygningsstatistikk
- **Totalt antall rom:** 34
- **Total gulvareal:** 417.77 m²
- **Total volum:** 1,128.50 m³
- **Gjennomsnittlig romstørrelse:** 12.29 m²

### Romtyper
- **BRA Etasje:** 2 rom (76.46 m² hver)
- **BRA Leilighet:** 4 rom (32.57 m² hver)
- **Stue:** 8 rom (8.68-8.69 m² hver)
- **Soverom:** 4 rom (7.51-7.54 m² hver)
- **Bad:** 4 rom (4.72-4.73 m² hver)
- **WC:** 4 rom (4.81-4.84 m² hver)
- **Gang:** 4 rom (4.65-4.66 m² hver)
- **Sjakt:** 4 rom (0.50 m² hver)
- **Fasade:** 4 rom (1.73-3.72 m² hver)

### Relasjoner
- **Contains:** 165 totale relasjoner
- **DefinedBy:** 102 totale relasjoner

## Kjøre Hovedapplikasjonen

```bash
python main.py
```

1. Start applikasjonen
2. Last inn filen: `tesfiler/AkkordSvingen 23_ARK.ifc`
3. Generer romskjema og analyser relasjoner

## Tekniske Detaljer

### Parsere som fungerer
- ✅ **IfcSpaceExtractor** - Ekstraherer romdata
- ✅ **IfcRelationshipParser** - Analyserer relasjoner
- ⚠️ **IfcSpaceBoundaryParser** - Trenger API-justering

### Datamodeller
- ✅ **SpaceData** - Romdata med kvantiteter
- ✅ **RelationshipData** - Relasjonsdata
- ✅ **SurfaceData** - Overflatedata

### Støttede IFC-entiteter
- `IfcSpace` (34 funnet)
- `IfcBuilding` (1 funnet)
- `IfcBuildingStorey` (3 funnet)
- `IfcRelContainedInSpatialStructure`
- `IfcRelDefinesByProperties`
- `IfcRelSpaceBoundary`

## Feilsøking

Hvis du får importfeil:
```bash
pip install ifcopenshell PyQt6
```

Hvis IFC-filen ikke finnes:
- Sjekk at `tesfiler/AkkordSvingen 23_ARK.ifc` eksisterer
- Kontroller filstørrelse (skal være ~2.31 MB)

## Neste Steg

1. **GUI-forbedringer:** Implementer filvelger for IFC-filer
2. **Eksport:** Legg til Excel/CSV-eksport
3. **Visualisering:** Legg til 2D/3D-visning av rom
4. **Rapporter:** Generer PDF-rapporter
5. **Validering:** Legg til IFC-datavalidering