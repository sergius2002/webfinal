#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 BOT MANAGER - Utilidad SSH centralizada para gestión del bot de Telegram
Reemplaza todos los scripts SSH redundantes con una sola herramienta unificada
"""

import paramiko
import sys
import time
import argparse


class PythonAnywhereSSH:
    """Clase para manejar conexiones SSH a PythonAnywhere"""
    
    def __init__(self, hostname: str, username: str, password: str, port: int = 22):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.client = None
    
    def conectar(self) -> bool:
        """Establece la conexión SSH"""
        try:
            print(f"🔌 Conectando a {self.hostname} como {self.username}...")
            
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
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
            
        except Exception as e:
            print(f"❌ Error de conexión: {e}")
            return False
    
    def ejecutar_comando(self, comando: str, timeout: int = 60) -> str:
        """Ejecuta un comando en el servidor remoto"""
        if not self.client:
            print("❌ No hay conexión SSH activa")
            return ""
        
        try:
            print(f"🚀 Ejecutando: {comando}")
            
            stdin, stdout, stderr = self.client.exec_command(comando, timeout=timeout)
            
            salida = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            
            if error and "Error, do this: mount" not in error:
                print(f"⚠️ Errores: {error}")
            
            return salida
            
        except Exception as e:
            print(f"❌ Error ejecutando comando: {e}")
            return ""
    
    def cerrar_conexion(self):
        """Cierra la conexión SSH"""
        if self.client:
            self.client.close()
            print("🔌 Conexión SSH cerrada")
    
    def __enter__(self):
        if self.conectar():
            return self
        else:
            raise Exception("No se pudo establecer la conexión SSH")
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cerrar_conexion()


class BotManager:
    """Gestor centralizado para todas las operaciones del bot"""
    
    def __init__(self):
        self.hostname = "ssh.eu.pythonanywhere.com"
        self.username = "sacristobalspa"
        self.password = "dirqoc-navco2-zethaB"
        self.token_correcto = "8065976460"
        self.token_anterior = "8204914856"
    
    def limpiar_y_reiniciar(self):
        """Limpia múltiples instancias y reinicia solo una"""
        print("🧹 LIMPIANDO MÚLTIPLES INSTANCIAS Y REINICIANDO BOT")
        print("=" * 60)
        
        with PythonAnywhereSSH(self.hostname, self.username, self.password) as ssh:
            # 1. Verificar procesos actuales
            print("\n🔍 Verificando procesos actuales:")
            resultado = ssh.ejecutar_comando("ps aux | grep python")
            if resultado:
                print("Procesos Python encontrados:")
                for linea in resultado.split('\n'):
                    if 'telegram' in linea.lower() or 'bot' in linea.lower():
                        print(f"  📍 {linea}")
            
            # 2. Matar TODOS los procesos relacionados
            print("\n🛑 Deteniendo TODOS los procesos de Telegram:")
            comandos_kill = [
                "pkill -f telegram_bot_always",
                "pkill -f telegram",
                "pkill -f telebot",
                "killall python3 2>/dev/null || true"
            ]
            
            for cmd in comandos_kill:
                ssh.ejecutar_comando(cmd)
                time.sleep(1)
            
            # 3. Esperar liberación de recursos
            print("\n⏳ Esperando 5 segundos para liberación de recursos...")
            time.sleep(5)
            
            # 4. Verificar limpieza
            print("\n✅ Verificando limpieza:")
            resultado = ssh.ejecutar_comando("ps aux | grep telegram | grep -v grep")
            if resultado.strip():
                print(f"⚠️ Aún hay procesos: {resultado}")
            else:
                print("✅ Todos los procesos eliminados")
            
            # 5. Limpiar logs
            print("\n🗑️ Limpiando logs:")
            ssh.ejecutar_comando("cd webfinal/mi_app && rm -f telegram_bot.log")
            ssh.ejecutar_comando("cd webfinal/mi_app && touch telegram_bot.log")
            
            # 6. Verificar token
            self._verificar_token(ssh)
            
            # 7. Iniciar bot
            self._iniciar_bot(ssh)
            
            # 8. Verificar resultado
            self._verificar_instancia_unica(ssh)
    
    def reiniciar_simple(self):
        """Reinicio simple del bot"""
        print("🤖 REINICIO SIMPLE DEL BOT")
        print("=" * 40)
        
        with PythonAnywhereSSH(self.hostname, self.username, self.password) as ssh:
            # Detener bot
            print("\n🛑 Deteniendo bot:")
            ssh.ejecutar_comando("pkill -f telegram_bot_always")
            time.sleep(2)
            
            # Verificar token
            self._verificar_token(ssh)
            
            # Iniciar bot
            self._iniciar_bot(ssh)
    
    def verificar_token_y_reiniciar(self):
        """Verifica token correcto y reinicia"""
        print("🔑 VERIFICANDO TOKEN Y REINICIANDO")
        print("=" * 45)
        
        with PythonAnywhereSSH(self.hostname, self.username, self.password) as ssh:
            # Detener procesos
            print("\n🛑 Deteniendo procesos:")
            ssh.ejecutar_comando("pkill -f telegram_bot_always")
            time.sleep(2)
            
            # Verificar token correcto
            print(f"\n🔑 Verificando token correcto ({self.token_correcto}):")
            resultado = ssh.ejecutar_comando(f"cd webfinal/mi_app && grep -n '{self.token_correcto}' telegram_bot_always.py")
            if resultado:
                print("✅ Token correcto encontrado:")
                print(resultado)
            else:
                print("❌ Token correcto NO encontrado")
                return
            
            # Verificar que no esté el token anterior
            print(f"\n🚫 Verificando ausencia del token anterior ({self.token_anterior}):")
            resultado = ssh.ejecutar_comando(f"cd webfinal/mi_app && grep -n '{self.token_anterior}' telegram_bot_always.py")
            if resultado:
                print("❌ Aún se encuentra el token anterior:")
                print(resultado)
            else:
                print("✅ Token anterior eliminado correctamente")
            
            # Verificar módulos
            self._verificar_modulos(ssh)
            
            # Iniciar bot
            self._iniciar_bot(ssh)
    
    def instalar_dependencias_y_reiniciar(self):
        """Instala dependencias y reinicia el bot"""
        print("📦 INSTALANDO DEPENDENCIAS Y REINICIANDO")
        print("=" * 50)
        
        with PythonAnywhereSSH(self.hostname, self.username, self.password) as ssh:
            # Detener bot
            print("\n🛑 Deteniendo bot:")
            ssh.ejecutar_comando("pkill -f telegram_bot_always")
            time.sleep(2)
            
            # Verificar requirements.txt
            print("\n📄 Verificando requirements.txt:")
            resultado = ssh.ejecutar_comando("cd webfinal && ls -la requirements.txt")
            if resultado:
                print(resultado)
            
            # Mostrar contenido
            print("\n📋 Contenido de requirements.txt:")
            resultado = ssh.ejecutar_comando("cd webfinal && cat requirements.txt")
            if resultado:
                print(resultado)
            
            # Instalar dependencias
            print("\n📦 Instalando dependencias (puede tomar varios minutos):")
            resultado = ssh.ejecutar_comando("cd webfinal && pip3 install --user -r requirements.txt", timeout=300)
            if resultado:
                print(resultado)
            
            # Verificar instalaciones específicas
            self._verificar_modulos(ssh)
            
            # Iniciar bot
            self._iniciar_bot(ssh)
    
    def verificar_chat_id(self):
        """Verifica configuración del chat ID y logs"""
        print("🔍 VERIFICANDO CHAT ID Y LOGS")
        print("=" * 40)
        
        with PythonAnywhereSSH(self.hostname, self.username, self.password) as ssh:
            # Verificar chat ID configurado
            print("\n🔑 Chat ID configurado:")
            resultado = ssh.ejecutar_comando("cd webfinal/mi_app && grep -n 'chat_id_telegram.*=' telegram_bot_always.py")
            if resultado:
                print(resultado)
            
            # Log completo
            print("\n📋 Log completo (últimas 50 líneas):")
            resultado = ssh.ejecutar_comando("cd webfinal/mi_app && tail -50 telegram_bot.log")
            if resultado:
                print(resultado)
            
            # Mensajes de permisos denegados
            print("\n🚫 Mensajes de permisos denegados:")
            resultado = ssh.ejecutar_comando("cd webfinal/mi_app && grep -n 'No tienes permiso' telegram_bot.log")
            if resultado:
                print(resultado)
            else:
                print("No se encontraron mensajes de permisos denegados")
            
            # Chat IDs en el log
            print("\n💬 Chat IDs encontrados en el log:")
            resultado = ssh.ejecutar_comando("cd webfinal/mi_app && grep -o 'chat [0-9-]*' telegram_bot.log | sort | uniq")
            if resultado:
                print(resultado)
            
            # Estado del bot
            print("\n🤖 Estado del bot:")
            resultado = ssh.ejecutar_comando("ps aux | grep python3 | grep telegram")
            if resultado:
                print("✅ Bot está corriendo:")
                print(resultado)
            else:
                print("❌ Bot no está corriendo")
    
    def _verificar_token(self, ssh):
        """Verifica que el token correcto esté configurado"""
        print(f"\n🔑 Verificando token correcto ({self.token_correcto}):")
        resultado = ssh.ejecutar_comando(f"cd webfinal/mi_app && grep -n '{self.token_correcto}' telegram_bot_always.py")
        if resultado:
            print("✅ Token correcto encontrado")
        else:
            print("❌ Token correcto NO encontrado")
            raise Exception("Token incorrecto configurado")
    
    def _verificar_modulos(self, ssh):
        """Verifica que los módulos necesarios estén instalados"""
        print("\n📦 Verificando módulos necesarios:")
        
        # Verificar supabase
        resultado = ssh.ejecutar_comando("python3 -c 'import supabase; print(\"✅ Supabase OK\")'")
        if "✅ Supabase OK" in resultado:
            print("✅ Supabase instalado")
        else:
            print("❌ Supabase faltante")
        
        # Verificar telebot
        resultado = ssh.ejecutar_comando("python3 -c 'import telebot; print(\"✅ Telebot OK\")'")
        if "✅ Telebot OK" in resultado:
            print("✅ Telebot instalado")
        else:
            print("❌ Telebot faltante")
    
    def _iniciar_bot(self, ssh):
        """Inicia el bot en segundo plano"""
        print("\n🚀 Iniciando bot:")
        comando_inicio = "cd webfinal/mi_app && nohup python3 telegram_bot_always.py > telegram_bot.log 2>&1 &"
        ssh.ejecutar_comando(comando_inicio)
        
        print("\n⏳ Esperando 8 segundos para inicio...")
        time.sleep(8)
        
        # Verificar log
        print("\n📋 Log del bot:")
        resultado = ssh.ejecutar_comando("cd webfinal/mi_app && tail -10 telegram_bot.log")
        if resultado:
            print(resultado)
            
            if "Error crítico" in resultado:
                print("❌ Errores críticos detectados")
            elif "Bot de Telegram iniciado" in resultado:
                print("✅ Bot iniciado exitosamente")
            else:
                print("⚠️ Estado incierto, revisar log")
    
    def _verificar_instancia_unica(self, ssh):
        """Verifica que solo hay una instancia del bot"""
        print("\n🔍 Verificando instancia única:")
        resultado = ssh.ejecutar_comando("ps aux | grep telegram_bot_always | grep -v grep | wc -l")
        if resultado.strip():
            num_procesos = resultado.strip()
            print(f"Número de procesos: {num_procesos}")
            if num_procesos == "1":
                print("✅ Perfecto! Solo una instancia")
            elif num_procesos == "0":
                print("❌ Bot no se inició")
            else:
                print(f"⚠️ Hay {num_procesos} instancias - conflicto!")


def main():
    """Función principal con argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(
        description="🤖 Bot Manager - Gestión centralizada del bot de Telegram",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python bot_manager.py --clean          # Limpiar múltiples instancias y reiniciar
  python bot_manager.py --restart        # Reinicio simple
  python bot_manager.py --verify-token   # Verificar token y reiniciar
  python bot_manager.py --install-deps   # Instalar dependencias y reiniciar
  python bot_manager.py --check-chat-id  # Verificar configuración de chat ID
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--clean', action='store_true', 
                      help='Limpiar múltiples instancias y reiniciar')
    group.add_argument('--restart', action='store_true', 
                      help='Reinicio simple del bot')
    group.add_argument('--verify-token', action='store_true', 
                      help='Verificar token correcto y reiniciar')
    group.add_argument('--install-deps', action='store_true', 
                      help='Instalar dependencias y reiniciar')
    group.add_argument('--check-chat-id', action='store_true', 
                      help='Verificar configuración de chat ID')
    
    args = parser.parse_args()
    
    try:
        manager = BotManager()
        
        if args.clean:
            manager.limpiar_y_reiniciar()
        elif args.restart:
            manager.reiniciar_simple()
        elif args.verify_token:
            manager.verificar_token_y_reiniciar()
        elif args.install_deps:
            manager.instalar_dependencias_y_reiniciar()
        elif args.check_chat_id:
            manager.verificar_chat_id()
        
        print("\n🎯 OPERACIÓN COMPLETADA")
        
    except Exception as e:
        print(f"❌ Error en la ejecución: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()