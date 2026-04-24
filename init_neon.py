import psycopg2
import bcrypt

NEON_CONN = "postgresql://neondb_owner:npg_D3z2uqPSwdtj@ep-delicate-band-acgfpuaz.sa-east-1.aws.neon.tech/neondb?sslmode=require"

def init_neon_db():
    conn = psycopg2.connect(NEON_CONN)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sets (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES usuarios(id) ON DELETE CASCADE,
            nombre_set TEXT NOT NULL,
            pieza TEXT NOT NULL,
            kundun INTEGER DEFAULT 1,
            luck BOOLEAN DEFAULT FALSE,
            nivel_bs INTEGER DEFAULT 0,
            add_lif INTEGER DEFAULT 0,
            opt_sd BOOLEAN DEFAULT FALSE,
            opt_dd BOOLEAN DEFAULT FALSE,
            opt_dsr BOOLEAN DEFAULT FALSE,
            opt_ref BOOLEAN DEFAULT FALSE,
            opt_hp BOOLEAN DEFAULT FALSE,
            opt_zen BOOLEAN DEFAULT FALSE,
            obtenido BOOLEAN DEFAULT FALSE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS premios_sets (
            id SERIAL PRIMARY KEY,
            nombre_set TEXT UNIQUE NOT NULL,
            bonus_desc TEXT
        )
    ''')
    
    premios = [
        ('Leather', '1000 HP'), ('Bronce', '15 ATK SPEED'), ('Violent Wind', '3% Critico Resist'),
        ('Silk', 'ATK SPEED 20'), ('Pad', '1500 HP'), ('Scale', 'DMG 4%'),
        ('Vine', '1000 HP'), ('Brass', '2% SD'), ('Wind', 'DEF 2%'),
        ('Red Winged', '1500 HP'), ('Sphinix', '1500 HP'), ('Bone', '2% DMG'),
        ('Plate', '1% DD'), ('Spirit', 'EDMG 3% RESIST'), ('Legendary', '3% DEF'),
        ('Adamantine', 'CRT RESIST 4%'), ('Ancient', '5% EX DMG RESIST (3)'),
        ('Demonic', '2% REFLECT'), ('Sacred Fire', '5% DEF (2)'), ('Dragon', '1500HP (2)'),
        ('Grand Soul', '2% DEF'), ('Guardian', 'ATK SPEED 25'), ('Light Plate', '2% EX DMG (1)'),
        ('Holy Spirit', '2% DD'), ('Storm Crow', '4% EXCE'), ('Storm Zahard', '2000HP'),
        ('Dark Steel', '2000 HP'), ('Thunder Hawk', '2000 HP'), ('Black Dragon', 'A Speed 30'),
        ('Dark Phoenix', '6% SD')
    ]
    
    for nombre, bonus in premios:
        cursor.execute('''
            INSERT INTO premios_sets (nombre_set, bonus_desc) 
            VALUES (%s, %s)
            ON CONFLICT (nombre_set) DO UPDATE SET bonus_desc = EXCLUDED.bonus_desc
        ''', (nombre, bonus))
    
    password = bcrypt.hashpw('mu2024'.encode(), bcrypt.gensalt()).decode()
    cursor.execute('''
        INSERT INTO usuarios (email, username, password_hash)
        VALUES (%s, %s, %s)
        ON CONFLICT (email) DO NOTHING
    ''', ('nehuy93@gmail.com', 'admin', password))
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Base de datos Neon configuradas!")

if __name__ == "__main__":
    init_neon_db()