# Requirements Document

## Introduction

Denne funksjonen utvider IFC Room Schedule-applikasjonen med muligheten til å importere enhetstider og produktdata, og mappe disse til alle IFC building element-entiteter (IfcWall, IfcSlab, IfcBeam, IfcColumn, IfcDoor, IfcWindow, etc.) samt overflater og rom. Dette skaper en kraftig kobling mellom 3D-modellen og prosjektøkonomien, og muliggjør automatisk kostnadsberegning, tidsestimering og ressursplanlegging basert på faktiske bygningselementer og deres egenskaper.

## Requirements

### Requirement 1

**User Story:** Som en kalkulatør vil jeg kunne importere enhetstider fra standardiserte databaser, slik at jeg kan automatisk beregne arbeidstid basert på faktiske mengder fra IFC-modellen.

#### Acceptance Criteria

1. WHEN brukeren importerer enhetstidsfil THEN systemet SHALL validere filformat (JSON, CSV, Excel) og vise importstatus
2. WHEN enhetstider importeres THEN systemet SHALL parse data og lagre enhetstider med tilhørende arbeidsoperasjoner
3. WHEN enhetstider er importert THEN systemet SHALL vise oversikt over tilgjengelige arbeidsoperasjoner og deres enhetstider
4. IF enhetstidsfil inneholder feil THEN systemet SHALL vise spesifikke feilmeldinger og fortsette med gyldige data
5. WHEN enhetstider lagres THEN systemet SHALL støtte forskjellige enheter (timer/m², timer/m³, timer/stk, timer/m)

### Requirement 2

**User Story:** Som en innkjøper vil jeg kunne importere produktdata med priser og spesifikasjoner, slik at jeg kan automatisk beregne materialkostnader basert på mengder fra IFC-modellen.

#### Acceptance Criteria

1. WHEN brukeren importerer produktdatabase THEN systemet SHALL validere og parse produktinformasjon med priser
2. WHEN produktdata importeres THEN systemet SHALL lagre produkter med navn, beskrivelse, pris, enhet og leverandørinformasjon
3. WHEN produkter er importert THEN systemet SHALL vise katalog over tilgjengelige produkter organisert etter kategori
4. IF produktdata mangler kritisk informasjon THEN systemet SHALL markere ufullstendige produkter og tillate manuell utfylling
5. WHEN produktpriser lagres THEN systemet SHALL støtte forskjellige prisenheter (NOK/m², NOK/m³, NOK/stk, NOK/m)

### Requirement 3

**User Story:** Som en prosjektleder vil jeg kunne mappe enhetstider og produkter til alle IFC building element-entiteter, overflater og rom, slik at jeg kan få automatiske kostnads- og tidsberegninger basert på faktiske bygningselementer.

#### Acceptance Criteria

1. WHEN brukeren velger et IFC building element (IfcWall, IfcSlab, IfcBeam, IfcColumn, IfcDoor, IfcWindow, etc.) THEN systemet SHALL vise relevante arbeidsoperasjoner og produkter for mapping
2. WHEN brukeren mapper arbeidsoperasjon til building element THEN systemet SHALL automatisk beregne total arbeidstid basert på elementets mengder (volum, areal, lengde, antall) og enhetstid
3. WHEN brukeren mapper produkt til building element THEN systemet SHALL automatisk beregne total materialkostnad basert på elementets mengder og produktpris
4. WHEN mapping er definert THEN systemet SHALL lagre mapping-relasjoner og oppdatere beregninger automatisk ved endringer i IFC-data
5. WHEN flere operasjoner mappes til samme building element THEN systemet SHALL summere alle kostnader og tider korrekt
6. WHEN systemet ekstraherer IFC building elements THEN systemet SHALL hente ut alle relevante mengder (NetVolume, GrossVolume, NetArea, GrossArea, Height, Length, Width)
7. WHEN building elements har materialer THEN systemet SHALL kunne mappe produkter basert på material-egenskaper

### Requirement 4

