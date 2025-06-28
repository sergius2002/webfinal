-- Trigger final corregido para verificar unicidad de pagadores
-- Sin ambigüedades de variables

-- Función corregida sin ambigüedades
CREATE OR REPLACE FUNCTION verificar_unicidad_pagadores()
RETURNS TRIGGER AS $$
DECLARE
    nuevos_ruts TEXT[];
    rut_actual TEXT;
    cliente_coincidente TEXT;
    rut_duplicado TEXT;
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
    SELECT rut_valor INTO rut_duplicado
    FROM unnest(nuevos_ruts) AS rut_valor
    WHERE rut_valor IS NOT NULL AND rut_valor <> ''
    GROUP BY rut_valor
    HAVING COUNT(*) > 1
    LIMIT 1;

    IF rut_duplicado IS NOT NULL THEN
        RAISE EXCEPTION 'Hay pagadores duplicados en el mismo cliente %. RUT duplicado: %', NEW.cliente, rut_duplicado;
    END IF;

    -- Revisa existencia en otros clientes
    FOREACH rut_actual IN ARRAY nuevos_ruts LOOP
        IF rut_actual IS NOT NULL AND rut_actual <> '' THEN
            -- Buscar si el RUT existe en otros clientes
            SELECT p.cliente INTO cliente_coincidente
            FROM pagadores p
            WHERE p.cliente <> NEW.cliente 
            AND (
                p.pagador1 = rut_actual OR p.pagador2 = rut_actual OR p.pagador3 = rut_actual OR p.pagador4 = rut_actual OR p.pagador5 = rut_actual OR
                p.pagador6 = rut_actual OR p.pagador7 = rut_actual OR p.pagador8 = rut_actual OR p.pagador9 = rut_actual OR p.pagador10 = rut_actual OR
                p.pagador11 = rut_actual OR p.pagador12 = rut_actual OR p.pagador13 = rut_actual OR p.pagador14 = rut_actual OR p.pagador15 = rut_actual OR
                p.pagador16 = rut_actual OR p.pagador17 = rut_actual OR p.pagador18 = rut_actual OR p.pagador19 = rut_actual OR p.pagador20 = rut_actual OR
                p.pagador21 = rut_actual OR p.pagador22 = rut_actual OR p.pagador23 = rut_actual OR p.pagador24 = rut_actual OR p.pagador25 = rut_actual OR
                p.pagador26 = rut_actual OR p.pagador27 = rut_actual OR p.pagador28 = rut_actual OR p.pagador29 = rut_actual OR p.pagador30 = rut_actual OR
                p.pagador31 = rut_actual OR p.pagador32 = rut_actual OR p.pagador33 = rut_actual OR p.pagador34 = rut_actual OR p.pagador35 = rut_actual OR
                p.pagador36 = rut_actual OR p.pagador37 = rut_actual OR p.pagador38 = rut_actual OR p.pagador39 = rut_actual OR p.pagador40 = rut_actual OR
                p.pagador41 = rut_actual OR p.pagador42 = rut_actual OR p.pagador43 = rut_actual OR p.pagador44 = rut_actual OR p.pagador45 = rut_actual OR
                p.pagador46 = rut_actual OR p.pagador47 = rut_actual OR p.pagador48 = rut_actual OR p.pagador49 = rut_actual OR p.pagador50 = rut_actual OR
                p.pagador51 = rut_actual OR p.pagador52 = rut_actual OR p.pagador53 = rut_actual OR p.pagador54 = rut_actual OR p.pagador55 = rut_actual OR
                p.pagador56 = rut_actual OR p.pagador57 = rut_actual OR p.pagador58 = rut_actual OR p.pagador59 = rut_actual OR p.pagador60 = rut_actual OR
                p.pagador61 = rut_actual OR p.pagador62 = rut_actual OR p.pagador63 = rut_actual OR p.pagador64 = rut_actual OR p.pagador65 = rut_actual OR
                p.pagador66 = rut_actual OR p.pagador67 = rut_actual OR p.pagador68 = rut_actual OR p.pagador69 = rut_actual OR p.pagador70 = rut_actual OR
                p.pagador71 = rut_actual OR p.pagador72 = rut_actual OR p.pagador73 = rut_actual OR p.pagador74 = rut_actual OR p.pagador75 = rut_actual OR
                p.pagador76 = rut_actual OR p.pagador77 = rut_actual OR p.pagador78 = rut_actual OR p.pagador79 = rut_actual OR p.pagador80 = rut_actual OR
                p.pagador81 = rut_actual OR p.pagador82 = rut_actual OR p.pagador83 = rut_actual OR p.pagador84 = rut_actual OR p.pagador85 = rut_actual OR
                p.pagador86 = rut_actual OR p.pagador87 = rut_actual OR p.pagador88 = rut_actual OR p.pagador89 = rut_actual OR p.pagador90 = rut_actual OR
                p.pagador91 = rut_actual OR p.pagador92 = rut_actual OR p.pagador93 = rut_actual OR p.pagador94 = rut_actual OR p.pagador95 = rut_actual OR
                p.pagador96 = rut_actual OR p.pagador97 = rut_actual OR p.pagador98 = rut_actual OR p.pagador99 = rut_actual OR p.pagador100 = rut_actual OR
                p.pagador101 = rut_actual OR p.pagador102 = rut_actual OR p.pagador103 = rut_actual OR p.pagador104 = rut_actual OR p.pagador105 = rut_actual OR
                p.pagador106 = rut_actual OR p.pagador107 = rut_actual OR p.pagador108 = rut_actual OR p.pagador109 = rut_actual OR p.pagador110 = rut_actual OR
                p.pagador111 = rut_actual OR p.pagador112 = rut_actual OR p.pagador113 = rut_actual OR p.pagador114 = rut_actual OR p.pagador115 = rut_actual OR
                p.pagador116 = rut_actual OR p.pagador117 = rut_actual OR p.pagador118 = rut_actual OR p.pagador119 = rut_actual OR p.pagador120 = rut_actual OR
                p.pagador121 = rut_actual OR p.pagador122 = rut_actual OR p.pagador123 = rut_actual OR p.pagador124 = rut_actual OR p.pagador125 = rut_actual OR
                p.pagador126 = rut_actual OR p.pagador127 = rut_actual OR p.pagador128 = rut_actual OR p.pagador129 = rut_actual OR p.pagador130 = rut_actual OR
                p.pagador131 = rut_actual OR p.pagador132 = rut_actual OR p.pagador133 = rut_actual OR p.pagador134 = rut_actual OR p.pagador135 = rut_actual OR
                p.pagador136 = rut_actual OR p.pagador137 = rut_actual OR p.pagador138 = rut_actual OR p.pagador139 = rut_actual OR p.pagador140 = rut_actual OR
                p.pagador141 = rut_actual OR p.pagador142 = rut_actual OR p.pagador143 = rut_actual OR p.pagador144 = rut_actual OR p.pagador145 = rut_actual OR
                p.pagador146 = rut_actual OR p.pagador147 = rut_actual OR p.pagador148 = rut_actual OR p.pagador149 = rut_actual OR p.pagador150 = rut_actual OR
                p.pagador151 = rut_actual OR p.pagador152 = rut_actual OR p.pagador153 = rut_actual OR p.pagador154 = rut_actual OR p.pagador155 = rut_actual OR
                p.pagador156 = rut_actual OR p.pagador157 = rut_actual OR p.pagador158 = rut_actual OR p.pagador159 = rut_actual OR p.pagador160 = rut_actual OR
                p.pagador161 = rut_actual OR p.pagador162 = rut_actual OR p.pagador163 = rut_actual OR p.pagador164 = rut_actual OR p.pagador165 = rut_actual OR
                p.pagador166 = rut_actual OR p.pagador167 = rut_actual OR p.pagador168 = rut_actual OR p.pagador169 = rut_actual OR p.pagador170 = rut_actual OR
                p.pagador171 = rut_actual OR p.pagador172 = rut_actual OR p.pagador173 = rut_actual OR p.pagador174 = rut_actual OR p.pagador175 = rut_actual OR
                p.pagador176 = rut_actual OR p.pagador177 = rut_actual OR p.pagador178 = rut_actual OR p.pagador179 = rut_actual OR p.pagador180 = rut_actual OR
                p.pagador181 = rut_actual OR p.pagador182 = rut_actual OR p.pagador183 = rut_actual OR p.pagador184 = rut_actual OR p.pagador185 = rut_actual OR
                p.pagador186 = rut_actual OR p.pagador187 = rut_actual OR p.pagador188 = rut_actual OR p.pagador189 = rut_actual OR p.pagador190 = rut_actual OR
                p.pagador191 = rut_actual OR p.pagador192 = rut_actual OR p.pagador193 = rut_actual OR p.pagador194 = rut_actual OR p.pagador195 = rut_actual OR
                p.pagador196 = rut_actual OR p.pagador197 = rut_actual OR p.pagador198 = rut_actual OR p.pagador199 = rut_actual OR p.pagador200 = rut_actual
            )
            LIMIT 1;
            
            IF cliente_coincidente IS NOT NULL THEN
                RAISE EXCEPTION 'El pagador % ya está asociado al cliente %. No se puede duplicar entre clientes.', rut_actual, cliente_coincidente;
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
'Función corregida que verifica la unicidad de pagadores sin ambigüedades de variables.';

COMMENT ON TRIGGER trigger_verificar_unicidad_pagadores ON pagadores IS 
'Trigger que ejecuta la verificación de unicidad de pagadores antes de insertar o actualizar registros.'; 