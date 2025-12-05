import os

file_path = r'c:\Users\selmo\Documents\Projetos\TesteWeb\app.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
in_render_reviews = False
skip_lines = False

correct_render_reviews = """def render_reviews():
    user = get_current_user_cached()
    if not user:
        st.warning("Faça login para ver revisões pendentes.")
        return

    pending = database.get_pending_reviews(user.id)
    
    if not pending:
        st.container().success("🎉 Tudo em dia! Nenhum vídeo aguardando revisão.")
    else:
        st.info(f"Você tem {len(pending)} vídeo(s) aguardando aprovação.")
        
        # Convert to list to handle deletion during iteration
        for video_id in list(pending.keys()):
            item = pending[video_id]
            
            with st.expander(f"🎥 {item['current_title']}", expanded=True):
                col1, col2 = st.columns([1, 1.5])
                
                with col1:
                    st.markdown("### 🛑 Original")
                    st.caption("Metadados Atuais")
                    st.text_input("Título Atual", item['current_title'], disabled=True, key=f"old_title_{video_id}")
                    st.text_area("Descrição Atual", "...", disabled=True, height=100, key=f"old_desc_{video_id}")
                
                with col2:
                    st.markdown("### ✨ Sugestão Otimizada")
                    st.caption("Gerado por IA • Editável")
                    new_title = st.text_input("Novo Título", item['new_title'], key=f"title_{video_id}")
                    new_desc = st.text_area("Nova Descrição", item['new_description'], height=300, key=f"desc_{video_id}")
                    new_tags = st.text_area("Novas Tags", item['new_tags'], key=f"tags_{video_id}")
                    
                    if item.get('thumbnail_path'):
                        st.image(item['thumbnail_path'], caption="Thumbnail Gerada", width=300)

                st.divider()
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 4])
                
                if btn_col1.button("✅ Aprovar", key=f"approve_{video_id}", use_container_width=True):
                    service = get_authenticated_service()
                    if service:
                        if update_video_on_youtube(service, video_id, new_title, new_desc, new_tags, item.get('thumbnail_path')):
                            # Update History in DB
                            database.add_optimization_history(user.id, video_id, new_title, "optimized", {"timestamp": datetime.datetime.now().isoformat()})
                            # Remove from pending in DB
                            database.delete_pending_review(user.id, video_id)
                            st.toast("Vídeo atualizado com sucesso!", icon="✅")
                            st.rerun()
                            
                if btn_col2.button("🗑️ Rejeitar", key=f"reject_{video_id}", use_container_width=True):
                    database.delete_pending_review(user.id, video_id)
                    st.toast("Sugestão rejeitada.", icon="🗑️")
                    st.rerun()
"""

for line in lines:
    if line.strip().startswith("def render_reviews():"):
        in_render_reviews = True
        new_lines.append(correct_render_reviews)
        skip_lines = True
    elif in_render_reviews and (line.strip().startswith("# --- Tab 6") or line.strip().startswith("def fetch_google_models") or line.strip().startswith("# --- Tab Report")):
        in_render_reviews = False
        skip_lines = False
        new_lines.append(line)
    elif skip_lines:
        continue
    else:
        new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Indentation fixed.")
