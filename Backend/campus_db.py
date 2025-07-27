import sqlite3
import re

# This is your BUILDINGS data, now with all buildings and expanded, factual descriptions.
BUILDINGS = {
    "Lecture Hall Complex": {
        "lat": 8.683558103707359, "lng": 77.13498231455564, 
        "description": "The Lecture Hall Complex, commonly known as the LHC, is the primary academic hub for undergraduate and postgraduate classes. It features numerous lecture halls of various sizes, seminar rooms, and is equipped with modern audio-visual facilities for teaching.", 
        "aliases": ["lhc", "lecture halls", "lecture hall"]
    },
    "Physical Sciences Block": {
        "lat": 8.682521262142819, "lng": 77.1350371685667, 
        "description": "The Physical Sciences Block (PSB) houses the School of Physics. It contains faculty offices, advanced research laboratories for physics, and specialized equipment for experiments in various fields of physical science.", 
        "aliases": ["psb", "physics block", "physical science"]
    },
    "Biological Science Block, IISER TVM": {
        "lat": 8.681734690219086, "lng": 77.13735523514934, 
        "description": "The Biological Science Block is the headquarters for the School of Biology. It includes faculty offices, research labs for genetics, molecular biology, and ecology, as well as teaching labs for students.", 
        "aliases": ["bsb", "biology block", "biological science block", "dbs building"]
    },
    "Dept. of Chemical Sciences": {
        "lat": 320.62, "lng": 172.92, 
        "description": "The Department of Chemical Sciences building is the center for the School of Chemistry. It is equipped with state-of-the-art laboratories for organic, inorganic, physical, and theoretical chemistry research and teaching.", 
        "aliases": ["chemistry department", "chem block"]
    },
    "Library": {
        "lat": 8.681920078489515, "lng": 77.13392437090883, 
        "description": "The Central Library provides access to a vast collection of scientific books, journals, and digital resources. It offers quiet study areas, computer access, and support services for students and researchers.", 
        "aliases": ["iiser central library", "central library"]
    },
    "Animal House Block": {
        "lat": 8.681480148391024, "lng": 77.13805260950807, 
        "description": "The Animal House at IISER Thiruvananthapuram (IISER TVM) is a specialized facility designed to provide a controlled environment for the care and study of laboratory animals, particularly mice.It plays a crucial role in supporting research in biological sciences and related fields.", 
        "aliases": ["animal house", "animal facility"]
    },
    "IISER TVM Health Centre": {
        "lat": 8.683623824075873, "lng": 77.13245941243828, 
        "description": "The Health Centre provides primary medical care, first aid, and emergency services to all students, faculty, and staff on campus. It is staffed by qualified medical professionals.", 
        "aliases": ["health centre", "clinic", "hospital"]
    },
    "IISER TVM Shopping Centre": {
        "lat": 8.684229939019572, "lng": 77.13272693062969, 
        "description": "The Shopping Complex, often called ShopCom, houses several essential campus amenities, including a general store, eateries, and other student-run shops.", 
        "aliases": ["Shopping Complex", "shopping centre", "shopcom", "shops"]
    },
    "Central Dining Hall": {
        "lat": 347.53, "lng": 154.65, 
        "description": "The Central Dining Hall (CDH) is the main mess facility for hostel residents, serving breakfast, lunch, and dinner. It features a large seating capacity and a central kitchen.", 
        "aliases": ["cdh", "mess hall", "canteen"]
    },
    "Agasthya Hostel": {
        "lat": 8.68007, "lng": 77.136576, 
        "description": "Agasthya Hall of Residence is a permanent hostel building providing furnished accommodation primarily for male students at IISER Thiruvananthapuram.", 
        "aliases": ["agasthya"]
    },
    "Ponmudi Hostel": {
        "lat": 8.680537, "lng": 77.135906, 
        "description": "Ponmudi Hostel is a permanent hall of residence for female students, managed by dedicated wardens from the faculty.", 
        "aliases": ["ponmudi"]
    },
    "Visitors' Forest Retreat": {
        "lat": 8.682448845793244, "lng": 77.13310263238871, 
        "description": "The Visitors' Forest Retreat (VFR) serves as the campus guest house, providing comfortable accommodation for visiting faculty, conference attendees, and other official guests.", 
        "aliases": ["forest retreat", "guest house"]
    },
    "IISER TVM Indoor Sports Complex": {
        "lat": 8.678910683920078, "lng": 77.13498049288694, 
        "description": "The Indoor Sports Complex features facilities for a variety of indoor games, including badminton, table tennis, and a gymnasium for fitness activities.", 
        "aliases": ["indoor stadium", "sports complex"]
    },
    "Kathipara Stadium": {
        "lat": 8.686787382058368, "lng": 77.13056895919277, 
        "description": "Kathipara Stadium is the main outdoor sports facility on campus, featuring a full-size football ground and areas for athletic events.", 
        "aliases": ["stadium", "football ground"]
    },
    "Poultry farm": {
        "lat": 8.685457850899018, "lng": 77.13168742599625, 
        "description": "The poultry farm is a research and utility facility, often associated with biological science studies or campus sustainability initiatives.", 
        "aliases": ["poultry"]
    },
    "Thiruvananthapuram Central Railway Station": {
        "lat": 8.486848364860853, "lng": 76.95214645256466, 
        "description": "Thiruvananthapuram Central (TVC) is the primary railway station serving the city. It is a major hub for long-distance and local trains, located approximately 20-25 km from the IISER campus.", 
        "aliases": ["railway station", "central station", "train station"]
    },
    "Thiruvananthapuram International Airport": {
        "lat": 8.487130936935603, "lng": 76.92196659504725, 
        "description": "Thiruvananthapuram International Airport (TRV) is the closest airport to the campus, serving both domestic and international flights. It is situated about 25-30 km from IISER.", 
        "aliases": ["airport", "tvm airport"]
    },
    "I Cafe": {
        "lat": 8.680665982054032, "lng": 77.13678688931871, 
        "description": "I Cafe is a popular student-run eatery on campus, known for its snacks, beverages, and as a casual meeting spot.", 
        "aliases": ["i-cafe", "i cafe"]
    },
    "MOBEL Lab": {
        "lat": 8.682242857598077, "lng": 77.135774776028, 
        "description": "The Molecular Biophysics and Engineering Laboratory (MOBEL) is a specialized research facility focused on interdisciplinary studies at the intersection of biology, physics, and engineering.", 
        "aliases": ["mobel"]
    },
    "Central Instrumentation Facility Building": {
        "lat": 8.682592851841207, "lng": 77.13745920333834, 
        "description": "The Central Instrumentation Facility (CIF) houses a collection of high-end analytical instruments and equipment, providing sophisticated research support to all scientific departments on campus.", 
        "aliases": ["cif", "central instrumentation"]
    },
    "Residence Block C1, IISER TVM": {
        "lat": 8.685490511519728, "lng": 77.1264902852442, 
        "description": "The C1 Residence Block, located in the Kattippara residential complex, provides furnished apartment-style housing for the faculty and staff of the institute.", 
        "aliases": ["c1 quarters", "residence c1", "residence block", "faculty quarters", "faculty residence"]
    },
    "Director's Bungalow": {
        "lat": 8.686551221770518, "lng": 77.12820691906941, 
        "description": "This bungalow serves as the official on-campus residence for the Director of IISER Thiruvananthapuram.", 
        "aliases": ["director bungalow"]
    },
    "Community centre": {
        "lat": 8.687418795423712, "lng": 77.1308267544357, 
        "description": "The Community Centre is a multi-purpose venue for campus events, student gatherings, and recreational activities.", 
        "aliases": ["community hall"]
    },
    "IISER VITHURA Main gate": {
        "lat": 8.67793969519614, "lng": 77.13334274182657, 
        "description": "The main entrance and primary security checkpoint for the IISER campus in Vithura.", 
        "aliases": ["main gate", "gate 1"]
    },
    "Sulaimani Canteen": {
        "lat": 8.682507325369418, "lng": 77.13648746058396, 
        "description": "Sulaimani Canteen is a popular campus eatery, well-known for serving tea, coffee, and a variety of local snacks.", 
        "aliases": ["sulaimani"]
    },
    "Anamudi Block": {
        "lat": 8.6786226797446, "lng": 77.13585451303928, 
        "description": "Anamudi Block is a faculty residence. The A & D sections are for boys and are under the care of wardens Dr. Tanumoy Mandal (School of Physics) and Dr. Jerry Alfred Fereiro (School of Chemistry).", 
        "aliases": ["anamudi", "anamudi block", "anamudi residence", "anamudi faculty housing"]
    },
    "Phd Hostel 3": {
        "lat": 8.680282, "lng": 77.135699, 
        "description": "This hostel block provides dedicated, furnished accommodation for PhD research scholars on campus.", 
        "aliases": ["phd hostel 3", "phd hostel block 3"]
    },
    "Phd Hostel 4": {
        "lat": 8.679845, "lng": 77.136356, 
        "description": "This hostel block provides dedicated, furnished accommodation for PhD research scholars on campus.", 
        "aliases": ["phd hostel 4", "phd hostel block 4"]
    },
    "Phd Hostel 5": {
        "lat": 8.680004, "lng": 77.135479, 
        "description": "This hostel block provides dedicated, furnished accommodation for PhD research scholars on campus.", 
        "aliases": ["phd hostel 5", "phd hostel block 5"]
    },
    "Phd Hostel 6": {
        "lat": 8.680009, "lng": 77.135463, 
        "description": "This hostel block provides dedicated, furnished accommodation for PhD research scholars on campus.", 
        "aliases": ["phd hostel 6", "phd hostel block 6"]
    }
}

