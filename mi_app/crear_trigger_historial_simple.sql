-- PASO 4: Crear función y trigger simplificados
CREATE OR REPLACE FUNCTION registrar_cambio_cierre_simple()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO cierre_caja_historial (
            cierre_id, fecha_cierre, tipo_operacion, campo_modificado,
            valor_anterior, valor_nuevo, datos_completos, usuario
        ) VALUES (
            NEW.id, NEW.fecha, 'INSERT', 'REGISTRO_COMPLETO',
            NULL, 'CREADO', to_jsonb(NEW), COALESCE(NEW.usuario_creacion, 'sistema')
        );
        
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO cierre_caja_historial (
            cierre_id, fecha_cierre, tipo_operacion, campo_modificado,
            valor_anterior, valor_nuevo, datos_completos, usuario
        ) VALUES (
            NEW.id, NEW.fecha, 'UPDATE', 'REGISTRO_COMPLETO',
            'MODIFICADO', 'ACTUALIZADO', to_jsonb(NEW), COALESCE(NEW.usuario_modificacion, 'sistema')
        );
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Crear trigger
DROP TRIGGER IF EXISTS trigger_historial_cierre_simple ON cierre_caja;
CREATE TRIGGER trigger_historial_cierre_simple
    AFTER INSERT OR UPDATE ON cierre_caja
    FOR EACH ROW
    EXECUTE FUNCTION registrar_cambio_cierre_simple(); 