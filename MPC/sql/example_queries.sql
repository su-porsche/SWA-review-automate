-- Nützliche SQL-Abfragen für hierarchische Chunk-Suche

-- 1. Alle verfügbaren PDFs anzeigen
SELECT DISTINCT
    d.metadata->>'pdf' as pdf_name,
    COUNT(DISTINCT d.id) as documents,
    COUNT(c.id) as chunks
FROM documents d
LEFT JOIN chunks c ON d.id = c.document_id
GROUP BY d.metadata->>'pdf'
ORDER BY pdf_name;

-- 2. Alle Chunks aus Kapitel 5 (inkl. Unterkapitel) von einem bestimmten Dokument
SELECT DISTINCT
    c.id,
    d.metadata->>'section_number' as section,
    LEFT(c.chunk_text, 80) as chunk_preview,
    STRING_AGG(DISTINCT cc.category, ' | ') as all_categories
FROM chunks c
JOIN documents d ON c.document_id = d.id
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category LIKE '5%'
  AND d.metadata->>'pdf' = 'Leitfaden Software Architektur Dokumentation (English) _ VR6.0.2.pdf'
GROUP BY c.id, d.metadata, c.chunk_text
ORDER BY d.metadata->>'section_number', c.id
LIMIT 20;

-- 3. Hierarchie eines einzelnen Chunks anzeigen
SELECT
    c.id,
    LEFT(c.chunk_text, 100) as chunk_text,
    ARRAY_AGG(cc.category ORDER BY cc.category_level) as category_hierarchy,
    ARRAY_AGG(cc.category_level ORDER BY cc.category_level) as levels
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE c.id = 1443  -- Chunk-ID hier anpassen
GROUP BY c.id, c.chunk_text;

-- 4. Anzahl Chunks pro Hauptkapitel (nur erste Ebene)
SELECT
    REGEXP_REPLACE(category, '^(\d+).*', '\1') as main_chapter,
    COUNT(DISTINCT chunk_id) as unique_chunks,
    COUNT(*) as total_links
FROM chunk_categories
WHERE category ~ '^\d+ '  -- Nur Hauptkapitel
GROUP BY main_chapter
ORDER BY main_chapter::int;

-- 5. Alle Chunks aus Kapitel 5.2 (nur 5.2, nicht 5.2.1 etc.)
SELECT DISTINCT
    c.id,
    d.metadata->>'section_number' as section,
    LEFT(c.chunk_text, 80) as chunk_preview
FROM chunks c
JOIN documents d ON c.document_id = d.id
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category ~ '^5\.2 '  -- Genau 5.2
  AND d.metadata->>'pdf' LIKE '%Leitfaden%'
ORDER BY c.id
LIMIT 10;

-- 6. Chunks auf bestimmter Hierarchie-Ebene (z.B. nur zweite Ebene wie 5.1, 5.2)
SELECT DISTINCT
    c.id,
    cc.category,
    LEFT(c.chunk_text, 60) as preview
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE cc.category_level = 1  -- Erste Ebene der Hierarchie
  AND cc.category ~ '^\d+\.\d+ '  -- Pattern: "X.Y ..."
ORDER BY cc.category, c.id
LIMIT 15;

-- 7. Chunks die zu mehreren Kapiteln gehören (hierarchisch verknüpft)
SELECT
    c.id,
    COUNT(DISTINCT cc.category) as category_count,
    STRING_AGG(DISTINCT cc.category, ' → ' ORDER BY cc.category_level) as hierarchy,
    LEFT(c.chunk_text, 60) as preview
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id
GROUP BY c.id, c.chunk_text
HAVING COUNT(DISTINCT cc.category) > 1
ORDER BY category_count DESC, c.id
LIMIT 10;

-- 8. Volltext-Suche mit Kategorie-Filter
SELECT DISTINCT
    c.id,
    d.metadata->>'section_number' as section,
    cc.category,
    LEFT(c.chunk_text, 100) as chunk_preview
FROM chunks c
JOIN documents d ON c.document_id = d.id
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE c.chunk_text ILIKE '%security%'  -- Suchbegriff hier anpassen
  AND cc.category LIKE '5%'  -- Nur in Kapitel 5
ORDER BY c.id
LIMIT 10;

-- 9. Statistik: Durchschnittliche Kategorien pro Chunk
SELECT
    COUNT(DISTINCT c.id) as total_chunks,
    COUNT(*) as total_category_links,
    ROUND(COUNT(*)::numeric / COUNT(DISTINCT c.id), 2) as avg_categories_per_chunk
FROM chunks c
JOIN chunk_categories cc ON c.id = cc.chunk_id;

-- 10. Alle Unterkapitel von Kapitel 5 mit Chunk-Anzahl
SELECT
    cc.category,
    COUNT(DISTINCT cc.chunk_id) as chunk_count,
    MIN(cc.category_level) as level
FROM chunk_categories cc
WHERE cc.category LIKE '5%'
GROUP BY cc.category
ORDER BY cc.category;

-- 11. Helper: Finde Chunks mit bestimmtem Text UND in bestimmtem Dokument UND Kapitel
SELECT DISTINCT
    c.id,
    d.title as document,
    d.metadata->>'pdf' as pdf,
    cc.category,
    c.chunk_text
FROM chunks c
JOIN documents d ON c.document_id = d.id
JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE c.chunk_text ILIKE '%microcontroller%'
  AND cc.category LIKE '5%'
  AND d.metadata->>'pdf' LIKE '%VR6.0.2%'
LIMIT 5;

-- 12. Zeige alle Chunks eines Dokuments mit ihrer Hierarchie
SELECT
    c.id,
    d.metadata->>'section_number' as section,
    ARRAY_AGG(DISTINCT cc.category ORDER BY cc.category_level) as categories,
    LEFT(c.chunk_text, 60) as preview
FROM chunks c
JOIN documents d ON c.document_id = d.id
LEFT JOIN chunk_categories cc ON c.id = cc.chunk_id
WHERE d.id = 1234  -- Dokument-ID hier anpassen
GROUP BY c.id, d.metadata, c.chunk_text
ORDER BY c.id;
