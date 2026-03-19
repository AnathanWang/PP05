CREATE TABLE edinica_izm (
    kod_ed_izm   SERIAL       PRIMARY KEY,
    oboznachenie VARCHAR(10)  NOT NULL UNIQUE,
    naimenovanie VARCHAR(50)  NOT NULL
);

CREATE TABLE rol_kontragenta (
    kod_roli     SERIAL       PRIMARY KEY,
    naimenovanie VARCHAR(30)  NOT NULL UNIQUE
);

CREATE TABLE status_zakaza (
    kod_statusa  SERIAL       PRIMARY KEY,
    naimenovanie VARCHAR(30)  NOT NULL UNIQUE
);

CREATE TABLE kontragent (
    kod_kontragenta  SERIAL        PRIMARY KEY,
    naimenovanie     VARCHAR(150)  NOT NULL,
    inn              VARCHAR(12)   CHECK (inn ~ '^\d{10,12}$'),
    adres            TEXT,
    telefon          VARCHAR(20),
    kontakt_familiya VARCHAR(60),
    kontakt_imya     VARCHAR(60),
    kontakt_otchestvo VARCHAR(60),
    kod_roli         INT           NOT NULL REFERENCES rol_kontragenta(kod_roli)
);

CREATE TABLE material (
    kod_materiala SERIAL          PRIMARY KEY,
    naimenovanie  VARCHAR(150)    NOT NULL,
    kod_ed_izm    INT             NOT NULL REFERENCES edinica_izm(kod_ed_izm),
    cena          NUMERIC(12,2)   NOT NULL CHECK (cena >= 0)
);

CREATE TABLE produkciya (
    kod_produkcii SERIAL          PRIMARY KEY,
    naimenovanie  VARCHAR(150)    NOT NULL,
    kod_ed_izm    INT             NOT NULL REFERENCES edinica_izm(kod_ed_izm)
);

CREATE TABLE specifikaciya (
    kod_specifikacii  SERIAL          PRIMARY KEY,
    naimenovanie      VARCHAR(150)    NOT NULL,
    kod_produkcii     INT             NOT NULL REFERENCES produkciya(kod_produkcii),
    kolichestvo_vyhoda NUMERIC(10,3)  NOT NULL CHECK (kolichestvo_vyhoda > 0)
);

CREATE TABLE stroka_specifikacii (
    kod_stroki_spec  SERIAL          PRIMARY KEY,
    kod_specifikacii INT             NOT NULL REFERENCES specifikaciya(kod_specifikacii) ON DELETE CASCADE,
    kod_materiala    INT             NOT NULL REFERENCES material(kod_materiala),
    norma_rashoda    NUMERIC(10,4)   NOT NULL CHECK (norma_rashoda > 0),
    UNIQUE (kod_specifikacii, kod_materiala)
);

CREATE TABLE zakaz (
    kod_zakaza       SERIAL          PRIMARY KEY,
    nomer_dokumenta  VARCHAR(20)     NOT NULL,
    data_zakaza      DATE            NOT NULL DEFAULT CURRENT_DATE,
    kod_kontragenta  INT             NOT NULL REFERENCES kontragent(kod_kontragenta),
    kod_statusa      INT             NOT NULL REFERENCES status_zakaza(kod_statusa),
    summa_itogo      NUMERIC(14,2)   DEFAULT 0 CHECK (summa_itogo >= 0)
);

CREATE TABLE stroka_zakaza (
    kod_stroki_zakaza SERIAL         PRIMARY KEY,
    kod_zakaza        INT            NOT NULL REFERENCES zakaz(kod_zakaza) ON DELETE CASCADE,
    kod_produkcii     INT            NOT NULL REFERENCES produkciya(kod_produkcii),
    kolichestvo       NUMERIC(10,3)  NOT NULL CHECK (kolichestvo > 0),
    cena              NUMERIC(12,2)  NOT NULL CHECK (cena >= 0),
    summa             NUMERIC(14,2)  GENERATED ALWAYS AS (kolichestvo * cena) STORED
);

CREATE TABLE proizvodstvo (
    kod_proizvodstva   SERIAL         PRIMARY KEY,
    nomer_dokumenta    VARCHAR(20)    NOT NULL,
    data_proizvodstva  DATE           NOT NULL DEFAULT CURRENT_DATE,
    kod_specifikacii   INT            NOT NULL REFERENCES specifikaciya(kod_specifikacii),
    Trang_produkcii      INT            NOT NULL REFERENCES produkciya(kod_produkcii),
    planov_kolichestvo NUMERIC(10,3)  NOT NULL CHECK (planov_kolichestvo > 0),
    fakt_kolichestvo   NUMERIC(10,3)  CHECK (fakt_kolichestvo >= 0)
);

