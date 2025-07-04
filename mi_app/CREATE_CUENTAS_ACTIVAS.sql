-- Tabla para almacenar cuentas activas del sistema
CREATE TABLE IF NOT EXISTS cuentas_activas (
    id SERIAL PRIMARY KEY,
    banco VARCHAR(100) NOT NULL,
    numero_cuenta BIGINT NOT NULL,
    cedula VARCHAR(20) NOT NULL,
    nombre_titular VARCHAR(200) NOT NULL,
    pais VARCHAR(50) NOT NULL DEFAULT 'Venezuela',
    activa BOOLEAN DEFAULT TRUE,
    usuario_creacion VARCHAR(255),
    usuario_modificacion VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índices para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_cuentas_activas_banco ON cuentas_activas(banco);
CREATE INDEX IF NOT EXISTS idx_cuentas_activas_cedula ON cuentas_activas(cedula);
CREATE INDEX IF NOT EXISTS idx_cuentas_activas_activa ON cuentas_activas(activa);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_cuentas_activas_updated_at 
    BEFORE UPDATE ON cuentas_activas 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios para documentar la tabla
COMMENT ON TABLE cuentas_activas IS 'Tabla para almacenar las cuentas bancarias activas del sistema';
COMMENT ON COLUMN cuentas_activas.banco IS 'Nombre del banco (ej: Banesco, Mercantil, Provincial)';
COMMENT ON COLUMN cuentas_activas.numero_cuenta IS 'Número de cuenta bancaria';
COMMENT ON COLUMN cuentas_activas.cedula IS 'Cédula de identidad del titular';
COMMENT ON COLUMN cuentas_activas.nombre_titular IS 'Nombre completo del titular de la cuenta';
COMMENT ON COLUMN cuentas_activas.pais IS 'País donde está registrada la cuenta';
COMMENT ON COLUMN cuentas_activas.activa IS 'Indica si la cuenta está activa o no';
COMMENT ON COLUMN cuentas_activas.usuario_creacion IS 'Email del usuario que creó el registro';
COMMENT ON COLUMN cuentas_activas.usuario_modificacion IS 'Email del usuario que modificó el registro';

-- Insertar algunos datos de ejemplo (opcional - comentado por seguridad)
-- INSERT INTO cuentas_activas (banco, numero_cuenta, cedula, nombre_titular, pais, usuario_creacion) VALUES
--     ('Banesco', 12345678901234567890, 'V-12345678', 'Juan Pérez', 'Venezuela', 'admin@example.com'),
--     ('Mercantil', 98765432109876543210, 'V-87654321', 'María García', 'Venezuela', 'admin@example.com'),
--     ('Provincial', 11223344556677889900, 'V-11223344', 'Carlos López', 'Venezuela', 'admin@example.com')
-- ON CONFLICT DO NOTHING; 