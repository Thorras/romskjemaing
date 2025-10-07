Kort svar
En IFC‑fil “forstår” plassering og etasjevis visning gjennom (1) den hierarkiske spatiale strukturen (Prosjekt → Bygning → Etasje → Rom) og (2) lokale plasseringer (koordinatsystemer) som lenkes relativt i kjeder. Etasjeplaner lages enten ved å bruke 2D “FootPrint”/“Plan”-representasjoner som ligger i filen, eller – oftere – ved å kutte 3D‑geometrien ved et plan rundt etasjens høyde. “Soner” (IfcZone) har ikke egen geometri; de er bare grupper av rom (IfcSpace), så sonenes innbyrdes plassering følger av rommenes plassering og grenser. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org]

Detaljert: Hvilke IFC‑begreper brukes?

1. Spatial struktur og etasjer

IfcSpatialStructureElement definerer prosjektets romlige hierarki (Site/Building/BuildingStorey/Space) ved hjelp av dekomponering gjennom IfcRelAggregates. Dette er “treet” som alle plasseringer/innhold henger på. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org]
IfcBuildingStorey har attributtet Elevation (etasjens nivå) og kan ha høyder (Gross/Net) som BaseQuantities. Dette brukes av visere for å vite hvor de skal klippe/tegne en planvisning. [ifc43-docs...gsmart.org], [standards....gsmart.org]
IfcRelContainedInSpatialStructure knytter bygningsdeler til “sin” etasje (eller annet spatialt nivå), slik at viseren enkelt kan filtrere “alt som ligger i denne etasjen”. [standards....gsmart.org]

2. Plassering (koordinatsystemer i kjede)

IfcLocalPlacement gir lokal posisjon/rotasjon og kan peke relativt til en annen objekts plassering (PlacementRelTo). Hele bygget blir dermed et nett av koordinatsystemer, vanligvis slik at rom og elementer er plassert relativt til etasjens plassering. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org]

3. Geometri for planvisning

2D “Plan”-kontekst: IFC kan ha en IfcGeometricRepresentationContext med ContextType='Plan' (og subkontekster via IfcGeometricRepresentationSubContext) for skala-/visningsspesifikke 2D‑representasjoner. Hvis de finnes, kan viseren bruke dem direkte som plantegninger. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org]
FootPrint: Mange rom (IfcSpace) og dekker (IfcSlab) kan ha en ‘FootPrint’‑representasjon (2D grenser) som kan tegnes som plan uten kutt. [ifc43-docs...gsmart.org]
Snitt av 3D: Når 2D ikke er levert, tar visere typisk Body‑geometri og lager et snitt i høyde rundt etasjens Elevation for å generere planlinjer fyldig nok for visning. (Dette er en normal tolking basert på at IFC definerer 3D “Model”-kontekst som obligatorisk, mens 2D er valgfritt.) [standards....gsmart.org]

4. Soner (IfcZone) versus rom (IfcSpace)

IfcZone er en gruppe av rom (eller andre soner), uten egen form/mesh. Innholdet knyttes via IfcRelAssignsToGroup. Dermed avledes soneplassering visuelt ved å farge/markere medlemmene (rommene) – ikke ved å plassere en egen sone‑geometri. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org]
Soner kan refereres til en spatial struktur (f.eks. bygg/etasje) som “dekker” den, ved IfcRelReferencedInSpatialStructure (nyttig for å angi hvilke etasjer en sone gjelder for), men selve plasseringen følger fortsatt av de rommene som er gruppert. [ifc43-docs...gsmart.org], [github.com]
IfcSpace bygger den romlige hierarkien under etasje og kan dessuten ha ‘FootPrint’ og/eller 3D‑geometri brukt i plan. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org]

5. Naboskap/avgrensning mellom rom/soner

IfcRelSpaceBoundary beskriver fysiske/virtuelle grenser for rom (vegger, dører, åpninger osv.), inkludert 1. og 2. nivå (2a/2b) for analyser. Slike grenser kan brukes til å avlede naboskap mellom rom, og indirekte mellom soner (via hvilke rom som grenser). [standards....gsmart.org], [ifc43-docs...gsmart.org]

