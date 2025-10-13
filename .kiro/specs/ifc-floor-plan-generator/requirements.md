# Requirements Document

## Introduction

Dette systemet skal generere 2D planview/floor plans fra IFC-filer (Building Information Modeling). Systemet skal kunne prosessere IFC-filer, utføre horisontale snitt på spesifiserte høyder, og produsere SVG og GeoJSON output med konfigurerbar styling og filtrering. Systemet skal støtte norske feilmeldinger og ha robust feilhåndtering for vanlige problemer med IFC-filer.

## Requirements

### Requirement 1

**User Story:** Som en arkitekt/ingeniør, ønsker jeg å konvertere IFC-filer til 2D planview, slik at jeg kan få oversiktlige plantegninger for presentasjon og analyse.

#### Acceptance Criteria

1. WHEN en gyldig IFC-fil oppgis THEN systemet SHALL lese filen og identifisere alle IfcBuildingStorey elementer
2. WHEN IFC-filen ikke kan åpnes THEN systemet SHALL returnere feilkode "IFC_OPEN_FAILED" med norsk feilmelding
3. WHEN ingen IfcBuildingStorey finnes THEN systemet SHALL returnere feilkode "NO_STOREYS_FOUND" med veiledning om å kontrollere IFC-romstruktur

### Requirement 2

**User Story:** Som bruker, ønsker jeg å konfigurere snitthøyder per etasje, slik at jeg kan få optimale snitt for forskjellige etasjetyper.

#### Acceptance Criteria

1. WHEN standard cut_offset_m er definert THEN systemet SHALL bruke denne høyden for alle etasjer som standard
2. WHEN per_storey_overrides er spesifisert for en etasje THEN systemet SHALL bruke den spesifikke snitthøyden for den etasjen
3. WHEN snitt utføres på spesifisert høyde THEN systemet SHALL generere 2D geometri fra alle relevante elementer som krysses av snittet
4. WHEN snittet ikke gir noen segmenter THEN systemet SHALL returnere feilkode "EMPTY_CUT_RESULT" med veiledning om å verifisere cut_z og elementfiltre

### Requirement 3

**User Story:** Som bruker, ønsker jeg å filtrere hvilke IFC-klasser som inkluderes i planview, slik at jeg kan fokusere på relevante bygningselementer.

#### Acceptance Criteria

1. WHEN include_ifc_classes er spesifisert THEN systemet SHALL kun inkludere de opplistede IFC-klassene i snittet
2. WHEN exclude_ifc_classes er spesifisert THEN systemet SHALL ekskludere de opplistede IFC-klassene fra snittet
3. WHEN både include og exclude lister er tomme THEN systemet SHALL inkludere alle relevante IFC-klasser som standard
4. WHEN en IFC-klasse er i både include og exclude lister THEN exclude SHALL ha prioritet

### Requirement 4

**User Story:** Som bruker, ønsker jeg å konfigurere geometrigenerering, slik at jeg kan kontrollere kvaliteten og nøyaktigheten av 2D-representasjonen.

#### Acceptance Criteria

1. WHEN use_world_coords er true THEN systemet SHALL bruke globale koordinater for shape-generering
2. WHEN subtract_openings er true THEN systemet SHALL trekke fra åpninger (dører, vinduer) fra vegger og andre elementer
3. WHEN sew_shells er true THEN systemet SHALL søm skall for renere mesh-representasjon
4. WHEN geometrigenerering feiler for ett eller flere elementer THEN systemet SHALL returnere feilkode "GEOMETRY_SHAPE_FAILED" med veiledning om å sjekke representasjoner

### Requirement 5

**User Story:** Som bruker, ønsker jeg å generere SVG-filer med konfigurerbar styling, slik at jeg kan tilpasse utseendet til mine behov.

#### Acceptance Criteria

