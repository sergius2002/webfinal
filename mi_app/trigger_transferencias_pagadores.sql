-- =====================================================
-- TRIGGER PARA RELACIONAR TRANSFERENCIAS CON PAGADORES
-- Se activa cada vez que se inserta una nueva transferencia
-- =====================================================

-- Función que se ejecuta cuando se inserta una transferencia
CREATE OR REPLACE FUNCTION procesar_transferencia_pagador()
RETURNS TRIGGER AS $$
DECLARE
    cliente_existe BOOLEAN;
    pagador_encontrado BOOLEAN;
    rut_transferencia TEXT;
    columna_pagador TEXT;
    i INTEGER;
BEGIN
    -- Verificar si el cliente de la transferencia existe en la tabla pagadores
    SELECT EXISTS (
        SELECT 1 FROM pagadores WHERE cliente = NEW.cliente
    ) INTO cliente_existe;

    -- Si el cliente no existe en pagadores, crearlo
    IF NOT cliente_existe THEN
        INSERT INTO pagadores (cliente) VALUES (NEW.cliente);
        RAISE NOTICE 'Cliente % creado automáticamente en tabla pagadores', NEW.cliente;
    END IF;

    -- Si la transferencia tiene un RUT, verificar si está en los pagadores del cliente
    -- Asumimos que el RUT está en el campo 'rut' de la transferencia
    -- Ajusta el nombre del campo según tu estructura real
    IF NEW.rut IS NOT NULL AND NEW.rut != '' THEN
        rut_transferencia := NEW.rut;
        
        -- Verificar si el RUT ya está en los pagadores del cliente
        SELECT EXISTS (
            SELECT 1 FROM pagadores 
            WHERE cliente = NEW.cliente 
            AND (
                pagador1 = rut_transferencia OR pagador2 = rut_transferencia OR pagador3 = rut_transferencia OR 
                pagador4 = rut_transferencia OR pagador5 = rut_transferencia OR pagador6 = rut_transferencia OR 
                pagador7 = rut_transferencia OR pagador8 = rut_transferencia OR pagador9 = rut_transferencia OR 
                pagador10 = rut_transferencia OR pagador11 = rut_transferencia OR pagador12 = rut_transferencia OR 
                pagador13 = rut_transferencia OR pagador14 = rut_transferencia OR pagador15 = rut_transferencia OR 
                pagador16 = rut_transferencia OR pagador17 = rut_transferencia OR pagador18 = rut_transferencia OR 
                pagador19 = rut_transferencia OR pagador20 = rut_transferencia OR pagador21 = rut_transferencia OR 
                pagador22 = rut_transferencia OR pagador23 = rut_transferencia OR pagador24 = rut_transferencia OR 
                pagador25 = rut_transferencia OR pagador26 = rut_transferencia OR pagador27 = rut_transferencia OR 
                pagador28 = rut_transferencia OR pagador29 = rut_transferencia OR pagador30 = rut_transferencia OR 
                pagador31 = rut_transferencia OR pagador32 = rut_transferencia OR pagador33 = rut_transferencia OR 
                pagador34 = rut_transferencia OR pagador35 = rut_transferencia OR pagador36 = rut_transferencia OR 
                pagador37 = rut_transferencia OR pagador38 = rut_transferencia OR pagador39 = rut_transferencia OR 
                pagador40 = rut_transferencia OR pagador41 = rut_transferencia OR pagador42 = rut_transferencia OR 
                pagador43 = rut_transferencia OR pagador44 = rut_transferencia OR pagador45 = rut_transferencia OR 
                pagador46 = rut_transferencia OR pagador47 = rut_transferencia OR pagador48 = rut_transferencia OR 
                pagador49 = rut_transferencia OR pagador50 = rut_transferencia OR pagador51 = rut_transferencia OR 
                pagador52 = rut_transferencia OR pagador53 = rut_transferencia OR pagador54 = rut_transferencia OR 
                pagador55 = rut_transferencia OR pagador56 = rut_transferencia OR pagador57 = rut_transferencia OR 
                pagador58 = rut_transferencia OR pagador59 = rut_transferencia OR pagador60 = rut_transferencia OR 
                pagador61 = rut_transferencia OR pagador62 = rut_transferencia OR pagador63 = rut_transferencia OR 
                pagador64 = rut_transferencia OR pagador65 = rut_transferencia OR pagador66 = rut_transferencia OR 
                pagador67 = rut_transferencia OR pagador68 = rut_transferencia OR pagador69 = rut_transferencia OR 
                pagador70 = rut_transferencia OR pagador71 = rut_transferencia OR pagador72 = rut_transferencia OR 
                pagador73 = rut_transferencia OR pagador74 = rut_transferencia OR pagador75 = rut_transferencia OR 
                pagador76 = rut_transferencia OR pagador77 = rut_transferencia OR pagador78 = rut_transferencia OR 
                pagador79 = rut_transferencia OR pagador80 = rut_transferencia OR pagador81 = rut_transferencia OR 
                pagador82 = rut_transferencia OR pagador83 = rut_transferencia OR pagador84 = rut_transferencia OR 
                pagador85 = rut_transferencia OR pagador86 = rut_transferencia OR pagador87 = rut_transferencia OR 
                pagador88 = rut_transferencia OR pagador89 = rut_transferencia OR pagador90 = rut_transferencia OR 
                pagador91 = rut_transferencia OR pagador92 = rut_transferencia OR pagador93 = rut_transferencia OR 
                pagador94 = rut_transferencia OR pagador95 = rut_transferencia OR pagador96 = rut_transferencia OR 
                pagador97 = rut_transferencia OR pagador98 = rut_transferencia OR pagador99 = rut_transferencia OR 
                pagador100 = rut_transferencia OR pagador101 = rut_transferencia OR pagador102 = rut_transferencia OR 
                pagador103 = rut_transferencia OR pagador104 = rut_transferencia OR pagador105 = rut_transferencia OR 
                pagador106 = rut_transferencia OR pagador107 = rut_transferencia OR pagador108 = rut_transferencia OR 
                pagador109 = rut_transferencia OR pagador110 = rut_transferencia OR pagador111 = rut_transferencia OR 
                pagador112 = rut_transferencia OR pagador113 = rut_transferencia OR pagador114 = rut_transferencia OR 
                pagador115 = rut_transferencia OR pagador116 = rut_transferencia OR pagador117 = rut_transferencia OR 
                pagador118 = rut_transferencia OR pagador119 = rut_transferencia OR pagador120 = rut_transferencia OR 
                pagador121 = rut_transferencia OR pagador122 = rut_transferencia OR pagador123 = rut_transferencia OR 
                pagador124 = rut_transferencia OR pagador125 = rut_transferencia OR pagador126 = rut_transferencia OR 
                pagador127 = rut_transferencia OR pagador128 = rut_transferencia OR pagador129 = rut_transferencia OR 
                pagador130 = rut_transferencia OR pagador131 = rut_transferencia OR pagador132 = rut_transferencia OR 
                pagador133 = rut_transferencia OR pagador134 = rut_transferencia OR pagador135 = rut_transferencia OR 
                pagador136 = rut_transferencia OR pagador137 = rut_transferencia OR pagador138 = rut_transferencia OR 
                pagador139 = rut_transferencia OR pagador140 = rut_transferencia OR pagador141 = rut_transferencia OR 
                pagador142 = rut_transferencia OR pagador143 = rut_transferencia OR pagador144 = rut_transferencia OR 
                pagador145 = rut_transferencia OR pagador146 = rut_transferencia OR pagador147 = rut_transferencia OR 
                pagador148 = rut_transferencia OR pagador149 = rut_transferencia OR pagador150 = rut_transferencia OR 
                pagador151 = rut_transferencia OR pagador152 = rut_transferencia OR pagador153 = rut_transferencia OR 
                pagador154 = rut_transferencia OR pagador155 = rut_transferencia OR pagador156 = rut_transferencia OR 
                pagador157 = rut_transferencia OR pagador158 = rut_transferencia OR pagador159 = rut_transferencia OR 
                pagador160 = rut_transferencia OR pagador161 = rut_transferencia OR pagador162 = rut_transferencia OR 
                pagador163 = rut_transferencia OR pagador164 = rut_transferencia OR pagador165 = rut_transferencia OR 
                pagador166 = rut_transferencia OR pagador167 = rut_transferencia OR pagador168 = rut_transferencia OR 
                pagador169 = rut_transferencia OR pagador170 = rut_transferencia OR pagador171 = rut_transferencia OR 
                pagador172 = rut_transferencia OR pagador173 = rut_transferencia OR pagador174 = rut_transferencia OR 
                pagador175 = rut_transferencia OR pagador176 = rut_transferencia OR pagador177 = rut_transferencia OR 
                pagador178 = rut_transferencia OR pagador179 = rut_transferencia OR pagador180 = rut_transferencia OR 
                pagador181 = rut_transferencia OR pagador182 = rut_transferencia OR pagador183 = rut_transferencia OR 
                pagador184 = rut_transferencia OR pagador185 = rut_transferencia OR pagador186 = rut_transferencia OR 
                pagador187 = rut_transferencia OR pagador188 = rut_transferencia OR pagador189 = rut_transferencia OR 
                pagador190 = rut_transferencia OR pagador191 = rut_transferencia OR pagador192 = rut_transferencia OR 
                pagador193 = rut_transferencia OR pagador194 = rut_transferencia OR pagador195 = rut_transferencia OR 
                pagador196 = rut_transferencia OR pagador197 = rut_transferencia OR pagador198 = rut_transferencia OR 
                pagador199 = rut_transferencia OR pagador200 = rut_transferencia
            )
        ) INTO pagador_encontrado;

        -- Si el RUT no está en los pagadores del cliente, agregarlo automáticamente
        IF NOT pagador_encontrado THEN
            -- Buscar la primera columna vacía para agregar el pagador
            FOR i IN 1..200 LOOP
                columna_pagador := 'pagador' || i;
                EXECUTE format('SELECT %I FROM pagadores WHERE cliente = $1', columna_pagador) 
                INTO pagador_encontrado USING NEW.cliente;
                
                -- Si la columna está vacía o es NULL, usar esta columna
                IF pagador_encontrado IS NULL OR pagador_encontrado = '' OR pagador_encontrado = 'EMPTY' THEN
                    EXECUTE format('UPDATE pagadores SET %I = $1 WHERE cliente = $2', columna_pagador) 
                    USING rut_transferencia, NEW.cliente;
                    RAISE NOTICE 'Pagador % agregado automáticamente al cliente % en columna %', rut_transferencia, NEW.cliente, columna_pagador;
                    EXIT;
                END IF;
            END LOOP;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger que se ejecuta después de insertar una transferencia
