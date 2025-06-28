-- =====================================================
-- TRIGGERS PARA SINCRONIZACIÓN ENTRE CLIENTES Y PAGADORES
-- EJECUTAR EN EL SQL EDITOR DE SUPABASE
-- =====================================================

-- 1. Función para insertar pagador cuando se crea un cliente
CREATE OR REPLACE FUNCTION insertar_pagador_por_cliente()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO pagadores (cliente, nombre, rut, email)
    VALUES (NEW.nombre, NEW.nombre, '', '')
    ON CONFLICT (cliente, nombre) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Trigger para insertar cliente
DROP TRIGGER IF EXISTS trigger_insertar_cliente ON clientes;
CREATE TRIGGER trigger_insertar_cliente
    AFTER INSERT ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION insertar_pagador_por_cliente();

-- 3. Función para actualizar pagadores cuando se actualiza un cliente
CREATE OR REPLACE FUNCTION actualizar_pagadores_por_cliente()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE pagadores 
    SET cliente = NEW.nombre
    WHERE cliente = OLD.nombre;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 4. Trigger para actualizar cliente
DROP TRIGGER IF EXISTS trigger_actualizar_cliente ON clientes;
CREATE TRIGGER trigger_actualizar_cliente
    AFTER UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION actualizar_pagadores_por_cliente();

-- 5. Función para eliminar pagadores cuando se elimina un cliente
CREATE OR REPLACE FUNCTION eliminar_pagadores_por_cliente()
RETURNS TRIGGER AS $$
BEGIN
    DELETE FROM pagadores 
    WHERE cliente = OLD.nombre;
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;

-- 6. Trigger para eliminar cliente
DROP TRIGGER IF EXISTS trigger_eliminar_cliente ON clientes;
CREATE TRIGGER trigger_eliminar_cliente
    AFTER DELETE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION eliminar_pagadores_por_cliente();

-- 7. Función para insertar cliente cuando se crea un pagador
CREATE OR REPLACE FUNCTION insertar_cliente_por_pagador()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO clientes (nombre)
    VALUES (NEW.cliente)
    ON CONFLICT (nombre) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 8. Trigger para insertar pagador
DROP TRIGGER IF EXISTS trigger_insertar_pagador ON pagadores;
CREATE TRIGGER trigger_insertar_pagador
    AFTER INSERT ON pagadores
    FOR EACH ROW
    EXECUTE FUNCTION insertar_cliente_por_pagador();

-- =====================================================
-- VERIFICACIÓN DE TRIGGERS CREADOS
-- =====================================================

-- Consulta para verificar que los triggers se crearon correctamente
SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement
FROM information_schema.triggers 
WHERE trigger_name LIKE '%cliente%' OR trigger_name LIKE '%pagador%'
ORDER BY trigger_name;

-- =====================================================
-- INSTRUCCIONES DE USO
-- =====================================================

/*
ESTOS TRIGGERS MANTIENEN SINCRONIZADAS LAS TABLAS CLIENTES Y PAGADORES:

1. Al crear un cliente → se crea automáticamente un pagador con el mismo nombre
2. Al crear un pagador → se crea automáticamente el cliente si no existe
3. Al actualizar un cliente → se actualizan todos sus pagadores asociados
4. Al eliminar un cliente → se eliminan todos sus pagadores asociados

CARACTERÍSTICAS:
- Evita duplicados usando ON CONFLICT
- Mantiene integridad referencial
- Funciona bidireccionalmente
- Maneja casos edge como eliminación de clientes sin pagadores

PARA PROBAR LOS TRIGGERS:
1. Crear un nuevo cliente desde la aplicación
2. Verificar que se creó automáticamente un pagador
3. Crear un nuevo pagador con un cliente que no existe
4. Verificar que se creó automáticamente el cliente
*/ 