1. WHEN SVG genereres THEN systemet SHALL bruke default_color og default_linewidth_px som standard styling
2. WHEN class_styles er definert for en IFC-klasse THEN systemet SHALL bruke den spesifikke fargen og linjetykkelsen for den klassen
3. WHEN invert_y er true THEN systemet SHALL invertere Y-aksen for klassisk 2D-tegning orientering
4. WHEN background er spesifisert THEN systemet SHALL sette bakgrunnsfarge, ellers transparent bakgrunn
5. WHEN SVG-fil ikke kan skrives THEN systemet SHALL returnere feilkode "WRITE_FAILED" med veiledning om rettigheter og diskplass

### Requirement 6

**User Story:** Som bruker, ønsker jeg å eksportere til GeoJSON format, slik at jeg kan bruke dataene i web-applikasjoner og GIS-systemer.

#### Acceptance Criteria

1. WHEN write_geojson er true THEN systemet SHALL generere GeoJSON-filer i tillegg til SVG
2. WHEN GeoJSON genereres THEN hver polyline SHALL ha properties med ifc_class og kategori (norsk oversettelse)
3. WHEN GeoJSON genereres THEN filnavnet SHALL følge geojson_filename_pattern
4. WHEN GeoJSON inkluderer metadata THEN det SHALL inneholde linjetype og etasjenavn

### Requirement 7

**User Story:** Som bruker, ønsker jeg konfigurerbare filnavn og manifest, slik at jeg kan organisere output-filene systematisk.

#### Acceptance Criteria

1. WHEN SVG-filer genereres THEN filnavnene SHALL følge svg_filename_pattern med index og sanitized storey name
2. WHEN filnavn saniteres THEN skråstreker, kolon og lignende SHALL erstattes med understrek
3. WHEN manifest genereres THEN det SHALL inneholde metadata om alle genererte filer
4. WHEN manifest_filename er spesifisert THEN manifestfilen SHALL ha det spesifiserte navnet

### Requirement 8

**User Story:** Som bruker, ønsker jeg ytelsesoptimalisering for store IFC-filer, slik at prosesseringen kan håndtere komplekse bygningsmodeller effektivt.

#### Acceptance Criteria

1. WHEN multiprocessing er true THEN systemet SHALL kjøre parallell prosessering per etasje/element
2. WHEN max_workers er spesifisert THEN systemet SHALL bruke det angitte antallet worker-tråder/prosesser
3. WHEN cache_geometry er true THEN systemet SHALL cache geometri per GUID for gjenbruk
4. WHEN store IFC-filer prosesseres THEN systemet SHALL håndtere minnebruk effektivt

### Requirement 9

**User Story:** Som bruker, ønsker jeg automatisk enhetsdeteksjon og manuell overstyring, slik at koordinater og målestokk blir korrekt uavhengig av IFC-filens enheter.

#### Acceptance Criteria

1. WHEN auto_detect_units er true THEN systemet SHALL forsøke å detektere skalering fra IFC-enheter til meter
2. WHEN unit_scale_to_m er spesifisert THEN systemet SHALL bruke manuell skalering og overstyre automatisk deteksjon
3. WHEN enhetskonvertering utføres THEN alle koordinater og dimensjoner SHALL skaleres korrekt
4. WHEN enhetsdeteksjon feiler THEN systemet SHALL falle tilbake på standard skalering og logge advarsel

### Requirement 10

**User Story:** Som bruker, ønsker jeg konfigurerbare toleranser for geometrisk prosessering, slik at jeg kan balansere nøyaktighet mot ytelse.

#### Acceptance Criteria

1. WHEN slice_tol er spesifisert THEN systemet SHALL bruke denne toleransen for plan-snitt operasjoner
2. WHEN chain_tol er spesifisert THEN systemet SHALL bruke denne toleransen for polylinje-kjeding
3. WHEN toleranser er for strenge THEN systemet SHALL kunne håndtere dette uten å krasje
4. WHEN toleranser er for løse THEN systemet SHALL fortsatt produsere meningsfulle resultater