# Connect to the SQLite database
conn = sqlite3.connect('campus.db')
cursor = conn.cursor()

# --- Create the tables (IF NOT EXISTS makes this script safe to re-run) ---
cursor.execute('''
CREATE TABLE IF NOT EXISTS buildings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    lat REAL NOT NULL,
    lng REAL NOT NULL,
    description TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    building_id INTEGER,
    name TEXT NOT NULL,
    FOREIGN KEY (building_id) REFERENCES buildings (id)
)
''')

# --- Clear existing data to ensure a fresh build ---
print("Clearing old data from 'buildings' and 'aliases' tables...")
cursor.execute("DELETE FROM aliases")
cursor.execute("DELETE FROM buildings")
cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('buildings', 'aliases')")
print("Old data cleared.")

# --- Populate the tables ---
print("Populating database...")
for name, data in BUILDINGS.items():
    try:
        cursor.execute(
            "INSERT INTO buildings (name, lat, lng, description) VALUES (?, ?, ?, ?)",
            (name, data['lat'], data['lng'], data['description'])
        )
        building_id = cursor.lastrowid
        
        all_aliases = set()
        
        for alias in data.get('aliases', []):
            all_aliases.add(alias.lower().strip())
            
        all_aliases.add(name.lower().strip())
        
        simplified_name = re.sub(r'\b(block|centre|complex|building|, iiser tvm)\b', '', name.lower(), flags=re.IGNORECASE).strip()
        simplified_name = re.sub(r'\s+', ' ', simplified_name)
        if simplified_name and simplified_name != name.lower().strip():
            all_aliases.add(simplified_name)
            
        print(f" -> For '{name}', inserting aliases: {all_aliases}")
        for alias in all_aliases:
            if alias:
                cursor.execute(
                    "INSERT INTO aliases (building_id, name) VALUES (?, ?)",
                    (building_id, alias)
                )

    except sqlite3.IntegrityError as e:
        print(f"Error inserting '{name}': {e}. This might be due to a duplicate name.")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("✅ Database 'campus.db' created and populated successfully!")
