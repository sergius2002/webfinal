#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de conexión SSH a PythonAnywhere usando paramiko
Autor: Asistente de Programación
Fecha: 2024
"""

import paramiko
import sys
import time
from typing import Optional


class PythonAnywhereSSH:
    """
    Clase para manejar conexiones SSH a PythonAnywhere
    """
    
    def __init__(self, hostname: str, username: str, password: str, port: int = 22):
        """
        Inicializa la conexión SSH
        
        Args:
            hostname: Host de PythonAnywhere (ssh.eu.pythonanywhere.com)
            username: Nombre de usuario de PythonAnywhere
            password: Contraseña de la cuenta
            port: Puerto SSH (por defecto 22)
        """
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.client = None
        self.channel = None
    
    def conectar(self) -> bool:
        """
        Establece la conexión SSH
        
        Returns:
            bool: True si la conexión fue exitosa, False en caso contrario
        """
        try:
            print(f"🔌 Conectando a {self.hostname} como {self.username}...")
            
            # Crear cliente SSH
            self.client = paramiko.SSHClient()
            
            # Configurar política de host keys (auto-add para desarrollo)
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Establecer conexión con timeout
            self.client.connect(
                hostname=self.hostname,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=30,
                allow_agent=False,
                look_for_keys=False
            )
            
            print("✅ Conexión SSH establecida exitosamente")
            return True
            
        except paramiko.AuthenticationException:
            print("❌ Error de autenticación: Usuario o contraseña incorrectos")
            return False
        except paramiko.SSHException as e:
            print(f"❌ Error SSH: {e}")
            return False
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def ejecutar_comando(self, comando: str) -> Optional[str]:
        """
        Ejecuta un comando en el servidor remoto
        
        Args:
            comando: Comando a ejecutar
            
        Returns:
            str: Salida del comando o None si hubo error
        """
        if not self.client:
            print("❌ No hay conexión SSH activa")
            return None
        
        try:
            print(f"🚀 Ejecutando comando: {comando}")
            
            # Ejecutar comando
            stdin, stdout, stderr = self.client.exec_command(comando)
            
            # Obtener salida
            salida = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            # Verificar si hubo errores
            if error:
                print(f"⚠️ Errores del comando: {error}")
            
            return salida
            
        except Exception as e:
            print(f"❌ Error ejecutando comando: {e}")
            return None
    
    def cerrar_conexion(self):
        """
        Cierra la conexión SSH
        """
        if self.client:
            self.client.close()
            print("🔌 Conexión SSH cerrada")
    
    def __enter__(self):
        """
        Context manager entry
        """
        if self.conectar():
            return self
        else:
            raise Exception("No se pudo establecer la conexión SSH")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit
        """
        self.cerrar_conexion()


def main():
    """
    Función principal del script
    """
    # Configuración de conexión
    HOSTNAME = "ssh.eu.pythonanywhere.com"
    USERNAME = "sacristobalspa"
    PASSWORD = "dirqoc-navco2-zethaB"  # Contraseña de PythonAnywhere
    
    print("🚀 Script de conexión SSH a PythonAnywhere")
    print("=" * 50)
    
    # Usar context manager para manejo automático de conexión
    try:
        with PythonAnywhereSSH(HOSTNAME, USERNAME, PASSWORD) as ssh:
            
            # Comando 1: Listar archivos del directorio home
            print("\n📁 Listando archivos del directorio home:")
            resultado = ssh.ejecutar_comando("ls -la")
            if resultado:
                print(resultado)
            
            # Comando 2: Verificar el directorio actual
            print("\n📍 Directorio actual:")
            resultado = ssh.ejecutar_comando("pwd")
            if resultado:
                print(resultado)
            
            # Comando 3: Navegar al directorio webfinal
            print("\n📂 Navegando al directorio webfinal:")
            resultado = ssh.ejecutar_comando("cd webfinal && pwd")
            if resultado:
                print(f"Directorio actual: {resultado.strip()}")
            
            # Comando 4: Verificar si hay repositorio git en webfinal
            print("\n🔍 Verificando repositorio git en webfinal:")
            resultado = ssh.ejecutar_comando("cd webfinal && git status")
            if resultado:
                print(resultado)
            else:
                print("No se encontró repositorio git en webfinal")
            
            # Comando 5: Verificar último commit
            print("\n📝 Último commit:")
            resultado = ssh.ejecutar_comando("cd webfinal && git log --oneline -3")
            if resultado:
                print(resultado)
            
            # Comando 6: Actualizar desde el repositorio remoto
            print("\n🔄 Actualizando desde repositorio remoto:")
            resultado = ssh.ejecutar_comando("cd webfinal && git fetch origin")
            if resultado:
                print("Fetch completado")
            
            # Comando 7: Hacer pull de los cambios
            print("\n⬇️ Descargando cambios:")
            resultado = ssh.ejecutar_comando("cd webfinal && git pull origin main")
            if resultado:
                print("Pull completado:")
                print(resultado)
            
            # Comando 8: Verificar estado final
            print("\n✅ Estado final del repositorio:")
            resultado = ssh.ejecutar_comando("cd webfinal && git status")
            if resultado:
                print(resultado)
    
    except Exception as e:
        print(f"❌ Error en la ejecución: {e}")
        sys.exit(1)
    
    print("\n✅ Script completado exitosamente")


if __name__ == "__main__":
    main() 
    main()