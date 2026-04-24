import sqlite3

def actualizar_base_datos():
    conn = sqlite3.connect('mu_online.db')
    cursor = conn.cursor()

    # 1. Tabla de Sets (Mantiene tu estructura actual)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_set TEXT NOT NULL,
            pieza TEXT NOT NULL,
            luck BOOLEAN DEFAULT 0,
            nivel_bs INTEGER DEFAULT 0,
            add_lif INTEGER DEFAULT 0,
            opt_sd BOOLEAN DEFAULT 0,
            opt_dd BOOLEAN DEFAULT 0,
            opt_dsr BOOLEAN DEFAULT 0,
            opt_ref BOOLEAN DEFAULT 0,
            opt_hp BOOLEAN DEFAULT 0,
            opt_zen BOOLEAN DEFAULT 0,
            obtenido BOOLEAN DEFAULT 0
        )
    ''')

    # 2. Tabla de Premios (Donde se guardan los bonus por set completo)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS premios_sets (
            nombre_set TEXT PRIMARY KEY,
            bonus_desc TEXT
        )
    ''')

    # 3. Lista Consolidada de Premios (Todas tus capturas combinadas)
    premios = [
        # Tanda 1
        ('Leather', '1000 HP'), ('Bronce', '15 ATK SPEED'), ('Violent Wind', '3% Critico Resist'),
        ('Silk', 'ATK SPEED 20'), ('Pad', '1500 HP'), ('Scale', 'DMG 4%'),
        ('Vine', '1000 HP'), ('Brass', '2% SD'), ('Wind', 'DEF 2%'),
        ('Red Winged', '1500 HP'), ('Sphinix', '1500 HP'), ('Bone', '2% DMG'),
        ('Plate', '1% DD'), ('Spirit', 'EDMG 3% RESIST'), ('Legendary', '3% DEF'),
        
        # Tanda 2 (Nueva captura)
        ('Admantine', 'CRT RESIST 4%'),
        ('Ancient', '5% EX DMG RESIST (3)'),
        ('Demonic', '2% REFLECT'),
        ('Sacred Fire', '5% DEF (2)'),
        ('Dragon', '1500HP (2)'),
        ('Grand Soul', '2% DEF'),
        ('Guardian', 'ATK SPEED 25'),
        ('Light Plate', '2% EX DMG (1)'),
        ('Holy Spirit', '2% DD'),
        ('Storm Crow', '4% EXCE'),
        ('Storm Zahard', '2000HP'),
        ('Dark Steel', '2000 HP'),
        ('Thunder Hawk', '2000 HP'),
        ('Black Dragon', 'A Speed 30'),
        ('Dark Phoenix', '6% SD')
    ]

    # INSERT OR REPLACE asegura que si el set ya existe, se actualice el bonus
    cursor.executemany("INSERT OR REPLACE INTO premios_sets VALUES (?, ?)", premios)

    conn.commit()
    conn.close()
    print(f"¡Base de datos actualizada! Se configuraron {len(premios)} premios de sets.")

if __name__ == "__main__":
    actualizar_base_datos()

