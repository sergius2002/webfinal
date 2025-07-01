-- =====================================================
-- TABLA DE HISTORIAL DE CAMBIOS PARA CIERRE DE CAJA
-- VERSIÓN SIMPLIFICADA - EJECUTAR PASO A PASO
-- =====================================================

-- PASO 1: Crear tabla básica
CREATE TABLE IF NOT EXISTS cierre_caja_historial (
    id SERIAL PRIMARY KEY,
    cierre_id INTEGER,
    fecha_cierre DATE NOT NULL,
    tipo_operacion VARCHAR(20) NOT NULL CHECK (tipo_operacion IN ('INSERT', 'UPDATE')),
    campo_modificado VARCHAR(50),
    valor_anterior TEXT,
    valor_nuevo TEXT,
    datos_completos JSONB NOT NULL,
    usuario VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
); 