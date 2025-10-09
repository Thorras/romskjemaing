# Kritisk Fix: Cosmetic Pen for Millimeter-koordinater

## Problem
IFC-filer bruker millimeter som koordinatenhet, noe som betyr at når rompolygoner tegnes med normale penner, blir linjene ekstremt tynne (f.eks. 1mm bred linje i et koordinatsystem med tusenvis av millimeter).

## Root Cause
- **IFC-koordinater**: Alle mål er i millimeter (mm)
- **Normale penner**: Skaleres med koordinatsystemet
- **Resultat**: 1px linje blir 1mm bred i et rom på 3000mm x 4000mm = usynlig

## Løsning: Cosmetic Pen
Bruker `pen.setCosmetic(True)` som gjør at pennen alltid er 1 pixel bred på skjermen, uavhengig av koordinatsystem-skala.

### Teknisk Implementasjon
```python
# FØR (feil - skaleres med koordinatsystem)
pen = QPen(self.COLOR_ROOM_BORDER, border_width)

# ETTER (riktig - alltid synlig på skjerm)
pen = QPen(self.COLOR_ROOM_BORDER, border_width)
pen.setCosmetic(True)  # KRITISK: Pen width i screen pixels, ikke world coordinates
```

## Endringer Implementert

### 1. Romgrenser
```python
# Room borders - alltid 1px på skjerm
pen = QPen(self.COLOR_ROOM_BORDER, 1.0)
pen.setCosmetic(True)
pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
pen.setCapStyle(Qt.PenCapStyle.SquareCap)
```

### 2. Selection Highlights
```python
# Selection borders - alltid synlige
selection_pen = QPen(self.COLOR_SELECTION_BORDER, self.ROOM_SELECTED_WIDTH)
selection_pen.setCosmetic(True)
```

### 3. Hover Effects
```python
# Hover borders - alltid synlige
hover_pen = QPen(self.COLOR_HOVER_BORDER, self.ROOM_HOVER_WIDTH)
hover_pen.setCosmetic(True)
```

### 4. Grid Lines
```python
# Grid lines - alltid synlige
grid_pen = QPen(self.COLOR_GRID, 0.25)
grid_pen.setCosmetic(True)
```

## Resultat

### Før Fix:
- ❌ Usynlige romgrenser (1mm bred i 3000mm koordinatsystem)
- ❌ Usynlige selection highlights
- ❌ Usynlig grid
- ❌ Ingen visuell feedback

### Etter Fix:
- ✅ Tydelige romgrenser (alltid 1px på skjerm)
- ✅ Synlige selection highlights
- ✅ Synlig grid overlay
- ✅ Profesjonelt utseende som ArchiCAD

## Teknisk Forklaring

### Cosmetic vs Normal Pen:
- **Normal Pen**: Bredde i world coordinates (mm) → skaleres med zoom
- **Cosmetic Pen**: Bredde i screen pixels → alltid samme størrelse på skjerm

### Hvorfor Dette Er Kritisk:
IFC-filer bruker millimeter, så et rom kan være 3000mm x 4000mm. En 1mm bred linje i dette koordinatsystemet blir mikroskopisk når hele rommet skal vises på skjermen.

Med cosmetic pen er linjen alltid 1 pixel bred på skjermen, uavhengig av zoom-nivå eller koordinatsystem-skala.

## Testing
- ✅ Test med ekte IFC-data (AkkordSvingen) - romgrenser nå synlige
- ✅ Test med syntetisk data - fungerer perfekt
- ✅ Alle zoom-nivåer - konsistent synlighet
- ✅ Selection og hover - fungerer som forventet

Denne fiksen er kritisk for alle IFC-baserte visualiseringer som bruker millimeter-koordinater!