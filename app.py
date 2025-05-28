import streamlit as st
import locale
from datetime import datetime
import pandas as pd
from fpdf import FPDF
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from io import BytesIO

# --- Configuración inicial ---
locale.setlocale(locale.LC_ALL, 'es_CO.UTF-8')
st.set_page_config(
    page_title="ContaHogar Pro",
    layout="wide",
    page_icon="💰",
    initial_sidebar_state="expanded"
)

# --- CSS Mejorado ---
st.markdown("""
<style>
    :root {
        --color-primario: #4ECDC4;
        --color-secundario: #FF6B6B;
    }
    
    .persona-card {
        transition: all 0.3s ease;
        border-radius: 12px;
        padding: 15px;
        margin: 12px 0;
        background: white;
        box-shadow: 0 4px 8px rgba(0,0,0,0.05);
        border-left: 5px solid var(--color-primario);
    }
    
    .persona-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.1);
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
    }
    
    .stButton>button {
        transition: all 0.2s;
        border-radius: 8px !important;
        border: 1px solid var(--color-primario) !important;
    }
    
    .stButton>button:hover {
        transform: scale(1.02);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .stNumberInput input, .stTextInput input {
        border-radius: 8px !important;
        border: 1px solid #ddd !important;
    }
    
    .total-card {
        background: linear-gradient(135deg, #f8f9fa, #e9ecef);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 4px solid var(--color-primario);
    }
    
    .alerta-card {
        background: #FFF3F3;
        border-left: 4px solid var(--color-secundario);
    }
</style>
""", unsafe_allow_html=True)

# --- Datos de Ejemplo ---
COLORES = {
    "rosa": "#FFD1DC", "verde": "#C4E8C2",
    "azul": "#B5D8FF", "amarillo": "#FFECB8"
}

ARRENDOS = {
    "Daniel Berrio": {"valor": 443_000, "color": COLORES["rosa"], "icono": "👨‍💻", "recordatorio": "05"},
    "Oscar Berrio": {"valor": 423_000, "color": COLORES["verde"], "icono": "👨‍🏫", "recordatorio": "05"},
    "Daniel Hurtado": {"valor": 406_000, "color": COLORES["azul"], "icono": "👨‍🔧", "recordatorio": "05"},
    "Henner Heredia": {"valor": 376_000, "color": COLORES["amarillo"], "icono": "👨‍🎨", "recordatorio": "05"}
}

