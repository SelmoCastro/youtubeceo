import os

file_path = r'c:\Users\selmo\Documents\Projetos\TesteWeb\app.py'

# Read as binary
with open(file_path, 'rb') as f:
    content = f.read()

# Decode with ignore to strip bad bytes
text = content.decode('utf-8', errors='ignore')

# Marker to find the end of valid code
marker = 'st.json({k: "********" if "KEY" in k and v else v for k, v in current_config.items()})'

if marker in text:
    parts = text.split(marker)
    # Take the part before the marker + marker
    clean_text = parts[0] + marker + '\n'
else:
    # If marker not found, try to find the last valid function definition 'render_integrations'
    # or just use the text as is (risky if garbage is appended)
    print("Marker not found. Using text as is.")
    clean_text = text

# Append the correct router block
router_block = '''
# --- Main Router ---
if selected_page == "🏠 Início":
    render_home()
elif selected_page == "🚀 Desempenho":
    render_performance()
elif selected_page == "💰 Monetização":
    render_monetization()
elif selected_page == "📤 Upload":
    render_upload()
elif selected_page == "✨ Otimizar Existentes":
    render_optimize()
elif selected_page == "📝 Revisões Pendentes":
    render_reviews()
elif selected_page == "📋 Relatório":
    render_report()
elif selected_page == "🔌 Integrações":
    render_integrations()
'''

final_content = clean_text + router_block

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(final_content)

print('File repaired successfully.')
