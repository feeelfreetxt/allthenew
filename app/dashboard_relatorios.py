import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import traceback
from datetime import datetime

def exibir_relatorio_individual(self, relatorio):
    """Exibe o relatório individual na interface com gráficos separados por grupo"""
    try:
        if not relatorio:
            st.warning("Relatório vazio ou inválido")
            return
            
        # Exibir cabeçalho com estilo melhorado
        st.markdown("""
            <style>
            .header-container {
                background-color: #f0f2f6;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
            .metric-container {
                display: flex;
                justify-content: space-between;
                flex-wrap: wrap;
            }
            .chart-container {
                margin-top: 30px;
                padding: 20px;
                background-color: white;
                border-radius: 10px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            </style>
        """, unsafe_allow_html=True)

        # Cabeçalho principal
        st.markdown(f"""
            <div class="header-container">
                <h2>Relatório de Desempenho por Grupo</h2>
                <p>Período: {relatorio['periodo']}</p>
            </div>
        """, unsafe_allow_html=True)

        # Criar tabs para separar os grupos
        tab_julio, tab_leandro = st.tabs(["Grupo Julio", "Grupo Leandro"])

        # Processar dados por grupo
        for grupo, tab in [("julio", tab_julio), ("leandro", tab_leandro)]:
            with tab:
                colaboradores = [c for c in relatorio['colaboradores'] if c['grupo'].lower() == grupo]
                if not colaboradores:
                    st.warning(f"Nenhum colaborador encontrado no grupo {grupo.title()}")
                    continue

                # Criar gráfico de barras para métricas principais
                fig = go.Figure()
                nomes = [c['nome'] for c in colaboradores]
                
                # Adicionar barras para cada métrica
                fig.add_trace(go.Bar(
                    name='Taxa Preenchimento',
                    x=nomes,
                    y=[c['metricas'].get('taxa_preenchimento', 0) for c in colaboradores],
                    marker_color='#2ecc71'
                ))
                
                fig.add_trace(go.Bar(
                    name='Taxa Padronização',
                    x=nomes,
                    y=[c['metricas'].get('taxa_padronizacao', 0) for c in colaboradores],
                    marker_color='#3498db'
                ))
                
                fig.add_trace(go.Bar(
                    name='Score Qualidade',
                    x=nomes,
                    y=[c['metricas'].get('score_qualidade', 0) for c in colaboradores],
                    marker_color='#e74c3c'
                ))

                # Atualizar layout
                fig.update_layout(
                    title=f'Métricas do Grupo {grupo.title()}',
                    barmode='group',
                    xaxis_title="Colaboradores",
                    yaxis_title="Percentual (%)",
                    height=500,
                    template='plotly_white',
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right",
                        x=1
                    )
                )

                st.plotly_chart(fig, use_container_width=True)

                # Tabela detalhada
                st.markdown("### Detalhamento por Colaborador")
                df_grupo = pd.DataFrame([{
                    'Colaborador': c['nome'],
                    'Total Registros': c['metricas'].get('total_registros', 0),
                    'Taxa Preenchimento (%)': f"{c['metricas'].get('taxa_preenchimento', 0):.1f}",
                    'Taxa Padronização (%)': f"{c['metricas'].get('taxa_padronizacao', 0):.1f}",
                    'Score Qualidade': f"{c['metricas'].get('score_qualidade', 0):.1f}"
                } for c in colaboradores])
                
                st.dataframe(
                    df_grupo.style.background_gradient(subset=['Score Qualidade'], cmap='RdYlGn'),
                    hide_index=True
                )

                # Adicionar métricas individuais em cards
                st.markdown("### Métricas Individuais")
                cols = st.columns(len(colaboradores))
                for idx, (col, colab) in enumerate(zip(cols, colaboradores)):
                    with col:
                        st.markdown(f"""
                            <div style='padding: 10px; border-radius: 5px; border: 1px solid #ddd;'>
                                <h4>{colab['nome']}</h4>
                                <p>Score: {colab['metricas'].get('score_qualidade', 0):.1f}</p>
                                <p>Registros: {colab['metricas'].get('total_registros', 0)}</p>
                            </div>
                        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Erro ao exibir relatório: {str(e)}")
        st.error(traceback.format_exc())