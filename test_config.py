import os
import importlib
import config

# Test Default (Banco de Chile)
print(f"Default Brand: {config.BRAND['name']} (ID: {config.BRAND['id']})")
assert config.BRAND['id'] == 'banco_chile'

# Test BancoEstado
os.environ['BRAND_ID'] = 'banco_estado'
importlib.reload(config)
print(f"Switched Brand: {config.BRAND['name']} (ID: {config.BRAND['id']})")
assert config.BRAND['id'] == 'banco_estado'

print("✅ Config test passed!")
