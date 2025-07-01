-- =====================================================
-- TABLA DE HISTORIAL DE CAMBIOS PARA CIERRE DE CAJA
-- EJECUTAR EN EL SQL EDITOR DE SUPABASE
-- =====================================================

-- Crear tabla de historial de cambios
CREATE TABLE IF NOT EXISTS cierre_caja_historial (
    id SERIAL PRIMARY KEY,
    cierre_id INTEGER REFERENCES cierre_caja(id) ON DELETE CASCADE,
    fecha_cierre DATE NOT NULL,
    
    -- Información del cambio
    tipo_operacion VARCHAR(20) NOT NULL CHECK (tipo_operacion IN ('INSERT', 'UPDATE')),
    campo_modificado VARCHAR(50),
    valor_anterior TEXT,
    valor_nuevo TEXT,
    
    -- Datos completos del registro (snapshot)
    datos_completos JSONB NOT NULL,
    
    -- Información de auditoría
    usuario VARCHAR(255) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    
    -- Metadatos
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_historial_cierre_id ON cierre_caja_historial(cierre_id);
CREATE INDEX IF NOT EXISTS idx_historial_fecha ON cierre_caja_historial(fecha_cierre);
CREATE INDEX IF NOT EXISTS idx_historial_usuario ON cierre_caja_historial(usuario);
CREATE INDEX IF NOT EXISTS idx_historial_created_at ON cierre_caja_historial(created_at);

-- Crear función para registrar cambios automáticamente
CREATE OR REPLACE FUNCTION registrar_cambio_cierre()
RETURNS TRIGGER AS $$
DECLARE
    campo_actual TEXT;
    valor_ant TEXT;
    valor_nue TEXT;
    datos_json JSONB;
BEGIN
    -- Convertir el registro completo a JSON
    IF TG_OP = 'INSERT' THEN
        datos_json := to_jsonb(NEW);
        
        -- Registrar creación completa
        INSERT INTO cierre_caja_historial (
            cierre_id, fecha_cierre, tipo_operacion, campo_modificado,
            valor_anterior, valor_nuevo, datos_completos, usuario
        ) VALUES (
            NEW.id, NEW.fecha, 'INSERT', 'REGISTRO_COMPLETO',
            NULL, 'CREADO', datos_json, NEW.usuario_creacion
        );
        
    ELSIF TG_OP = 'UPDATE' THEN
        datos_json := to_jsonb(NEW);
        
        -- Registrar cambio general
        INSERT INTO cierre_caja_historial (
            cierre_id, fecha_cierre, tipo_operacion, campo_modificado,
            valor_anterior, valor_nuevo, datos_completos, usuario
        ) VALUES (
            NEW.id, NEW.fecha, 'UPDATE', 'REGISTRO_COMPLETO',
            to_jsonb(OLD)::text, to_jsonb(NEW)::text, datos_json, NEW.usuario_modificacion
        );
        
        -- Registrar cambios específicos por campo
        IF OLD.saldo_inicial != NEW.saldo_inicial THEN
            INSERT INTO cierre_caja_historial (cierre_id, fecha_cierre, tipo_operacion, campo_modificado, valor_anterior, valor_nuevo, datos_completos, usuario)
            VALUES (NEW.id, NEW.fecha, 'UPDATE', 'saldo_inicial', OLD.saldo_inicial::text, NEW.saldo_inicial::text, datos_json, NEW.usuario_modificacion);
        END IF;
        
        IF OLD.ingresos_binance != NEW.ingresos_binance THEN
            INSERT INTO cierre_caja_historial (cierre_id, fecha_cierre, tipo_operacion, campo_modificado, valor_anterior, valor_nuevo, datos_completos, usuario)
            VALUES (NEW.id, NEW.fecha, 'UPDATE', 'ingresos_binance', OLD.ingresos_binance::text, NEW.ingresos_binance::text, datos_json, NEW.usuario_modificacion);
        END IF;
        
        IF OLD.ingresos_extra != NEW.ingresos_extra THEN
            INSERT INTO cierre_caja_historial (cierre_id, fecha_cierre, tipo_operacion, campo_modificado, valor_anterior, valor_nuevo, datos_completos, usuario)
            VALUES (NEW.id, NEW.fecha, 'UPDATE', 'ingresos_extra', OLD.ingresos_extra::text, NEW.ingresos_extra::text, datos_json, NEW.usuario_modificacion);
        END IF;
        
        IF OLD.egresos_detal != NEW.egresos_detal THEN
            INSERT INTO cierre_caja_historial (cierre_id, fecha_cierre, tipo_operacion, campo_modificado, valor_anterior, valor_nuevo, datos_completos, usuario)
            VALUES (NEW.id, NEW.fecha, 'UPDATE', 'egresos_detal', OLD.egresos_detal::text, NEW.egresos_detal::text, datos_json, NEW.usuario_modificacion);
        END IF;
        
        IF OLD.gastos != NEW.gastos THEN
            INSERT INTO cierre_caja_historial (cierre_id, fecha_cierre, tipo_operacion, campo_modificado, valor_anterior, valor_nuevo, datos_completos, usuario)
            VALUES (NEW.id, NEW.fecha, 'UPDATE', 'gastos', OLD.gastos::text, NEW.gastos::text, datos_json, NEW.usuario_modificacion);
        END IF;
        
        IF OLD.pago_movil != NEW.pago_movil THEN
            INSERT INTO cierre_caja_historial (cierre_id, fecha_cierre, tipo_operacion, campo_modificado, valor_anterior, valor_nuevo, datos_completos, usuario)
            VALUES (NEW.id, NEW.fecha, 'UPDATE', 'pago_movil', OLD.pago_movil::text, NEW.pago_movil::text, datos_json, NEW.usuario_modificacion);
        END IF;
        
        IF OLD.cierre_detal != NEW.cierre_detal THEN
            INSERT INTO cierre_caja_historial (cierre_id, fecha_cierre, tipo_operacion, campo_modificado, valor_anterior, valor_nuevo, datos_completos, usuario)
            VALUES (NEW.id, NEW.fecha, 'UPDATE', 'cierre_detal', OLD.cierre_detal::text, NEW.cierre_detal::text, datos_json, NEW.usuario_modificacion);
        END IF;
        
        IF OLD.saldo_bancos != NEW.saldo_bancos THEN
            INSERT INTO cierre_caja_historial (cierre_id, fecha_cierre, tipo_operacion, campo_modificado, valor_anterior, valor_nuevo, datos_completos, usuario)
            VALUES (NEW.id, NEW.fecha, 'UPDATE', 'saldo_bancos', OLD.saldo_bancos::text, NEW.saldo_bancos::text, datos_json, NEW.usuario_modificacion);
        END IF;
        
        IF OLD.ingresos_extra_detalle::text != NEW.ingresos_extra_detalle::text THEN
            INSERT INTO cierre_caja_historial (cierre_id, fecha_cierre, tipo_operacion, campo_modificado, valor_anterior, valor_nuevo, datos_completos, usuario)
            VALUES (NEW.id, NEW.fecha, 'UPDATE', 'ingresos_extra_detalle', OLD.ingresos_extra_detalle::text, NEW.ingresos_extra_detalle::text, datos_json, NEW.usuario_modificacion);
        END IF;
        
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Crear trigger para registrar cambios automáticamente
DROP TRIGGER IF EXISTS trigger_historial_cierre ON cierre_caja;
CREATE TRIGGER trigger_historial_cierre
    AFTER INSERT OR UPDATE ON cierre_caja
    FOR EACH ROW
    EXECUTE FUNCTION registrar_cambio_cierre();

-- Crear vista para consultas fáciles del historial
CREATE OR REPLACE VIEW vista_historial_cierre AS
SELECT 
    h.id,
    h.fecha_cierre,
    h.tipo_operacion,
    h.campo_modificado,
    h.valor_anterior,
    h.valor_nuevo,
    h.usuario,
    h.created_at,
    c.id as cierre_id,
    -- Formatear valores monetarios
    CASE 
        WHEN h.campo_modificado IN ('saldo_inicial', 'ingresos_binance', 'ingresos_extra', 'egresos_detal', 'gastos', 'pago_movil', 'cierre_detal', 'saldo_bancos') 
        THEN CONCAT('$', FORMAT(h.valor_anterior::numeric, 'FM999,999,999')) 
        ELSE h.valor_anterior 
    END as valor_anterior_formateado,
    CASE 
        WHEN h.campo_modificado IN ('saldo_inicial', 'ingresos_binance', 'ingresos_extra', 'egresos_detal', 'gastos', 'pago_movil', 'cierre_detal', 'saldo_bancos') 
        THEN CONCAT('$', FORMAT(h.valor_nuevo::numeric, 'FM999,999,999')) 
        ELSE h.valor_nuevo 
    END as valor_nuevo_formateado
FROM cierre_caja_historial h
LEFT JOIN cierre_caja c ON h.cierre_id = c.id
ORDER BY h.created_at DESC;

-- Comentarios para documentar las tablas
COMMENT ON TABLE cierre_caja_historial IS 'Historial completo de cambios en cierres de caja para auditoría y responsabilidad';
COMMENT ON COLUMN cierre_caja_historial.tipo_operacion IS 'Tipo de operación: INSERT (creación) o UPDATE (modificación)';
COMMENT ON COLUMN cierre_caja_historial.campo_modificado IS 'Campo específico que fue modificado';
COMMENT ON COLUMN cierre_caja_historial.valor_anterior IS 'Valor anterior del campo';
COMMENT ON COLUMN cierre_caja_historial.valor_nuevo IS 'Valor nuevo del campo';
COMMENT ON COLUMN cierre_caja_historial.datos_completos IS 'Snapshot completo del registro en formato JSON';
COMMENT ON COLUMN cierre_caja_historial.usuario IS 'Usuario responsable del cambio';

-- Función para consultar historial de un cierre específico
CREATE OR REPLACE FUNCTION obtener_historial_cierre(fecha_consulta DATE)
RETURNS TABLE (
    operacion TEXT,
    campo TEXT,
    valor_anterior TEXT,
    valor_nuevo TEXT,
    usuario TEXT,
    fecha_hora TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        h.tipo_operacion::TEXT,
        COALESCE(h.campo_modificado, 'N/A')::TEXT,
        COALESCE(h.valor_anterior_formateado, 'N/A')::TEXT,
        COALESCE(h.valor_nuevo_formateado, 'N/A')::TEXT,
        h.usuario::TEXT,
        h.created_at
    FROM vista_historial_cierre h
    WHERE h.fecha_cierre = fecha_consulta
    ORDER BY h.created_at ASC;
END;
$$ LANGUAGE plpgsql; 