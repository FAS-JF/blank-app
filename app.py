import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Configurações iniciais para mobile
st.set_page_config(
    page_title="Análise de Carreira",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Função de categorização
def categorizar_area(row):
    codigo = str(row.get('Codigo', '')).upper()
    disciplina = str(row.get('Disciplina', '')).upper()
    mapeamento = {
        'MAT': 'Matemática', 'FIS': 'Física', 'CEL': 'Eletrônica',
        'ENE': 'Sistemas de Potência', 'CÁLCULO': 'Matemática',
        'FÍSICA': 'Física', 'LABORATÓRIO': 'Práticas'
    }
    for key, value in mapeamento.items():
        if codigo.startswith(key) or key in disciplina:
            return value
    return 'Outras'

# Função para carregar dados acadêmicos
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('historico.csv').rename(columns={
            'Código': 'Codigo',
            'Horas/Aula': 'Horas'
        })
        df['Nota'] = pd.to_numeric(df['Nota'], errors='coerce').fillna(0)
        df['Horas'] = pd.to_numeric(df['Horas'], errors='coerce').fillna(0)
        
        df['Area'] = df.apply(categorizar_area, axis=1)
        df['Creditos'] = (df['Horas'] // 15).astype(int)
        return df
    except Exception as e:
        st.error(f"Erro na carga de dados: {str(e)}")
        return pd.DataFrame()

# Função para análise de carreira
def create_career_assessment(ratings):
    benchmark = {
        'Competência': ['Engenharia Elétrica', 'Power Line Communication', 'Gestão de Projetos',
                       'Atendimento ao Cliente', 'Análise de Dados', 'Vendas Técnicas',
                       'Automação Industrial', 'Liderança de Equipes', 'Sustentabilidade Energética',
                       'Transformação Digital'],
        'Benchmark': [3.8, 3.2, 4.1, 3.5, 3.9, 3.4, 4.0, 3.7, 4.2, 3.6]
    }
    
    df = pd.DataFrame({
        'Competência': ratings.keys(),
        'Sua Avaliação': ratings.values(),
        'Média de Mercado': benchmark['Benchmark']
    })
    
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=df['Sua Avaliação'],
        theta=df['Competência'],
        fill='toself',
        name='Seu Perfil',
        line_color='#636EFA'
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=df['Média de Mercado'],
        theta=df['Competência'],
        fill='toself',
        name='Média de Mercado',
        line_color='#EF553B'
    ))
    
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        title='Análise Comparativa de Competências',
        template='plotly_dark',
        height=600
    )
    
    fig_bar = px.bar(df, 
                    x='Competência', 
                    y=['Sua Avaliação', 'Média de Mercado'],
                    barmode='group',
                    title='Comparação Detalhada',
                    labels={'value': 'Nível', 'variable': 'Legenda'},
                    color_discrete_map={
                        'Sua Avaliação': '#636EFA',
                        'Média de Mercado': '#EF553B'
                    })
    
    return fig_radar, fig_bar, df

