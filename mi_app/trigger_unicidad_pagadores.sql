-- Trigger para verificar unicidad de pagadores
-- Garantiza que cada RUT de pagador sea único entre todos los clientes
-- y que no haya duplicados dentro del mismo cliente

-- Función que verifica la unicidad
CREATE OR REPLACE FUNCTION verificar_unicidad_pagadores()
RETURNS TRIGGER AS $$
DECLARE
    rut TEXT;
    otro_cliente TEXT;
    otro_rut TEXT;
    i INT;
    j INT;
    columna TEXT;
    columna_j TEXT;
BEGIN
    -- Recorre todas las columnas pagador1...pagador200 del registro nuevo/actualizado
    FOR i IN 1..200 LOOP
        columna := 'pagador' || i;
        EXECUTE format('SELECT ($1).%I', columna) INTO rut USING NEW;
        
        -- Solo procesa si el RUT no es NULL ni vacío
        IF rut IS NOT NULL AND rut <> '' THEN
            -- 1. Verifica que el RUT no esté en otro cliente
            SELECT cliente INTO otro_cliente
            FROM pagadores
            WHERE cliente <> NEW.cliente
            AND (
                pagador1 = rut OR pagador2 = rut OR pagador3 = rut OR pagador4 = rut OR pagador5 = rut OR
                pagador6 = rut OR pagador7 = rut OR pagador8 = rut OR pagador9 = rut OR pagador10 = rut OR
                pagador11 = rut OR pagador12 = rut OR pagador13 = rut OR pagador14 = rut OR pagador15 = rut OR
                pagador16 = rut OR pagador17 = rut OR pagador18 = rut OR pagador19 = rut OR pagador20 = rut OR
                pagador21 = rut OR pagador22 = rut OR pagador23 = rut OR pagador24 = rut OR pagador25 = rut OR
                pagador26 = rut OR pagador27 = rut OR pagador28 = rut OR pagador29 = rut OR pagador30 = rut OR
                pagador31 = rut OR pagador32 = rut OR pagador33 = rut OR pagador34 = rut OR pagador35 = rut OR
                pagador36 = rut OR pagador37 = rut OR pagador38 = rut OR pagador39 = rut OR pagador40 = rut OR
                pagador41 = rut OR pagador42 = rut OR pagador43 = rut OR pagador44 = rut OR pagador45 = rut OR
                pagador46 = rut OR pagador47 = rut OR pagador48 = rut OR pagador49 = rut OR pagador50 = rut OR
                pagador51 = rut OR pagador52 = rut OR pagador53 = rut OR pagador54 = rut OR pagador55 = rut OR
                pagador56 = rut OR pagador57 = rut OR pagador58 = rut OR pagador59 = rut OR pagador60 = rut OR
                pagador61 = rut OR pagador62 = rut OR pagador63 = rut OR pagador64 = rut OR pagador65 = rut OR
                pagador66 = rut OR pagador67 = rut OR pagador68 = rut OR pagador69 = rut OR pagador70 = rut OR
                pagador71 = rut OR pagador72 = rut OR pagador73 = rut OR pagador74 = rut OR pagador75 = rut OR
                pagador76 = rut OR pagador77 = rut OR pagador78 = rut OR pagador79 = rut OR pagador80 = rut OR
                pagador81 = rut OR pagador82 = rut OR pagador83 = rut OR pagador84 = rut OR pagador85 = rut OR
                pagador86 = rut OR pagador87 = rut OR pagador88 = rut OR pagador89 = rut OR pagador90 = rut OR
                pagador91 = rut OR pagador92 = rut OR pagador93 = rut OR pagador94 = rut OR pagador95 = rut OR
                pagador96 = rut OR pagador97 = rut OR pagador98 = rut OR pagador99 = rut OR pagador100 = rut OR
                pagador101 = rut OR pagador102 = rut OR pagador103 = rut OR pagador104 = rut OR pagador105 = rut OR
                pagador106 = rut OR pagador107 = rut OR pagador108 = rut OR pagador109 = rut OR pagador110 = rut OR
                pagador111 = rut OR pagador112 = rut OR pagador113 = rut OR pagador114 = rut OR pagador115 = rut OR
                pagador116 = rut OR pagador117 = rut OR pagador118 = rut OR pagador119 = rut OR pagador120 = rut OR
                pagador121 = rut OR pagador122 = rut OR pagador123 = rut OR pagador124 = rut OR pagador125 = rut OR
                pagador126 = rut OR pagador127 = rut OR pagador128 = rut OR pagador129 = rut OR pagador130 = rut OR
                pagador131 = rut OR pagador132 = rut OR pagador133 = rut OR pagador134 = rut OR pagador135 = rut OR
                pagador136 = rut OR pagador137 = rut OR pagador138 = rut OR pagador139 = rut OR pagador140 = rut OR
                pagador141 = rut OR pagador142 = rut OR pagador143 = rut OR pagador144 = rut OR pagador145 = rut OR
                pagador146 = rut OR pagador147 = rut OR pagador148 = rut OR pagador149 = rut OR pagador150 = rut OR
                pagador151 = rut OR pagador152 = rut OR pagador153 = rut OR pagador154 = rut OR pagador155 = rut OR
                pagador156 = rut OR pagador157 = rut OR pagador158 = rut OR pagador159 = rut OR pagador160 = rut OR
                pagador161 = rut OR pagador162 = rut OR pagador163 = rut OR pagador164 = rut OR pagador165 = rut OR
                pagador166 = rut OR pagador167 = rut OR pagador168 = rut OR pagador169 = rut OR pagador170 = rut OR
                pagador171 = rut OR pagador172 = rut OR pagador173 = rut OR pagador174 = rut OR pagador175 = rut OR
                pagador176 = rut OR pagador177 = rut OR pagador178 = rut OR pagador179 = rut OR pagador180 = rut OR
                pagador181 = rut OR pagador182 = rut OR pagador183 = rut OR pagador184 = rut OR pagador185 = rut OR
                pagador186 = rut OR pagador187 = rut OR pagador188 = rut OR pagador189 = rut OR pagador190 = rut OR
                pagador191 = rut OR pagador192 = rut OR pagador193 = rut OR pagador194 = rut OR pagador195 = rut OR
                pagador196 = rut OR pagador197 = rut OR pagador198 = rut OR pagador199 = rut OR pagador200 = rut
            )
            LIMIT 1;
            
            IF otro_cliente IS NOT NULL THEN
                RAISE EXCEPTION 'El pagador % ya está asociado al cliente %. No se puede duplicar entre clientes.', rut, otro_cliente;
            END IF;

            -- 2. Verifica que el RUT no esté repetido en el mismo cliente
            FOR j IN 1..200 LOOP
                IF j <> i THEN
                    columna_j := 'pagador' || j;
                    EXECUTE format('SELECT ($1).%I', columna_j) INTO otro_rut USING NEW;
                    IF otro_rut = rut THEN
                        RAISE EXCEPTION 'El pagador % está repetido en el cliente % (columnas % y %). No se puede duplicar.', rut, NEW.cliente, columna, columna_j;
                    END IF;
                END IF;
            END LOOP;
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
'Función que verifica que cada RUT de pagador sea único entre todos los clientes y que no haya duplicados dentro del mismo cliente. Se ejecuta antes de INSERT o UPDATE en la tabla pagadores.';

COMMENT ON TRIGGER trigger_verificar_unicidad_pagadores ON pagadores IS 
'Trigger que ejecuta la verificación de unicidad de pagadores antes de insertar o actualizar registros.'; 