DROP TRIGGER IF EXISTS trigger_transferencia_pagador ON transferencias;
CREATE TRIGGER trigger_transferencia_pagador
    AFTER INSERT ON transferencias
    FOR EACH ROW
    EXECUTE FUNCTION procesar_transferencia_pagador();

-- =====================================================
-- COMENTARIOS Y EXPLICACIÓN
-- =====================================================

/*
ESTE TRIGGER SE ACTIVA CADA VEZ QUE SE INSERTA UNA NUEVA TRANSFERENCIA:

1. VERIFICACIÓN DE CLIENTE:
   - Verifica si el cliente de la transferencia existe en la tabla pagadores
   - Si no existe, lo crea automáticamente

2. VERIFICACIÓN DE PAGADOR:
   - Si la transferencia tiene un RUT, verifica si está en los pagadores del cliente
   - Si no está, lo agrega automáticamente en la primera columna vacía disponible

3. FUNCIONALIDAD:
   - Mantiene sincronizadas las tablas transferencias y pagadores
   - Crea clientes automáticamente si no existen
   - Agrega pagadores automáticamente si no están registrados
   - Evita duplicados verificando antes de insertar

4. CAMPOS REQUERIDOS:
   - transferencias.cliente: nombre del cliente
   - transferencias.rut: RUT del pagador (ajustar nombre según tu estructura)
   - pagadores.cliente: nombre del cliente
   - pagadores.pagador1 a pagador200: columnas para almacenar RUTs

PARA EJECUTAR:
1. Conectarse a la base de datos Supabase
2. Ejecutar este script completo
3. El trigger se activará automáticamente en futuras inserciones de transferencias

NOTA: Ajusta el nombre del campo 'rut' en la tabla transferencias según tu estructura real
*/ 