CREATE TABLE rashod_materiala (
    kod_rashoda        SERIAL         PRIMARY KEY,
    kod_proizvodstva   INT            NOT NULL REFERENCES proizvodstvo(kod_proizvodstva) ON DELETE CASCADE,
    kod_materiala      INT            NOT NULL REFERENCES material(kod_materiala),
    kolichestvo        NUMERIC(10,4)  NOT NULL CHECK (kolichestvo > 0),
    stoimost           NUMERIC(12,2)  NOT NULL CHECK (stoimost >= 0)
);

CREATE TABLE raschet_sebestoimosti (
    kod_rascheta          SERIAL         PRIMARY KEY,
    kod_produkcii         INT            NOT NULL REFERENCES produkciya(kod_produkcii),
    kod_specifikacii      INT            NOT NULL REFERENCES specifikaciya(kod_specifikacii),
    stoimost_materialov   NUMERIC(14,2)  NOT NULL CHECK (stoimost_materialov >= 0),
    sebestoimost_ed       NUMERIC(12,2)  NOT NULL CHECK (sebestoimost_ed >= 0),
    data_rascheta         DATE           NOT NULL DEFAULT CURRENT_DATE
);

CREATE INDEX idx_stroka_zakaza_zakaz     ON stroka_zakaza(kod_zakaza);
CREATE INDEX idx_stroka_zakaza_prod      ON stroka_zakaza(kod_produkcii);
CREATE INDEX idx_stroka_spec_spec        ON stroka_specifikacii(kod_specifikacii);
CREATE INDEX idx_rashod_proizv           ON rashod_materiala(kod_proizvodstva);
CREATE INDEX idx_specifikaciya_prod      ON specifikaciya(kod_produkcii);

INSERT INTO edinica_izm (oboznachenie, naimenovanie) VALUES
    ('шт',  'Штука'),
    ('кг',  'Килограмм'),
    ('л',   'Литр'),
    ('уп',  'Упаковка');

INSERT INTO rol_kontragenta (naimenovanie) VALUES
    ('Покупатель'),
    ('Поставщик'),
    ('Покупатель и поставщик');

INSERT INTO status_zakaza (naimenovanie) VALUES
    ('Новый'),
    ('В работе'),
    ('Выполнен'),
    ('Отменён');

CREATE TEMP TABLE tmp_kontragenty_json (data JSONB);
INSERT INTO tmp_kontragenty_json (data) VALUES ('[
	{
		"id": "000000001",
		"name": "ООО \"Поставка\"",
		"inn": "",
		"addres": "г.Пятигорск",
		"phone": "+79198634592",
		"salesman": true,
		"buyer": true
	},
	{
		"id": "000000002",
		"name": "ООО \"Кинотеатр Квант\"",
		"inn": "26320045123",
		"addres": "г. Железноводск, ул. Мира, 123",
		"phone": "+79884581555",
		"salesman": true,
		"buyer": false
	},
	{
		"id": "000000008",
		"name": "ООО \"Новый JDTO\"",
		"inn": "26320045111",
		"addres": "г. Железноводсу",
		"phone": "+79884581555",
		"salesman": true,
		"buyer": false
	},
	{
		"id": "000000003",
		"name": "ООО \"Ромашка\"",
		"inn": "4140784214",
		"addres": "г. Омск, ул. Строителей, 294",
		"phone": "+79882584546",
		"salesman": false,
		"buyer": true
	},
	{
		"id": "000000009",
		"name": "ООО \"Ипподром\"",
		"inn": "5874045632",
		"addres": "г. Уфа, ул. Набережная,  37",
		"phone": "+79627486389",
		"salesman": true,
		"buyer": true
	},
	{
		"id": "000000010",
		"name": "ООО \"Ассоль\"",
		"inn": "2629011278",
		"addres": "г. Калуга, ул. Пушкина, 94",
		"phone": "+79184572398",
		"salesman": false,
		"buyer": true
	}
]');

INSERT INTO kontragent (naimenovanie, inn, adres, telefon, kod_roli)
SELECT
    elem->>'name'    AS naimenovanie,
    NULLIF(elem->>'inn', '')  AS inn,
    elem->>'addres'  AS adres,
    elem->>'phone'   AS telefon,
    CASE
        WHEN (elem->>'salesman')::boolean AND (elem->>'buyer')::boolean
            THEN (SELECT kod_roli FROM rol_kontragenta WHERE naimenovanie = 'Покупатель и поставщик')
        WHEN (elem->>'salesman')::boolean
            THEN (SELECT kod_roli FROM rol_kontragenta WHERE naimenovanie = 'Поставщик')
        ELSE
            (SELECT kod_roli FROM rol_kontragenta WHERE naimenovanie = 'Покупатель')
    END AS kod_roli
FROM tmp_kontragenty_json,
     jsonb_array_elements(data) AS elem;