Hvordan en viewer typisk lager “etasjevis planvisning” (praktisk algoritme)

Bygg spatialt tre
Gå fra IfcProject → IfcBuilding → IfcBuildingStorey → IfcSpace ved IfcRelAggregates. For elementer (vegger, dører …) bruk IfcRelContainedInSpatialStructure for å legge dem i riktig etasje. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org], [standards....gsmart.org]

Regn ut transformasjoner
Løs opp IfcLocalPlacement‑kjedene til matriser i verdenskoordinater for etasjen, rommene og elementene. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org]

Bestem snitthøyde
Bruk IfcBuildingStorey.Elevation (og ev. Net/GrossHeight i BaseQuantities) til å definere klippeplan og visningsområde for etasjen. [ifc43-docs...gsmart.org]

Hent geometri for plan

Hvis tilgjengelig: tegn Plan‑/FootPrint‑representasjoner. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org]
Ellers: lag et snitt av 3D “Body” omtrent ved dørhøyde/standard cut plane for å hente vegglinjer, døråpninger osv. (3D “Model”-kontekst er obligatorisk, så du kan alltid falle tilbake på snitt). [standards....gsmart.org]

Fargelegg soner
Finn IfcRelAssignsToGroup → IfcZone for hvert IfcSpace og farge/fyll footprints etter sone. Sonens utstrekning i plan = union av footprints for tilhørende rom i etasjen. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org]

(Valgfritt) Naboskap
Bruk IfcRelSpaceBoundary til å bygge en graf over hvilke rom som grenser til hverandre, for å markere sonegrenser tydelig eller beregne sone‑til‑sone‑kontakt. [standards....gsmart.org]

Vanlige fallgruver og tips

Sone ≠ geometri: Ikke let etter en mesh på IfcZone – den finnes normalt ikke. Visualisér heller rommene i sonen. [ifc43-docs...gsmart.org]
Manglende 2D: Mange modeller leverer ikke “Plan”/FootPrint. Sørg for en robust 3D‑til‑2D snittprosess. (IFC gjør 3D‑kontekst obligatorisk, 2D valgfri.) [standards....gsmart.org]
Etasjehøyder: Hvis GrossHeight/NetHeight mangler, bruk avstanden til neste etasjes Elevation eller elementenes faktiske utstrekning som fallback i din app. (IFC beskriver hvor høyder kan lagres, men krever ikke at de alltid er fylt ut.) [ifc43-docs...gsmart.org]
Zoner i infrastruktur/avanserte bruk: IfcSpatialZone (ikke bare IfcZone) kan også forekomme og være del av spatial struktur; sjekk referanser/aggregat ift. hvor det “bor”. [ifc43-docs...gsmart.org], [github.com]

Relevante spesifikasjonsnoder (for videre lesning)

Plassering: IfcLocalPlacement, Product Local Placement. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org]
Etasjer: IfcBuildingStorey (Elevation, høyder). [ifc43-docs...gsmart.org], [standards....gsmart.org]
Spatial struktur: IfcSpatialStructureElement, IfcRelAggregates, IfcRelContainedInSpatialStructure. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org], [standards....gsmart.org]
Plan/2D‑kontekst: IfcGeometricRepresentationContext (‘Plan’), IfcGeometricRepresentationSubContext. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org]
FootPrint: Konsept for 2D av rom/dekker. [ifc43-docs...gsmart.org]
Zoner: IfcZone (ingen egen shape) + IfcRelAssignsToGroup; referanser til spatial struktur. [ifc43-docs...gsmart.org], [ifc43-docs...gsmart.org], [github.com]
Rom og grenser: IfcSpace, IfcRelSpaceBoundary(2ndLevel). [ifc43-docs...gsmart.org], [standards....gsmart.org], [ifc43-docs...gsmart.org]