# Interface principal
def main():
    st.title("Gestão de Carreira Inteligente")
    
    df = load_data()
    
    tab1, tab2 = st.tabs(["📚 Análise Acadêmica", "🧠 Assessment de Carreira"])
    
    with tab1:
        if not df.empty:
            col1, col2 = st.columns(2)
            with col1:
                anos = st.multiselect(
                    "Selecione os anos:",
                    options=df['Ano'].unique(),
                    default=df['Ano'].unique()
                )
            with col2:
                areas = st.multiselect(
                    "Selecione as áreas:",
                    options=df['Area'].unique(),
                    default=df['Area'].unique()
                )
            
            filtered_df = df[df['Ano'].isin(anos) & df['Area'].isin(areas)]
            
            if not filtered_df.empty:
                df_acumulado = filtered_df.groupby('Ano', as_index=False).agg({'Creditos': 'sum'})
                df_acumulado['Acumulado'] = df_acumulado['Creditos'].cumsum()
                total_creditos = df_acumulado['Creditos'].sum()
                df_acumulado['% Acumulado'] = (df_acumulado['Acumulado'] / total_creditos * 100).round(2)
                
                col_metric1, col_metric2 = st.columns(2)
                with col_metric1:
                    st.metric("📦 Créditos Totais", total_creditos)
                with col_metric2:
                    ira = (filtered_df['Nota'] * filtered_df['Creditos']).sum() / total_creditos if total_creditos > 0 else 0
                    st.metric("🎯 IRA Atual", f"{ira:.2f}")
                
                st.subheader("Progressão Acadêmica")
                fig1 = px.bar(
                    filtered_df.groupby('Ano', as_index=False)['Creditos'].sum(),
                    x='Ano', y='Creditos', 
                    color='Creditos',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig1, use_container_width=True)
                
                st.subheader("Progressão Acumulada")
                fig3 = px.line(
                    df_acumulado,
                    x='Ano',
                    y='% Acumulado',
                    markers=True,
                    line_shape='spline',
                    title='Percentual Acumulado de Créditos'
                )
                st.plotly_chart(fig3, use_container_width=True)
                
                st.subheader("Distribuição de Notas por Área")
                fig2 = px.box(
                    filtered_df, 
                    x='Area', y='Nota', 
                    color='Area',
                    points="all"
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                st.subheader("Top 10 Disciplinas por Nota")
                top_disciplinas = filtered_df.nlargest(10, 'Nota')[['Disciplina', 'Nota', 'Creditos', 'Area']]
                st.dataframe(
                    top_disciplinas.style.format({'Nota': '{:.1f}'}),
                    use_container_width=True,
                    height=400
                )
            else:
                st.warning("Nenhum dado encontrado com os filtros selecionados")
        else:
            st.warning("Nenhum dado disponível para análise")
    
    with tab2:
        st.subheader("Análise de Potencial Profissional")
        
        if 'ratings' not in st.session_state:
            st.session_state.ratings = {
                'Engenharia Elétrica': 3.0,
                'Power Line Communication': 3.0,
                'Gestão de Projetos': 3.0,
                'Atendimento ao Cliente': 3.0,
                'Análise de Dados': 3.0,
                'Vendas Técnicas': 3.0,
                'Automação Industrial': 3.0,
                'Liderança de Equipes': 3.0,
                'Sustentabilidade Energética': 3.0,
                'Transformação Digital': 3.0
            }
        
        cols = st.columns(2)
        competencies = list(st.session_state.ratings.keys())
        
        for i, competence in enumerate(competencies):
            with cols[i%2]:
                st.session_state.ratings[competence] = st.slider(
                    f"{competence} (0-5)",
                    min_value=0.0,
                    max_value=5.0,
                    value=st.session_state.ratings[competence],
                    step=0.5,
                    key=f"slider_{competence}"
                )
        
        fig_radar, fig_bar, df_comparison = create_career_assessment(st.session_state.ratings)
        
        st.subheader("Análise Estratégica de Competências")
        st.plotly_chart(fig_radar, use_container_width=True)
        
        st.subheader("Comparação Detalhada com Benchmark de Mercado")
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.divider()
        
        df_comparison['Diferencial'] = df_comparison['Sua Avaliação'] - df_comparison['Média de Mercado']
        strengths = df_comparison[df_comparison['Diferencial'] > 0.5]
        
        if not strengths.empty:
            st.subheader("🔥 Seus Pontos Fortes Destacados")
            for _, row in strengths.iterrows():
                st.markdown(f"""
                - **{row['Competência']}**  
                Seu nível: {row['Sua Avaliação']}  
                Média mercado: {row['Média de Mercado']}  
                Diferencial: +{row['Diferencial']:.1f}
                """)
        else:
            st.warning("Ajuste as avaliações para identificar seus pontos fortes")

if __name__ == "__main__":
    main()
