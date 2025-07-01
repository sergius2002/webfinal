-- PASO 2: Crear índices
CREATE INDEX IF NOT EXISTS idx_historial_cierre_id ON cierre_caja_historial(cierre_id);
CREATE INDEX IF NOT EXISTS idx_historial_fecha ON cierre_caja_historial(fecha_cierre);
CREATE INDEX IF NOT EXISTS idx_historial_usuario ON cierre_caja_historial(usuario);
CREATE INDEX IF NOT EXISTS idx_historial_created_at ON cierre_caja_historial(created_at); 