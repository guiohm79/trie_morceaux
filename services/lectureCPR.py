import re
import os

def trouve_vsti(fichier):
    print(f"Analyse de : {os.path.basename(fichier)}")
    
    with open(fichier, "rb") as f:
        data = f.read()
    
    # Liste BEAUCOUP plus complète
    vsti_connus = [
        # Synthés populaires
        "Serum", "Spire", "Sylenth1", "Massive", "Massive X", "FM8", "Pigments", "Diva", "Zebra", 
        "Omnisphere", "Nexus", "Vanguard", "Dune", "Avenger", "Phase Plant", "Vital", "Synth1", "Hive", "Repro",
        
        # Instruments samplés
        "Kontakt", "PLAY", "Halion", "Falcon", "Padshop", "SampleTank", "Iris", "Analog Lab",
        "LABS", "Spitfire", "Session Strings", "Addictive Drums", "Superior Drummer",
        "EZdrummer", "Battery", "Drumlab", "Abbey Road Drums",
        
        # Boîtes à rythmes
        "Kick 2", "Kick 3", "Punch", "Punchbox", "Drumbrute", "TR-8", "Addictive Drums", "BFD",
        
        # Workstations
        "Komplete Kontrol", "Maschine", "V-Station", "MPC", "Reason Rack", "Arturia V",
        "CODEX", "HALion Sonic", "Keyscape",
        
        # Plugins Steinberg/Cubase
        "REVerence", "Groove Agent", "Padshop", "Retrologue", "Halion", "LoopMash",
        "Mystic", "Prologue", "Embracer", "Backbone", "VST Amp Rack",
        
        # Effets
        "FabFilter", "Soundtoys", "Valhalla", "Serum FX", "OTT", "Soothe", "Pro-Q", "Pro-C",
        "Pro-L", "CLA-76", "Waves", "SSL", "Decapitator", "EchoBoy", "Saturn", "Pusher",
        "Sausage Fattener", "Ozone", "Neutron", "Nectar", "Trash", "Effectrix", 
        "Glitch", "RX", "iZotope", "PingPongDelay", "Replika", "Compressor", "Squasher"
    ]
    
    trouvés = set()  # On utilise un set pour éviter les doublons
    
    # Cherchons les VSTi numérotés (comme "Serum 01", "Kick 2 01", etc.)
    for vsti in vsti_connus:
        pattern = re.compile(f"{vsti}\\s+\\d{{2}}".encode('utf-8'))
        matches = pattern.findall(data)
        for match in matches:
            trouvés.add(match.decode('utf-8', errors='ignore'))
    
    # Cherchons aussi les instances sans numéro
    for vsti in vsti_connus:
        # On évite les faux positifs en vérifiant que ce n'est pas au milieu d'un mot
        pattern = re.compile(rb'(?<!\w)' + vsti.encode('utf-8') + rb'(?!\w)')
        matches = pattern.findall(data)
        if matches:
            if not any(vsti in déjà_trouvé for déjà_trouvé in trouvés):
                trouvés.add(vsti)
    
    # Cherchons aussi les entrées de type "Plugin Nam..."
    plugin_pattern = re.compile(rb'Plugin\s+Nam[^\n\r]{2,40}')
    plugin_matches = plugin_pattern.findall(data)
    
    for match in plugin_matches:
        texte = match.decode('utf-8', errors='ignore')
        # On extrait le nom du plugin si on le trouve
        for vsti in vsti_connus:
            if vsti in texte and vsti not in trouvés and not any(vsti in déjà_trouvé for déjà_trouvé in trouvés):
                trouvés.add(vsti)
    
    print("\nListe des plugins :")
    for vsti in sorted(trouvés):
        print(f"→ {vsti}")
    
    return trouvés

if __name__ == "__main__":
    trouve_vsti("monprojet.cpr")