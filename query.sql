SELECT 
    z.kod_zakaza,
    z.nomer_dokumenta,
    k.naimenovanie AS pokupatel,
    SUM(sz.kolichestvo * sz.cena) AS summa_prodazhi,
    ROUND(SUM(m.cena * ss.norma_rashoda / NULLIF(sp.kolichestvo_vyhoda, 0) * sz.kolichestvo)::numeric, 2) AS stoimost_materialov_vsego,
    ROUND((SUM(sz.kolichestvo * sz.cena) - SUM(m.cena * ss.norma_rashoda / NULLIF(sp.kolichestvo_vyhoda, 0) * sz.kolichestvo))::numeric, 2) AS pribyl
FROM zakaz z
JOIN kontragent k ON k.kod_kontragenta = z.kod_kontragenta
JOIN stroka_zakaza sz ON sz.kod_zakaza = z.kod_zakaza
JOIN produkciya p ON p.kod_produkcii = sz.kod_produkcii
JOIN specifikaciya sp ON sp.kod_produkcii = p.kod_produkcii
JOIN stroka_specifikacii ss ON ss.kod_specifikacii = sp.kod_specifikacii
JOIN material m ON m.kod_materiala = ss.kod_materiala
GROUP BY z.kod_zakaza, z.nomer_dokumenta, k.naimenovanie;
