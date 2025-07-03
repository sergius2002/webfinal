-- Tabla para almacenar superusuarios del sistema
CREATE TABLE IF NOT EXISTS superusuarios (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    usuario_creacion VARCHAR(255),
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crear índice en el email para búsquedas rápidas
CREATE INDEX IF NOT EXISTS idx_superusuarios_email ON superusuarios(email);

-- Trigger para actualizar updated_at automáticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_superusuarios_updated_at 
    BEFORE UPDATE ON superusuarios 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios para documentar la tabla
COMMENT ON TABLE superusuarios IS 'Tabla para almacenar superusuarios con acceso completo al módulo administrativo';
COMMENT ON COLUMN superusuarios.email IS 'Email único del superusuario';
COMMENT ON COLUMN superusuarios.usuario_creacion IS 'Email del usuario que creó este superusuario';
COMMENT ON COLUMN superusuarios.activo IS 'Indica si el superusuario está activo o no';

-- Insertar el primer superusuario (cambia el email por el tuyo)
-- IMPORTANTE: Cambia 'tu_email@ejemplo.com' por tu email real
INSERT INTO superusuarios (email, usuario_creacion, activo) 
VALUES ('tu_email@ejemplo.com', 'Sistema', TRUE)
ON CONFLICT (email) DO NOTHING;

-- Políticas de seguridad RLS (Row Level Security) - opcional
-- ALTER TABLE superusuarios ENABLE ROW LEVEL SECURITY;

-- Crear política para que solo superusuarios puedan ver/modificar la tabla
-- CREATE POLICY "superusuarios_policy" ON superusuarios
--     FOR ALL USING (true); 