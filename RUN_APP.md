# 🏃‍♂️ Kjør IFC Room Schedule Applikasjonen

## 🚀 **Rask Start**

### **Windows (PowerShell/CMD)**
```cmd
python main.py
```

### **macOS/Linux (Terminal)**
```bash
python3 main.py
```

## 📋 **Steg-for-Steg Guide**

### **1. Sjekk Python Installation**
```bash
python --version
# Skal vise Python 3.8 eller høyere
```

### **2. Sjekk Avhengigheter**
```bash
pip list | findstr -i "pyqt6 ifcopenshell pandas"
# Skal vise alle pakker installert
```

### **3. Kjør Applikasjonen**
```bash
python main.py
```

## 🔧 **Hvis Noe Mangler**

### **Installer Avhengigheter**
```bash
pip install -r requirements.txt
```

### **Opprett Virtual Environment (Anbefalt)**
```bash
# Opprett
python -m venv venv

# Aktiver (Windows)
venv\Scripts\activate

# Aktiver (macOS/Linux)
source venv/bin/activate

# Installer
pip install -r requirements.txt

# Kjør
python main.py
```

## 🎯 **Alternative Kjøremetoder**

### **Som Python Modul**
```bash
python -m ifc_room_schedule
```

### **Med Debugging**
```bash
python -u main.py
```

### **Med Logging**
```bash
python main.py --verbose
```

## 🐛 **Feilsøking**

### **"ModuleNotFoundError"**
```bash
pip install -r requirements.txt
```

### **"Qt platform plugin could not be initialized"**
```bash
# Windows
set QT_QPA_PLATFORM=windows

# Linux
export QT_QPA_PLATFORM=xcb

# macOS
export QT_QPA_PLATFORM=cocoa
```

### **"Permission denied"**
```bash
# Sjekk filrettigheter
ls -la main.py

# Gi kjøretillatelse (Unix/Linux/macOS)
chmod +x main.py
```

## 📊 **Forventet Oppførsel**

### **Ved Oppstart**
1. **Vindu åpnes** (2-5 sekunder)
2. **Velkomstskjerm** vises
3. **Meny og verktøylinje** er tilgjengelig
4. **Status bar** viser "Ready to load IFC file..."

### **Første Gang**
- Applikasjonen kan ta litt lengre tid første gang
- Windows Defender kan spørre om tillatelse
- Alle moduler lastes og initialiseres

## 🎮 **Bruksanvisning**

### **Last IFC Fil**
1. **File → Open** eller **Ctrl+O**
2. **Velg .ifc fil** fra filutforsker
3. **Vent** på parsing (1-30 sekunder)

### **Utforsk Data**
1. **Spaces panel** viser alle rom
2. **Klikk på rom** for detaljer
3. **Legg til beskrivelser** i editor
4. **Export** data når ferdig

## 💡 **Tips**

### **Ytelse**
- Lukk andre tunge programmer
- Bruk SSD for raskere fil-tilgang
- Ha minst 4GB RAM tilgjengelig

### **Filer**
- Test med små IFC filer først
- Sjekk at filer ikke er korrupte
- Bruk filer fra kjente BIM-verktøy

### **Utvikling**
- Bruk virtual environment
- Kjør tester: `pytest tests/`
- Aktiver logging for debugging

---

**Klar til å kjøre? Bare skriv `python main.py`!** 🚀