**User Story:** Som en estimator vil jeg kunne se detaljerte kostnads- og tidsberegninger per building element, per rom og totalt, slik at jeg kan lage nøyaktige prosjektkalkyler.

#### Acceptance Criteria

1. WHEN mapping er definert THEN systemet SHALL vise detaljerte beregninger per IFC building element med arbeidstid og materialkostnad
2. WHEN beregninger vises THEN systemet SHALL inkludere totalkostnader, arbeidstimer organisert etter element-type (vegger, dekker, bjelker, etc.)
3. WHEN brukeren ber om sammendrag THEN systemet SHALL generere totalkalkyler for hele prosjektet gruppert etter building element-kategorier
4. WHEN mengder endres i IFC-modell THEN systemet SHALL automatisk oppdatere alle beregninger basert på nye element-mengder
5. WHEN beregninger er komplette THEN systemet SHALL kunne eksportere detaljerte kostnadsrapporter med breakdown per element-type
6. WHEN systemet viser beregninger THEN systemet SHALL kunne filtrere og sortere etter element-type, etasje, eller andre IFC-egenskaper

### Requirement 5

**User Story:** Som en bruker vil jeg kunne definere egne arbeidsoperasjoner og produkter, slik at jeg kan tilpasse systemet til spesifikke prosjektbehov.

#### Acceptance Criteria

1. WHEN brukeren oppretter ny arbeidsoperasjon THEN systemet SHALL tillate definering av navn, beskrivelse, enhetstid og enhet
2. WHEN brukeren oppretter nytt produkt THEN systemet SHALL tillate definering av navn, beskrivelse, pris, enhet og kategori
3. WHEN egendefinerte elementer opprettes THEN systemet SHALL lagre disse sammen med importerte data
4. WHEN brukeren redigerer eksisterende elementer THEN systemet SHALL tillate endringer og oppdatere relaterte beregninger
5. WHEN egendefinerte data eksporteres THEN systemet SHALL inkludere både importerte og manuelt opprettede elementer

### Requirement 6

**User Story:** Som en kvalitetssikrer vil jeg kunne validere mapping og beregninger, slik at jeg kan sikre nøyaktighet i kostnadsestimater.

#### Acceptance Criteria

1. WHEN brukeren validerer mapping THEN systemet SHALL sjekke at alle kritiske IFC building elements har tilordnede operasjoner og produkter
2. WHEN systemet finner manglende mapping THEN systemet SHALL vise advarsler med spesifikke building elements som mangler tilordninger
3. WHEN beregninger valideres THEN systemet SHALL sjekke for urimelige verdier og vise advarsler basert på element-type og størrelse
4. IF enhetstider eller priser er utdaterte THEN systemet SHALL markere elementer som trenger oppdatering
5. WHEN validering er komplett THEN systemet SHALL generere valideringsrapport med status for alle building element-kategorier
6. WHEN systemet validerer IFC-data THEN systemet SHALL sjekke at alle nødvendige mengder (volum, areal, etc.) er tilgjengelige for beregninger

### Requirement 7

**User Story:** Som en bruker vil jeg kunne eksportere komplette kalkyler med mapping-informasjon, slik at jeg kan dele detaljerte kostnadsanalyser med prosjektteamet.

#### Acceptance Criteria

1. WHEN brukeren eksporterer kalkyler THEN systemet SHALL generere detaljerte rapporter i JSON, Excel eller PDF-format
2. WHEN eksport genereres THEN systemet SHALL inkludere alle mapping-relasjoner, beregninger og IFC building element-data
3. WHEN rapport eksporteres THEN systemet SHALL inkludere sammendrag per building element-type, per etasje, per rom og totalt for prosjektet
4. IF eksport inneholder store datamengder THEN systemet SHALL optimalisere filstørrelse og struktur for effektiv håndtering
5. WHEN eksport er ferdig THEN systemet SHALL tillate import av mapping-data i andre prosjekter for gjenbruk
6. WHEN eksport inkluderer IFC-data THEN systemet SHALL eksportere building element GUIDs og egenskaper for sporbarhet tilbake til 3D-modellen