INSERT INTO material (naimenovanie, kod_ed_izm, cena) VALUES
    ('Молоко нормализованное', (SELECT kod_ed_izm FROM edinica_izm WHERE oboznachenie='кг'), 34.00),
    ('Закваска сметанная',     (SELECT kod_ed_izm FROM edinica_izm WHERE oboznachenie='кг'), 45.00);

INSERT INTO produkciya (naimenovanie, kod_ed_izm) VALUES
    ('Сметана классическая 15% 540г.', (SELECT kod_ed_izm FROM edinica_izm WHERE oboznachenie='шт')),
    ('Кефир 2,5% 900г.',               (SELECT kod_ed_izm FROM edinica_izm WHERE oboznachenie='шт')),
    ('Кефир 3,2% 900г.',               (SELECT kod_ed_izm FROM edinica_izm WHERE oboznachenie='шт')),
    ('Молоко 2,5% 900г.',              (SELECT kod_ed_izm FROM edinica_izm WHERE oboznachenie='шт')),
    ('Молоко 3,2% 900г.',              (SELECT kod_ed_izm FROM edinica_izm WHERE oboznachenie='шт'));

INSERT INTO specifikaciya (naimenovanie, kod_produkcii, kolichestvo_vyhoda) VALUES
    ('Основная Сметана 15%', (SELECT kod_produkcii FROM produkciya WHERE naimenovanie = 'Сметана классическая 15% 540г.'), 1.0),
    ('Основной Кефир 2,5%', (SELECT kod_produkcii FROM produkciya WHERE naimenovanie = 'Кефир 2,5% 900г.'), 1.0),
    ('Основной Кефир 3,2%', (SELECT kod_produkcii FROM produkciya WHERE naimenovanie = 'Кефир 3,2% 900г.'), 1.0),
    ('Основное Молоко 2,5%', (SELECT kod_produkcii FROM produkciya WHERE naimenovanie = 'Молоко 2,5% 900г.'), 1.0);

INSERT INTO stroka_specifikacii (kod_specifikacii, kod_materiala, norma_rashoda)
SELECT (SELECT kod_specifikacii FROM specifikaciya WHERE naimenovanie = 'Основная Сметана 15%'), kod_materiala, norma FROM (VALUES ('Молоко нормализованное', 0.900), ('Закваска сметанная', 0.070)) AS v(mat_name, norma) JOIN material m ON m.naimenovanie = v.mat_name;

INSERT INTO stroka_specifikacii (kod_specifikacii, kod_materiala, norma_rashoda)
SELECT (SELECT kod_specifikacii FROM specifikaciya WHERE naimenovanie = 'Основной Кефир 2,5%'), kod_materiala, norma FROM (VALUES ('Молоко нормализованное', 0.950), ('Закваска сметанная', 0.050)) AS v(mat_name, norma) JOIN material m ON m.naimenovanie = v.mat_name;

INSERT INTO stroka_specifikacii (kod_specifikacii, kod_materiala, norma_rashoda)
SELECT (SELECT kod_specifikacii FROM specifikaciya WHERE naimenovanie = 'Основной Кефир 3,2%'), kod_materiala, norma FROM (VALUES ('Молоко нормализованное', 0.940), ('Закваска сметанная', 0.060)) AS v(mat_name, norma) JOIN material m ON m.naimenovanie = v.mat_name;

INSERT INTO stroka_specifikacii (kod_specifikacii, kod_materiala, norma_rashoda)
SELECT (SELECT kod_specifikacii FROM specifikaciya WHERE naimenovanie = 'Основное Молоко 2,5%'), kod_materiala, norma FROM (VALUES ('Молоко нормализованное', 1.000)) AS v(mat_name, norma) JOIN material m ON m.naimenovanie = v.mat_name;

INSERT INTO zakaz (nomer_dokumenta, data_zakaza, kod_kontragenta, kod_statusa)
VALUES (
    '2',
    '2025-06-06',
    (SELECT kod_kontragenta FROM kontragent WHERE naimenovanie LIKE '%Ассоль%' LIMIT 1),
    (SELECT kod_statusa FROM status_zakaza WHERE naimenovanie = 'Выполнен')
);

INSERT INTO stroka_zakaza (kod_zakaza, kod_produkcii, kolichestvo, cena)
SELECT
    (SELECT kod_zakaza FROM zakaz WHERE nomer_dokumenta = '2' AND data_zakaza = '2025-06-06'),
    kod_produkcii,
    qty,
    price
FROM (VALUES
    ('Кефир 2,5% 900г.',  12, 80.00),
    ('Кефир 3,2% 900г.',   9, 82.00),
    ('Молоко 2,5% 900г.', 10, 79.00)
) AS v(prod_name, qty, price)
JOIN produkciya p ON p.naimenovanie = v.prod_name;

UPDATE zakaz
SET summa_itogo = (SELECT SUM(summa) FROM stroka_zakaza WHERE kod_zakaza = zakaz.kod_zakaza)
WHERE nomer_dokumenta = '2';
