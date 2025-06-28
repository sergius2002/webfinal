-- =====================================================
-- TRIGGERS PARA SINCRONIZACIÓN ENTRE TABLAS CLIENTES Y PAGADORES
-- =====================================================

-- Función para insertar automáticamente en pagadores cuando se crea un cliente
CREATE OR REPLACE FUNCTION insertar_pagador_por_cliente()
RETURNS TRIGGER AS $$
BEGIN
    -- Insertar un registro en pagadores con el nombre del cliente
    INSERT INTO pagadores (cliente, nombre, rut, email)
    VALUES (NEW.nombre, NEW.nombre, '', '')
    ON CONFLICT (cliente, nombre) DO NOTHING; -- Evitar duplicados
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger que se ejecuta después de insertar un cliente
CREATE TRIGGER trigger_insertar_cliente
    AFTER INSERT ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION insertar_pagador_por_cliente();

-- Función para actualizar pagadores cuando se actualiza un cliente
CREATE OR REPLACE FUNCTION actualizar_pagadores_por_cliente()
RETURNS TRIGGER AS $$
BEGIN
    -- Actualizar todos los registros en pagadores que tengan el cliente anterior
    UPDATE pagadores 
    SET cliente = NEW.nombre
    WHERE cliente = OLD.nombre;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger que se ejecuta después de actualizar un cliente
CREATE TRIGGER trigger_actualizar_cliente
    AFTER UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_pagadores_por_cliente();

-- Función para eliminar pagadores cuando se elimina un cliente
CREATE OR REPLACE FUNCTION eliminar_pagadores_por_cliente()
RETURNS TRIGGER AS $$
BEGIN
    -- Eliminar todos los registros en pagadores que pertenezcan al cliente eliminado
    DELETE FROM pagadores 
    WHERE cliente = OLD.nombre;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger que se ejecuta después de eliminar un cliente
CREATE TRIGGER trigger_eliminar_cliente
    AFTER DELETE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION eliminar_pagadores_por_cliente();

-- =====================================================
-- TRIGGERS PARA SINCRONIZACIÓN INVERSA (PAGADORES -> CLIENTES)
-- =====================================================

-- Función para insertar automáticamente en clientes cuando se crea un pagador con cliente nuevo
CREATE OR REPLACE FUNCTION insertar_cliente_por_pagador()
RETURNS TRIGGER AS $$
BEGIN
    -- Insertar un registro en clientes si el cliente no existe
    INSERT INTO clientes (nombre)
    VALUES (NEW.cliente)
    ON CONFLICT (nombre) DO NOTHING; -- Evitar duplicados
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger que se ejecuta después de insertar un pagador
CREATE TRIGGER trigger_insertar_pagador
    AFTER INSERT ON pagadores
    FOR EACH ROW
    EXECUTE FUNCTION insertar_cliente_por_pagador();

-- Función para actualizar clientes cuando se actualiza un pagador
CREATE OR REPLACE FUNCTION actualizar_cliente_por_pagador()
RETURNS TRIGGER AS $$
BEGIN
    -- Si el cliente cambió, actualizar la tabla clientes
    IF OLD.cliente != NEW.cliente THEN
        -- Insertar el nuevo cliente si no existe
        INSERT INTO clientes (nombre)
        VALUES (NEW.cliente)
        ON CONFLICT (nombre) DO NOTHING;
        
        -- Verificar si el cliente anterior ya no tiene pagadores
        IF NOT EXISTS (SELECT 1 FROM pagadores WHERE cliente = OLD.cliente) THEN
            -- Eliminar el cliente si ya no tiene pagadores
            DELETE FROM clientes WHERE nombre = OLD.cliente;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger que se ejecuta después de actualizar un pagador
CREATE TRIGGER trigger_actualizar_pagador
    AFTER UPDATE ON pagadores
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_cliente_por_pagador();

-- Función para verificar y eliminar clientes cuando se elimina un pagador
CREATE OR REPLACE FUNCTION verificar_cliente_por_pagador()
RETURNS TRIGGER AS $$
BEGIN
    -- Verificar si el cliente eliminado ya no tiene pagadores
    IF NOT EXISTS (SELECT 1 FROM pagadores WHERE cliente = OLD.cliente) THEN
        -- Eliminar el cliente si ya no tiene pagadores
        DELETE FROM clientes WHERE nombre = OLD.cliente;
    END IF;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- Trigger que se ejecuta después de eliminar un pagador
CREATE TRIGGER trigger_eliminar_pagador
    AFTER DELETE ON pagadores
    FOR EACH ROW
    EXECUTE FUNCTION verificar_cliente_por_pagador();

-- =====================================================
-- COMENTARIOS Y EXPLICACIÓN
-- =====================================================

/*
ESTE CONJUNTO DE TRIGGERS MANTIENE SINCRONIZADAS LAS TABLAS CLIENTES Y PAGADORES:

1. TRIGGERS CLIENTES -> PAGADORES:
   - Al crear un cliente: Crea automáticamente un pagador con el mismo nombre
   - Al actualizar un cliente: Actualiza todos los pagadores asociados
   - Al eliminar un cliente: Elimina todos los pagadores asociados

2. TRIGGERS PAGADORES -> CLIENTES:
   - Al crear un pagador: Crea automáticamente el cliente si no existe
   - Al actualizar un pagador: Actualiza el cliente si cambia, elimina cliente anterior si no tiene pagadores
   - Al eliminar un pagador: Elimina el cliente si ya no tiene pagadores

3. CARACTERÍSTICAS:
   - Evita duplicados usando ON CONFLICT
   - Mantiene integridad referencial
   - Funciona bidireccionalmente
   - Maneja casos edge como eliminación de clientes sin pagadores

PARA EJECUTAR ESTOS TRIGGERS:
1. Conectarse a la base de datos Supabase
2. Ejecutar este script completo
3. Los triggers se activarán automáticamente en futuras operaciones

NOTA: Estos triggers asumen que las tablas tienen las siguientes estructuras:
- clientes: id, nombre, created_at
- pagadores: id, cliente, nombre, rut, email
*/ 