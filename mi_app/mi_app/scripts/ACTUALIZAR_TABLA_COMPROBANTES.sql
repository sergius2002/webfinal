-- Script para actualizar la tabla comprobantes con campos de usuario
-- Ejecutar en Supabase SQL Editor

-- Agregar nuevos campos para información del usuario
ALTER TABLE comprobantes 
ADD COLUMN IF NOT EXISTS usuario_id BIGINT,
ADD COLUMN IF NOT EXISTS usuario_username TEXT,
ADD COLUMN IF NOT EXISTS usuario_nombre TEXT,
ADD COLUMN IF NOT EXISTS usuario_apellido TEXT,
ADD COLUMN IF NOT EXISTS timestamp_envio TIMESTAMP WITH TIME ZONE;

-- Crear índice para búsquedas por usuario
CREATE INDEX IF NOT EXISTS idx_comprobantes_usuario_id ON comprobantes(usuario_id);
CREATE INDEX IF NOT EXISTS idx_comprobantes_usuario_username ON comprobantes(usuario_username);

-- Comentarios para documentar los nuevos campos
COMMENT ON COLUMN comprobantes.usuario_id IS 'ID único del usuario de Telegram';
COMMENT ON COLUMN comprobantes.usuario_username IS 'Username del usuario de Telegram';
COMMENT ON COLUMN comprobantes.usuario_nombre IS 'Nombre del usuario de Telegram';
COMMENT ON COLUMN comprobantes.usuario_apellido IS 'Apellido del usuario de Telegram';
COMMENT ON COLUMN comprobantes.timestamp_envio IS 'Timestamp cuando se envió el comprobante';

-- Verificar que los campos se agregaron correctamente
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'comprobantes' 
AND column_name IN ('usuario_id', 'usuario_username', 'usuario_nombre', 'usuario_apellido', 'timestamp_envio')
ORDER BY column_name; 