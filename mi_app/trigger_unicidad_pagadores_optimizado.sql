-- Trigger optimizado para verificar unicidad de pagadores
-- Usa arrays nativos de PostgreSQL para mejor rendimiento

-- Función optimizada
CREATE OR REPLACE FUNCTION verificar_unicidad_pagadores()
RETURNS TRIGGER AS $$
DECLARE
    nuevos_ruts TEXT[];
    rut_actual TEXT;
    coincidencia TEXT;
BEGIN
    -- Extrae todos los pagadores en un array
    SELECT ARRAY[
        NEW.pagador1, NEW.pagador2, NEW.pagador3, NEW.pagador4, NEW.pagador5, NEW.pagador6, NEW.pagador7, NEW.pagador8, NEW.pagador9, NEW.pagador10,
        NEW.pagador11, NEW.pagador12, NEW.pagador13, NEW.pagador14, NEW.pagador15, NEW.pagador16, NEW.pagador17, NEW.pagador18, NEW.pagador19, NEW.pagador20,
        NEW.pagador21, NEW.pagador22, NEW.pagador23, NEW.pagador24, NEW.pagador25, NEW.pagador26, NEW.pagador27, NEW.pagador28, NEW.pagador29, NEW.pagador30,
        NEW.pagador31, NEW.pagador32, NEW.pagador33, NEW.pagador34, NEW.pagador35, NEW.pagador36, NEW.pagador37, NEW.pagador38, NEW.pagador39, NEW.pagador40,
        NEW.pagador41, NEW.pagador42, NEW.pagador43, NEW.pagador44, NEW.pagador45, NEW.pagador46, NEW.pagador47, NEW.pagador48, NEW.pagador49, NEW.pagador50,
        NEW.pagador51, NEW.pagador52, NEW.pagador53, NEW.pagador54, NEW.pagador55, NEW.pagador56, NEW.pagador57, NEW.pagador58, NEW.pagador59, NEW.pagador60,
        NEW.pagador61, NEW.pagador62, NEW.pagador63, NEW.pagador64, NEW.pagador65, NEW.pagador66, NEW.pagador67, NEW.pagador68, NEW.pagador69, NEW.pagador70,
        NEW.pagador71, NEW.pagador72, NEW.pagador73, NEW.pagador74, NEW.pagador75, NEW.pagador76, NEW.pagador77, NEW.pagador78, NEW.pagador79, NEW.pagador80,
        NEW.pagador81, NEW.pagador82, NEW.pagador83, NEW.pagador84, NEW.pagador85, NEW.pagador86, NEW.pagador87, NEW.pagador88, NEW.pagador89, NEW.pagador90,
        NEW.pagador91, NEW.pagador92, NEW.pagador93, NEW.pagador94, NEW.pagador95, NEW.pagador96, NEW.pagador97, NEW.pagador98, NEW.pagador99, NEW.pagador100,
        NEW.pagador101, NEW.pagador102, NEW.pagador103, NEW.pagador104, NEW.pagador105, NEW.pagador106, NEW.pagador107, NEW.pagador108, NEW.pagador109, NEW.pagador110,
        NEW.pagador111, NEW.pagador112, NEW.pagador113, NEW.pagador114, NEW.pagador115, NEW.pagador116, NEW.pagador117, NEW.pagador118, NEW.pagador119, NEW.pagador120,
        NEW.pagador121, NEW.pagador122, NEW.pagador123, NEW.pagador124, NEW.pagador125, NEW.pagador126, NEW.pagador127, NEW.pagador128, NEW.pagador129, NEW.pagador130,
        NEW.pagador131, NEW.pagador132, NEW.pagador133, NEW.pagador134, NEW.pagador135, NEW.pagador136, NEW.pagador137, NEW.pagador138, NEW.pagador139, NEW.pagador140,
        NEW.pagador141, NEW.pagador142, NEW.pagador143, NEW.pagador144, NEW.pagador145, NEW.pagador146, NEW.pagador147, NEW.pagador148, NEW.pagador149, NEW.pagador150,
        NEW.pagador151, NEW.pagador152, NEW.pagador153, NEW.pagador154, NEW.pagador155, NEW.pagador156, NEW.pagador157, NEW.pagador158, NEW.pagador159, NEW.pagador160,
        NEW.pagador161, NEW.pagador162, NEW.pagador163, NEW.pagador164, NEW.pagador165, NEW.pagador166, NEW.pagador167, NEW.pagador168, NEW.pagador169, NEW.pagador170,
        NEW.pagador171, NEW.pagador172, NEW.pagador173, NEW.pagador174, NEW.pagador175, NEW.pagador176, NEW.pagador177, NEW.pagador178, NEW.pagador179, NEW.pagador180,
        NEW.pagador181, NEW.pagador182, NEW.pagador183, NEW.pagador184, NEW.pagador185, NEW.pagador186, NEW.pagador187, NEW.pagador188, NEW.pagador189, NEW.pagador190,
        NEW.pagador191, NEW.pagador192, NEW.pagador193, NEW.pagador194, NEW.pagador195, NEW.pagador196, NEW.pagador197, NEW.pagador198, NEW.pagador199, NEW.pagador200
    ] INTO nuevos_ruts;

    -- Revisa duplicados internos en el mismo array
    PERFORM rut_duplicado
    FROM unnest(nuevos_ruts) AS rut_duplicado
    WHERE rut_duplicado IS NOT NULL AND rut_duplicado <> ''
    GROUP BY rut_duplicado
    HAVING COUNT(*) > 1;

    IF FOUND THEN
        RAISE EXCEPTION 'Hay pagadores duplicados en el mismo cliente %.', NEW.cliente;
    END IF;

    -- Revisa existencia en otros clientes
    FOREACH rut_actual IN ARRAY nuevos_ruts LOOP
        IF rut_actual IS NOT NULL AND rut_actual <> '' THEN
            SELECT cliente INTO coincidencia
            FROM pagadores
            WHERE cliente <> NEW.cliente AND rut_actual = ANY(ARRAY[
                pagador1, pagador2, pagador3, pagador4, pagador5, pagador6, pagador7, pagador8, pagador9, pagador10,
                pagador11, pagador12, pagador13, pagador14, pagador15, pagador16, pagador17, pagador18, pagador19, pagador20,
                pagador21, pagador22, pagador23, pagador24, pagador25, pagador26, pagador27, pagador28, pagador29, pagador30,
                pagador31, pagador32, pagador33, pagador34, pagador35, pagador36, pagador37, pagador38, pagador39, pagador40,
                pagador41, pagador42, pagador43, pagador44, pagador45, pagador46, pagador47, pagador48, pagador49, pagador50,
                pagador51, pagador52, pagador53, pagador54, pagador55, pagador56, pagador57, pagador58, pagador59, pagador60,
                pagador61, pagador62, pagador63, pagador64, pagador65, pagador66, pagador67, pagador68, pagador69, pagador70,
                pagador71, pagador72, pagador73, pagador74, pagador75, pagador76, pagador77, pagador78, pagador79, pagador80,
                pagador81, pagador82, pagador83, pagador84, pagador85, pagador86, pagador87, pagador88, pagador89, pagador90,
                pagador91, pagador92, pagador93, pagador94, pagador95, pagador96, pagador97, pagador98, pagador99, pagador100,
                pagador101, pagador102, pagador103, pagador104, pagador105, pagador106, pagador107, pagador108, pagador109, pagador110,
                pagador111, pagador112, pagador113, pagador114, pagador115, pagador116, pagador117, pagador118, pagador119, pagador120,
                pagador121, pagador122, pagador123, pagador124, pagador125, pagador126, pagador127, pagador128, pagador129, pagador130,
                pagador131, pagador132, pagador133, pagador134, pagador135, pagador136, pagador137, pagador138, pagador139, pagador140,
                pagador141, pagador142, pagador143, pagador144, pagador145, pagador146, pagador147, pagador148, pagador149, pagador150,
                pagador151, pagador152, pagador153, pagador154, pagador155, pagador156, pagador157, pagador158, pagador159, pagador160,
                pagador161, pagador162, pagador163, pagador164, pagador165, pagador166, pagador167, pagador168, pagador169, pagador170,
                pagador171, pagador172, pagador173, pagador174, pagador175, pagador176, pagador177, pagador178, pagador179, pagador180,
                pagador181, pagador182, pagador183, pagador184, pagador185, pagador186, pagador187, pagador188, pagador189, pagador190,
                pagador191, pagador192, pagador193, pagador194, pagador195, pagador196, pagador197, pagador198, pagador199, pagador200
            ])
            LIMIT 1;
            
            IF coincidencia IS NOT NULL THEN
                RAISE EXCEPTION 'El pagador % ya está asociado al cliente %. No se puede duplicar entre clientes.', rut_actual, coincidencia;
            END IF;
        END IF;
    END LOOP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Crear el trigger
DROP TRIGGER IF EXISTS trigger_verificar_unicidad_pagadores ON pagadores;

CREATE TRIGGER trigger_verificar_unicidad_pagadores
    BEFORE INSERT OR UPDATE ON pagadores
    FOR EACH ROW
    EXECUTE FUNCTION verificar_unicidad_pagadores();

-- Comentario explicativo
COMMENT ON FUNCTION verificar_unicidad_pagadores() IS 
'Función optimizada que verifica la unicidad de pagadores usando arrays nativos de PostgreSQL. Más eficiente que la versión con loops.';

COMMENT ON TRIGGER trigger_verificar_unicidad_pagadores ON pagadores IS 
'Trigger optimizado que ejecuta la verificación de unicidad de pagadores antes de insertar o actualizar registros.'; 