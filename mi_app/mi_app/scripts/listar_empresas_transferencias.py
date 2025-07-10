import os
from supabase import create_client

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

if __name__ == '__main__':
    response = supabase.table('transferencias').select('empresa').execute()
    empresas = set()
    if response.data:
        for row in response.data:
            nombre = row.get('empresa')
            if nombre:
                empresas.add(nombre)
    print('Empresas únicas en la tabla transferencias:')
    for emp in sorted(empresas):
        print(f'- {emp}')
    print(f'\nTotal: {len(empresas)} empresas únicas.') 