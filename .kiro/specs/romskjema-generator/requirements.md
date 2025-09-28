# Requirements Document

## Introduction

Dette systemet skal eksportere utfylte romdata per IFC Space fra applikasjonen til et strukturert romskjema-format. Eksporten skal følge en omfattende JSON-mal som dekker alle aspekter ved romspesifikasjoner - fra grunnleggende identifikasjon til detaljerte tekniske krav som følger norske byggestandarder.

## Requirements

### Requirement 1

**User Story:** Som en byggeprosjektleder vil jeg kunne eksportere romdata fra IFC Spaces til strukturerte romskjemaer, slik at jeg kan dele komplette romspesifikasjoner med prosjektteamet.

#### Acceptance Criteria

1. WHEN brukeren velger IFC Spaces for eksport THEN systemet SHALL samle all tilgjengelig romdata
2. WHEN brukeren starter eksport THEN systemet SHALL generere JSON-data basert på romskjema-malen
3. WHEN eksporten er ferdig THEN systemet SHALL produsere en fil per rom med komplett romskjema
4. IF romdata mangler kritisk informasjon THEN systemet SHALL markere manglende felt i eksporten

### Requirement 2

**User Story:** Som en arkitekt vil jeg kunne eksportere romdata med alle tekniske spesifikasjoner og krav, slik at romskjemaene inneholder komplett informasjon for forskjellige romtyper.

#### Acceptance Criteria

1. WHEN systemet eksporterer romdata THEN systemet SHALL inkludere alle tekniske krav basert på romtype
2. WHEN eksporten genereres THEN systemet SHALL populere felt som følger norske standarder (NS 3420, NS 8175, TEK17)
3. WHEN rommet har utstyr THEN systemet SHALL eksportere data for alle disipliner (ARK, RIV, RIE, RIB, RIA, RIBr)
4. IF rommet har spesifikke materialer THEN systemet SHALL inkludere leverandør- og produktinformasjon i eksporten

### Requirement 3

**User Story:** Som en prosjektmedarbeider vil jeg kunne eksportere romdata i forskjellige formater, slik at jeg kan dele informasjon med forskjellige verktøy og team.

#### Acceptance Criteria

1. WHEN brukeren eksporterer romdata THEN systemet SHALL generere gyldig JSON som følger romskjema-malen
2. WHEN brukeren velger eksportformat THEN systemet SHALL kunne generere JSON, PDF eller Excel-format
3. WHEN eksporten kjøres THEN systemet SHALL produsere filer som kan importeres i andre systemer
4. IF eksporten feiler THEN systemet SHALL vise tydelige feilmeldinger med årsak

### Requirement 4

**User Story:** Som en kvalitetssikrer vil jeg kunne validere romdata mot standarder og krav, slik at jeg kan sikre at alle spesifikasjoner er korrekte og komplette.

#### Acceptance Criteria

1. WHEN brukeren validerer romdata THEN systemet SHALL sjekke mot norske byggestandarder
2. WHEN systemet finner avvik THEN systemet SHALL vise spesifikke feilmeldinger med referanser
3. WHEN brukeren fyller ut HMS-data THEN systemet SHALL validere mot gjeldende sikkerhetskrav
4. IF romdata mangler kritiske felt THEN systemet SHALL hindre generering av romskjema

### Requirement 5

**User Story:** Som en BIM-koordinator vil jeg kunne eksportere romdata direkte fra IFC Spaces, slik at romskjemaene automatisk inneholder korrekte IFC-referanser og geometridata.

#### Acceptance Criteria

1. WHEN systemet eksporterer fra IFC Space THEN systemet SHALL automatisk inkludere Space GUID og geometridata
2. WHEN eksporten kjøres THEN systemet SHALL populere IFC-seksjonen med korrekte referanser
3. WHEN romskjema genereres THEN systemet SHALL inkludere alle IFC-metadata (site, building, storey GUIDs)
4. IF IFC-data mangler THEN systemet SHALL markere manglende IFC-informasjon i eksporten

### Requirement 6

**User Story:** Som en bruker vil jeg kunne konfigurere hvilke data som skal eksporteres og i hvilket format, slik at jeg kan tilpasse eksporten til prosjektets behov.

#### Acceptance Criteria

1. WHEN brukeren starter eksport THEN systemet SHALL vise konfigurasjonsmuligheter for eksport
2. WHEN brukeren velger eksportinnstillinger THEN systemet SHALL kunne filtrere hvilke seksjoner som inkluderes
3. WHEN eksporten kjøres THEN systemet SHALL respektere brukerens valg for format og innhold
4. IF brukeren velger delvis eksport THEN systemet SHALL markere hvilke seksjoner som er inkludert/ekskludert