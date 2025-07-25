import sqlite3

# This is your BUILDINGS data, now with standardized quotes.
BUILDINGS = {
    "I Cafe": {"lat": 8.680665982054032, "lng": 77.13678688931871, "description": "I Cafe is a popular spot for snacks and coffee.", "aliases": ["i-cafe", "i cafe"]},
    "Lecture Hall Complex": {"lat": 8.683558103707359, "lng": 77.13498231455564, "description": "The Lecture Hall Complex (LHC) is where most classes and academic events take place.", "aliases": ["lhc", "lecture halls", "lecture hall"]},
    "Physical Sciences Block": {"lat": 8.682521262142819, "lng": 77.1350371685667, "description": "The Physical Sciences Block (PSB) houses the physics department and its labs.", "aliases": ["psb", "physics block", "physical science"]},
    "Department of Physical Sciences": {"lat": 8.682622018019732, "lng": 77.13567553432202, "description": "The Department of Physical Sciences building.", "aliases": ["dps"]},
    "MOBEL Lab": {"lat": 8.682242857598077, "lng": 77.135774776028, "description": "The MOBEL Lab.", "aliases": ["mobel"]},
    "IISER Substation 4": {"lat": 8.682823529686484, "lng": 77.13655529887163, "description": "Electrical Substation 4.", "aliases": ["substation 4"]},
    "Central Instrumentation Facility Building": {"lat": 8.682592851841207, "lng": 77.13745920333834, "description": "The Central Instrumentation Facility Building (CIF).", "aliases": ["cif", "central instrumentation"]},
    "Biological Science Block, IISER TVM": {"lat": 8.681734690219086, "lng": 77.13735523514934, "description": "The Biological Science Block (BSB) is home to the biology department.", "aliases": ["bsb", "biology block", "biological science block"]},
    "VSR Lab": {"lat": 8.68138469516499, "lng": 77.13711383632304, "description": "The VSR Lab.", "aliases": ["vsr"]},
    "Animal House Block": {"lat": 8.681480148391024, "lng": 77.13805260950807, "description": "The Animal House Block.", "aliases": ["animal house"]},
    "ICREEE Greenhouse": {"lat": 8.680936082942651, "lng": 77.13767030114062, "description": "The ICREEE Greenhouse.", "aliases": ["icreee", "greenhouse"]},
    "Iiser Substation 2": {"lat": 8.680497633084729, "lng": 77.13693882392143, "description": "Electrical Substation 2.", "aliases": ["IISER substation 2"]},
    "Volleyball Court": {"lat": 8.681776252451229, "lng": 77.13498589592842, "description": "The campus volleyball court.", "aliases": ["volleyball"]},
    "Visitors' Forest Retreat": {"lat": 8.682448845793244, "lng": 77.13310263238871, "description": "Nestled in a scenic forest location, the Visitors Forest Retreat (VFR) provides comfortable guest house accommodation for campus visitors, conference attendees, and workshop participants.", "aliases": ["forest retreat"]},
    "Statue of Knowledge": {"lat": 8.682226281394632, "lng": 77.13353924861062, "description": "The 'Arivinte Shila' statue of knowledge.", "aliases": ["arivinte shila", "knowledge statue"]},
    "IISER TVM Health Centre": {"lat": 8.683623824075873, "lng": 77.13245941243828, "description": "The campus health centre.", "aliases": ["health centre", "clinic"]},
    "IISER TVM Shopping Centre": {"lat": 8.684229939019572, "lng": 77.13272693062969, "description": "The campus shopping complex.", "aliases": ["Shopping Complex", "shopping centre"]},
    "Project Office - Dept. of Infrastructure & Planning": {"lat": 8.683814397470826, "lng": 77.13282208283498, "description": "The Project Office for Infrastructure & Planning.", "aliases": ["project office", "infrastructure office"]},
    "Residence Block C1, IISER TVM": {"lat": 8.685490511519728, "lng": 77.1264902852442, "description": "The residential complex in Kattippara provides housing for the faculty and staff of our institute", "aliases": ["c1 quarters", "residence c1","residence block", "faculty quarters", "faculty residence"]},
    "Substation 3 IISER TVM": {"lat": 8.686996369460076, "lng": 77.12735412500257, "description": "Electrical Substation 3.", "aliases": ["iiser substation 3"]},
    "Director's Bungalow": {"lat": 8.686551221770518, "lng": 77.12820691906941, "description": "This bungalow serves as the official on-campus residence for the Director of IISER Thiruvananthapuram, Professor Jarugu Narasimha Moorthy", "aliases": ["director bungalow"]},
    "Department of Earth Environment and Sustainability Sciences": {"lat": 8.686289890825138, "lng": 77.12886700624243, "description": "The Department of Earth Environment and Sustainability Sciences.", "aliases": ["eess", "earth science"]},
    "C2 Quarters": {"lat": 8.685703924504221, "lng": 77.12644011856956, "description": "C2 Residence Block.", "aliases": ["c2 quarters", "residence c2"]},
    "Kathipara Stadium": {"lat": 8.686787382058368, "lng": 77.13056895919277, "description": "The Kathipara Stadium and football ground.", "aliases": ["stadium", "football ground"]},
    "Community centre": {"lat": 8.687418795423712, "lng": 77.1308267544357, "description": "The campus community centre.", "aliases": ["community hall"]},
    "Poultry farm": {"lat": 8.685457850899018, "lng": 77.13168742599625, "description": "The poultry farm.", "aliases": ["poultry"]},
    "CANARA BANK ATM": {"lat": 8.679424853436196, "lng": 77.1333417537436, "description": "An ATM for Canara Bank.", "aliases": ["canara atm"]},
    "IISER TVM second gate": {"lat": 8.678974836478497, "lng": 77.13418655672093, "description": "The second gate of the IISER TVM campus.", "aliases": ["second gate", "gate 2"]},
    "Mount IISERTVM": {"lat": 8.678862910731617, "lng": 77.13462149566395, "description": "A viewpoint on campus.", "aliases": ["mount iiser"]},
    "IISER TVM Indoor Sports Complex": {"lat": 8.678910683920078, "lng": 77.13498049288694, "description": "The indoor sports complex.", "aliases": ["indoor stadium", "sports complex"]},
    "Basketball court": {"lat": 8.67822411436848, "lng": 77.1346753452309, "description": "The campus basketball court.", "aliases": ["basketball"]},
    "Kabadi court": {"lat": 8.678105363643384, "lng": 77.13479685198737, "description": "The campus kabaddi court.", "aliases": ["kabaddi"]},
    "Tennis Court": {"lat": 8.67829918664407, "lng": 77.13516827604315, "description": "The campus tennis court.", "aliases": ["tennis"]},
    "Anamudi A block": {"lat": 8.6786226797446, "lng": 77.13585451303928, "description": "This faculty residence for boys is under the care of wardens Dr. Tanumoy Mandal (School of Physics) and Dr. Jerry Alfred Fereiro (School of Chemistry).The Anamudi D residence for boys is under the care of wardens Dr. Jerry Alfred Fereiro (School of Chemistry) and Dr. Tanumoy Mandal (School of Physics)", "aliases": ["anamudi block", "anamudi residence", "anamudi faculty housing"]},
    "Futsal court": {"lat": 8.678364704257847, "lng": 77.13596359296996, "description": "The campus futsal court.", "aliases": ["futsal"]},
    "IISER VITHURAMain gate": {"lat": 8.67793969519614, "lng": 77.13334274182657, "description": "The main entrance gate of the IISER campus.", "aliases": ["main gate", "gate 1"]},
    "DG yard": {"lat": 8.681696059695446, "lng": 77.1341959577972, "description": "The DG yard.", "aliases": ["dg yard"]},
    "STP sewage treatment plant": {"lat": 8.679652935248393, "lng": 77.13459441115718, "description": "The Sewage Treatment Plant.", "aliases": ["stp", "sewage plant"]},
    "CPWD office": {"lat": 8.679066159642666, "lng": 77.13390891564076, "description": "The CPWD office.", "aliases": ["cpwd"]},
    "Sulaimani Canteen": {"lat": 8.682507325369418, "lng": 77.13648746058396, "description": "Sulaimani Canteen, a place for tea and snacks.", "aliases": ["sulaimani"]},
    "J Cafe": {"lat": 8.67825944966011, "lng": 77.13612670153245, "description": "J Cafe, another spot for refreshments.", "aliases": ["j-cafe"]},
    "Ankita North Indian Restaurant": {"lat": 8.680232280005866, "lng": 77.13533104329053, "description": "Ankita, a restaurant serving North Indian food.", "aliases": ["ankita restaurant"]},
    "Thanal Canteen/Restaurant": {"lat": 8.680452578861068, "lng": 77.13524285100723, "description": "Thanal Canteen and Restaurant.", "aliases": ["thanal canteen", "thanal"]},
    "IISER Cooperative Society": {"lat": 8.680600623262412, "lng": 77.13631151075792, "description": "The campus cooperative society store.", "aliases": ["cooperative store", "cooperative society"]},
    "Department Of Biological Science Building": {"lat": 8.681850796088977, "lng": 77.13711550291133, "description": "The Department of Biological Science Building.", "aliases": ["dbs building"]},
    "Physical Sciences Block PSB Seminar Hall": {"lat": 8.682467698120522, "lng": 77.1349065257775, "description": "The seminar hall in the Physical Sciences Block.", "aliases": ["psb seminar hall"]},
    "Faculties and Staff Gym IISER TVM": {"lat": 8.68264942323973, "lng": 77.13333277715523, "description": "The gym for faculty and staff.", "aliases": ["faculty gym", "staff gym"]},
    "Shopping Complex": {"lat": 8.684241601150262, "lng": 77.13271502879515, "description": "The campus shopping complex.", "aliases": ["shopping complex"]},
    "Tasty Restaurant": {"lat": 8.68140397539519, "lng": 77.1345464974097, "description": "Tasty Restaurant on campus.", "aliases": ["tasty"]},
    "Cake World": {"lat": 8.681582430350973, "lng": 77.1355129776958, "description": "Cake World, a bakery on campus.", "aliases": ["cake shop"]},
    "RED CAFE RESTAURANT": {"lat": 8.682069517022708, "lng": 77.1348576550327, "description": "Red Cafe Restaurant.", "aliases": ["red cafe"]},
    "Kudumbashree Campus": {"lat": 8.681133705432966, "lng": 77.13431837655766, "description": "The Kudumbashree unit on campus.", "aliases": ["kudumbashree"]},
    "Agasthya Hostel": {"lat": 8.68007, "lng": 77.136576, "description": "Agasthya Hall of Residence is one of the boys' hostels at IISER Thiruvananthapuram (TVM). It's a permanent campus building, providing furnished accommodation for all students.", "aliases": ["agasthya"]},
    "Ponmudi Hostel": {"lat": 8.680537, "lng": 77.135906, "description": "Ponmudi Hostel for women. This women's hostel is under the guidance of wardens Dr. Pramitha M (School of Earth Environmental & Sustainability Sciences) and Dr. Pushpita Ghosh (School of Chemistry).", "aliases": ["ponmudi"]},
    "Phd Hostel 3": {"lat": 8.680282, "lng": 77.135699, "description": "This hostel provides dedicated accommodation for PhD research scholars on campus.", "aliases": ["phd hostel 3", "phd hostel block 3"]},
    "Phd Hostel 4": {"lat": 8.679845, "lng": 77.136356, "description": "This hostel provides dedicated accommodation for PhD research scholars on campus.", "aliases": ["phd hostel 4", "phd hostel block 4"]},
    "Phd Hostel 5": {"lat": 8.680004, "lng": 77.135479, "description": "This hostel provides dedicated accommodation for PhD research scholars on campus.", "aliases": ["phd hostel 5", "phd hostel block 5"]},
    "Phd Hostel 6": {"lat": 8.680009, "lng": 77.135463, "description": "This hostel provides dedicated accommodation for PhD research scholars on campus.", "aliases": ["phd hostel 6", "phd hostel block 6"]},
    "IISER Canteen": {"lat": 8.681324, "lng": 77.134068, "description": "The main IISER Canteen.", "aliases": ["main canteen"]},
    "North Indian Dhaba": {"lat": 8.68129, "lng": 77.134503, "description": "A dhaba serving North Indian food.", "aliases": ["dhaba"]},
    "SBI ATM": {"lat": 8.681793, "lng": 77.134173, "description": "An ATM for State Bank of India.", "aliases": ["sbi atm"]},
    "Resting Place beside Football Ground": {"lat": 8.686052107228857, "lng": 77.13032322749693, "description": "A resting place near the football ground.", "aliases": ["resting place"]},
    "Thirudhara Waterfall": {"lat": 8.68346078009775, "lng": 77.13596573014598, "description": "A beautiful natural waterfall located within the campus grounds.", "aliases": ["waterfall"]},
    "Library": {"lat": 8.681920078489515, "lng": 77.13392437090883, "description": "The Central Library at IISER Thiruvananthapuram.", "aliases": ["iiser central library", "central library"]},
    "Thiruvananthapuram Central Railway Station": {"lat": 8.486848364860853, "lng": 76.95214645256466, "description": "The main railway station connecting Thiruvananthapuram.", "aliases": ["railway station", "central station", "train station"]},
    "Thiruvananthapuram International Airport": {"lat": 8.487130936935603, "lng": 76.92196659504725, "description": "The primary airport serving the city of Thiruvananthapuram.", "aliases": ["airport", "tvm airport"]},
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

# --- **IMPROVEMENT**: Clear existing data to ensure a fresh build ---
print("Clearing old data from 'buildings' and 'aliases' tables...")
cursor.execute("DELETE FROM aliases")
cursor.execute("DELETE FROM buildings")
# Reset the auto-increment counter to be clean
cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('buildings', 'aliases')")
print("Old data cleared.")

# --- Populate the tables ---
print("Populating database...")
for name, data in BUILDINGS.items():
    try:
        # Insert the main building data
        cursor.execute(
            "INSERT INTO buildings (name, lat, lng, description) VALUES (?, ?, ?, ?)",
            (name, data['lat'], data['lng'], data['description'])
        )
        building_id = cursor.lastrowid
        
        # Insert all aliases for that building
        for alias in data.get('aliases', []):
            cursor.execute(
                "INSERT INTO aliases (building_id, name) VALUES (?, ?)",
                (building_id, alias)
            )
        # Also add the building's own name as a lowercase alias for easier searching
        cursor.execute(
            "INSERT INTO aliases (building_id, name) VALUES (?, ?)",
            (building_id, name.lower())
        )
    except sqlite3.IntegrityError as e:
        print(f"Error inserting '{name}': {e}. This might be due to a duplicate name.")

# Commit the changes and close the connection
conn.commit()
conn.close()

print("✅ Database 'campus.db' created and populated successfully!")