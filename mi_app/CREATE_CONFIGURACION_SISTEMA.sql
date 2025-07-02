-- Tabla para almacenar configuraciones del sistema
CREATE TABLE IF NOT EXISTS configuracion_sistema (
    id SERIAL PRIMARY KEY,
    clave VARCHAR(100) UNIQUE NOT NULL,
    valor TEXT NOT NULL,
    descripcion TEXT,
    usuario_modificacion VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índice en la clave para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_configuracion_sistema_clave ON configuracion_sistema(clave);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_configuracion_sistema_updated_at 
    BEFORE UPDATE ON configuracion_sistema 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios para documentar la tabla
COMMENT ON TABLE configuracion_sistema IS 'Tabla para almacenar configuraciones generales del sistema';
COMMENT ON COLUMN configuracion_sistema.clave IS 'Clave única que identifica la configuración';
COMMENT ON COLUMN configuracion_sistema.valor IS 'Valor de la configuración en formato JSON o texto';
COMMENT ON COLUMN configuracion_sistema.descripcion IS 'Descripción de para qué sirve esta configuración';
COMMENT ON COLUMN configuracion_sistema.usuario_modificacion IS 'Email del usuario que modificó la configuración';

-- Ejemplo de configuración inicial (opcional - comentado por seguridad)
-- INSERT INTO configuracion_sistema (clave, valor, descripcion, usuario_modificacion) 
-- VALUES (
--     'inicio_operaciones',
--     '{"fecha_inicio": "2024-01-01", "saldo_inicial": 500000, "configurado": true, "usuario_config": "admin@example.com", "fecha_config": "2024-01-01T00:00:00"}',
--     'Configuración del primer día de operaciones y saldo inicial del sistema de cierres',
--     'admin@example.com'
-- )
-- ON CONFLICT (clave) DO NOTHING; 