# --- Funciones Principales ---
def conectar_google_sheets():
    """Conexión segura usando Streamlit Secrets"""
    scope = ["https://spreadsheets.google.com/feeds", 
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp"], scope)
    return gspread.authorize(creds)

def exportar_a_google_sheets(datos):
    try:
        client = conectar_google_sheets()
        sheet = client.open("ContaHogar").sheet1
        
        df = pd.DataFrame.from_dict(datos, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'Persona'}, inplace=True)
        df['Fecha'] = datetime.now().strftime("%Y-%m-%d")
        
        valores = df.values.tolist()
        
        if sheet.acell('A1').value is None:
            sheet.append_row(df.columns.tolist())
        
        sheet.append_rows(valores)
        return True
    except Exception as e:
        st.error(f"Error al exportar: {str(e)}")
        return False

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Reporte ContaHogar', 0, 1, 'C')
        self.ln(10)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def generar_pdf(gastos):
    """Genera un PDF profesional con columnas perfectamente alineadas"""
    try:
        pdf = PDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- Encabezado ---
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, 'Reporte Detallado de Gastos', 0, 1, 'C')
        pdf.ln(8)
        
        pdf.set_font('Arial', 'I', 10)
        pdf.cell(0, 6, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M')}", 0, 1, 'C')
        pdf.ln(12)
        
        # --- Configuración de columnas ---
        # Ajustamos los anchos para mejor alineación
        col_widths = [55, 35, 35, 35, 35, 40]  # Última columna más ancha para totales
        
        # --- Encabezados de tabla ---
        pdf.set_font('Arial', 'B', 11)
        pdf.set_fill_color(79, 129, 189)  # Azul corporativo
        pdf.set_text_color(255, 255, 255)  # Texto blanco
        
        headers = ["Persona", "Arriendo", "Servicios", "Internet", "Aseo", "Total"]
        for i, header in enumerate(headers):
            pdf.cell(col_widths[i], 10, header, 1, 0, 'C', 1)
        pdf.ln()
        
        # --- Datos ---
        pdf.set_font('Arial', '', 10)
        pdf.set_text_color(0, 0, 0)  # Texto negro
        
        for nombre, datos in gastos.items():
            # Nombre (alineado a la izquierda)
            pdf.set_fill_color(240, 240, 240)  # Fondo gris claro
            pdf.cell(col_widths[0], 10, nombre, 1, 0, 'L', 1)
            
            # Valores numéricos (alineados a la derecha)
            pdf.set_fill_color(255, 255, 255)  # Fondo blanco
            valores = [
                f"${datos['valor']:,}",
                f"${datos['servicios']:,}",
                f"${datos['internet']:,}",
                f"${datos['aseo']:,}",
                f"${datos['total']:,}"
            ]
            
            for i, valor in enumerate(valores, start=1):
                pdf.cell(col_widths[i], 10, valor, 1, 0, 'R')
            
            pdf.ln()
        
        # --- Totales Generales ---
        pdf.set_font('Arial', 'B', 11)
        pdf.ln(5)
        
        # Calculamos totales
        totales = {
            "arriendo": sum(d['valor'] for d in gastos.values()),
            "servicios": sum(d['servicios'] for d in gastos.values()),
            "internet": sum(d['internet'] for d in gastos.values()),
            "aseo": sum(d['aseo'] for d in gastos.values()),
            "total": sum(d['total'] for d in gastos.values())
        }
        
        # Fila de totales
        pdf.set_fill_color(79, 129, 189)  # Mismo azul que encabezados
        pdf.set_text_color(255, 255, 255)  # Texto blanco
        
        pdf.cell(col_widths[0], 10, "TOTALES GENERALES", 1, 0, 'L', 1)
        pdf.cell(col_widths[1], 10, f"${totales['arriendo']:,}", 1, 0, 'R', 1)
        pdf.cell(col_widths[2], 10, f"${totales['servicios']:,}", 1, 0, 'R', 1)
        pdf.cell(col_widths[3], 10, f"${totales['internet']:,}", 1, 0, 'R', 1)
        pdf.cell(col_widths[4], 10, f"${totales['aseo']:,}", 1, 0, 'R', 1)
        pdf.cell(col_widths[5], 10, f"${totales['total']:,}", 1, 1, 'R', 1)
        
        # --- Notas ---
        pdf.ln(10)
        pdf.set_font('Arial', 'I', 9)
        pdf.set_text_color(0, 0, 0)  # Texto negro
        pdf.multi_cell(0, 5, "Nota: Este reporte muestra el desglose detallado de los gastos compartidos. Los valores incluyen arriendo base más servicios adicionales.")
        
        # Salida del PDF
        pdf_output = pdf.output(dest='S')
        return BytesIO(pdf_output.encode('latin1') if isinstance(pdf_output, str) else pdf_output)
        
    except Exception as e:
        st.error(f"Error al generar PDF: {str(e)}")
        return None

def calcular_totales(gastos):
    return {
        "arriendo": sum(d["valor"] for d in gastos.values()),
        "servicios": sum(d["servicios"] for d in gastos.values()),
        "internet": sum(d["internet"] for d in gastos.values()),
        "aseo": sum(d["aseo"] for d in gastos.values()),
        "total": sum(d["total"] for d in gastos.values())
    }

def verificar_recordatorios(gastos):
    hoy = datetime.now().day
    alertas = []
    for nombre, datos in gastos.items():
        dia_recordatorio = int(datos.get("recordatorio", 5))
        if hoy > dia_recordatorio and datos["total"] > datos["valor"]:
            alertas.append(nombre)
    return alertas

# --- Interfaz Principal ---
def main():
    st.title("🏠 ContaHogar Pro")
    st.markdown("#### Sistema de Gestión de Gastos Compartidos")
    
    # Inicializar session_state
    if 'gastos' not in st.session_state:
        st.session_state.gastos = {}
        for nombre in ARRENDOS:
            st.session_state.gastos[nombre] = {
                **ARRENDOS[nombre],
                "servicios": 0,
                "internet": 0,
                "aseo": 0,
                "total": ARRENDOS[nombre]["valor"]
            }
    
    # --- Sidebar ---
    with st.sidebar:
        st.header("📊 Totales Acumulados")
        
        if st.session_state.gastos:
            totales = calcular_totales(st.session_state.gastos)
            
            st.markdown(f"""
            <div class='total-card'>
                <h4>Resumen General</h4>
                <p>🏠 <b>Arriendos:</b> ${totales['arriendo']:,}</p>
                <p>💡 <b>Servicios:</b> ${totales['servicios']:,}</p>
                <p>🌐 <b>Internet:</b> ${totales['internet']:,}</p>
                <p>🧹 <b>Aseo:</b> ${totales['aseo']:,}</p>
                <hr>
                <h3>💰 Total: ${totales['total']:,}</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # Alertas
            alertas = verificar_recordatorios(st.session_state.gastos)
            if alertas:
                st.markdown("""
                <div class='total-card alerta-card'>
                    <h4>⚠️ Recordatorios</h4>
                    <p>Personas con pagos pendientes:</p>
                    <ul>
                """ + "\n".join([f"<li>{nombre}</li>" for nombre in alertas]) + """
                    </ul>
                </div>
                """, unsafe_allow_html=True)
            
            # Exportar datos
            st.divider()
            if st.button("📤 Exportar a Google Sheets"):
                if exportar_a_google_sheets(st.session_state.gastos):
                    st.success("Datos exportados correctamente")
                    st.balloons()
            
            if st.button("🖨️ Generar Reporte PDF"):
                pdf_file = generar_pdf(st.session_state.gastos)
                if pdf_file:
                    st.download_button(
                        label="⬇️ Descargar PDF",
                        data=pdf_file,
                        file_name=f"reporte_contahogar_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
    
    # --- Inputs de Gastos ---
    for nombre, data in ARRENDOS.items():
        with st.container():
            st.markdown(f"""
            <div class='persona-card'>
                <h4>{data['icono']} {nombre}</h4>
            </div>
            """, unsafe_allow_html=True)
            
            cols = st.columns(4)
            
            servicios = cols[0].number_input(
                "Servicios", 
                min_value=0, 
                value=st.session_state.gastos[nombre]["servicios"], 
                key=f"serv_{nombre}",
                format="%d"
            )
            
            internet = cols[1].number_input(
                "Internet", 
                min_value=0, 
                value=st.session_state.gastos[nombre]["internet"], 
                key=f"int_{nombre}",
                format="%d"
            )
            
            aseo = cols[2].number_input(
                "Aseo", 
                min_value=0, 
                value=st.session_state.gastos[nombre]["aseo"], 
                key=f"aseo_{nombre}",
                format="%d"
            )
            
            # Actualizar datos
            st.session_state.gastos[nombre] = {
                **data,
                "servicios": servicios,
                "internet": internet,
                "aseo": aseo,
                "total": data["valor"] + servicios + internet + aseo
            }
            
            cols[3].markdown(f"""
            <div style='background:#f8f9fa; padding:10px; border-radius:8px;'>
                <small>Subtotal:</small><br>
                <strong>${st.session_state.gastos[nombre]['total']:,}</strong>
            </div>
            """, unsafe_allow_html=True)
    
    # --- Pie de Página ---
    st.divider()
    st.caption(f"© {datetime.now().year} ContaHogar Pro | Desarrollado por Oscar Berrio")

if __name__ == "__main__":
    main()