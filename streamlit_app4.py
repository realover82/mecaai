import streamlit as st
import pandas as pd
from datetime import datetime

# csv2.py와 csv-b.py에서 함수들을 가져옵니다.
from csv2 import read_csv_with_dynamic_header, analyze_data
from csv_Fw import read_csv_with_dynamic_header_for_Fw, analyze_Fw_data
from csv_RfTx import read_csv_with_dynamic_header_for_RfTx, analyze_RfTx_data
from csv_Semi import read_csv_with_dynamic_header_for_Semi, analyze_Semi_data
from csv_Batadc import read_csv_with_dynamic_header_for_Batadc, analyze_Batadc_data

def display_analysis_result(df, file_name, analysis_function, date_col_name):
    """분석 결과를 Streamlit에 표시하는 함수 (분석 함수와 날짜 컬럼명을 인자로 받음)"""
    if df is None:
        st.error("데이터 로드에 실패했습니다. 파일 형식을 확인해주세요.")
        return

    st.markdown(f"### '{file_name}' 분석 리포트")
    with st.spinner("데이터 분석 중..."):
        summary_data, all_dates = analysis_function(df)
        
        kor_date_cols = [f"{d.strftime('%y%m%d')}" for d in all_dates]
        
        st.write(f"**분석 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.markdown("---")

        for jig in sorted(summary_data.keys()):
            st.subheader(f"구분: {jig}")
            
            report_data = {
                '지표': ['총 테스트 수', 'PASS', '가성불량', '진성불량', 'FAIL']
            }
            
            for date_iso, date_str in zip([d.strftime('%Y-%m-%d') for d in all_dates], kor_date_cols):
                data_point = summary_data[jig].get(date_iso)
                if data_point:
                    report_data[date_str] = [
                        data_point['total_test'],
                        data_point['pass'],
                        data_point['false_defect'],
                        data_point['true_defect'],
                        data_point['fail']
                    ]
                else:
                    report_data[date_str] = ['N/A'] * 5
            
            report_df = pd.DataFrame(report_data)
            st.table(report_df)
            
            # for date_iso, date_str in zip([d.strftime('%Y-%m-%d') for d in all_dates], kor_date_cols):
            #     data_point = summary_data[jig].get(date_iso)
            #     if data_point and data_point['false_defect_sns']:
            #         st.write(f"**({date_str}) 가성불량 시리얼 번호 목록 ({jig})**")
            #         for sn in data_point['false_defect_sns']:
            #             st.code(f"      {sn}")
            #         st.markdown("---")
            
        st.success("분석이 완료되었습니다!")

@st.cache_data
def read_pcb_data(uploaded_file):
    return read_csv_with_dynamic_header(uploaded_file)

@st.cache_data
def read_fw_data(uploaded_file):
    return read_csv_with_dynamic_header_for_Fw(uploaded_file)

@st.cache_data
def read_rftx_data(uploaded_file):
    return read_csv_with_dynamic_header_for_RfTx(uploaded_file)

@st.cache_data
def read_semi_data(uploaded_file):
    return read_csv_with_dynamic_header_for_Semi(uploaded_file)
    
@st.cache_data
def read_batadc_data(uploaded_file):
    return read_csv_with_dynamic_header_for_Batadc(uploaded_file)

def main():
    st.set_page_config(layout="wide")
    st.title("리모컨 생산 데이터 분석 툴")
    st.markdown("---")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["파일 PCB 분석", "파일 fw 분석", "파일 rftx 분석", "파일 semi 분석", "파일 func 분석"])

    with tab1:
        st.header("파일 PCB (Pcb_Process)")
        uploaded_file = st.file_uploader("파일 PCB를 선택하세요", type=["csv"], key="uploader_pcb")
        if uploaded_file:
            df = read_pcb_data(uploaded_file)
            st.dataframe(df.head())
            if st.button("파일 PCB 분석 실행", key="analyze_pcb"):
                display_analysis_result(df, uploaded_file.name, analyze_data, 'PcbStartTime')

    with tab2:
        st.header("파일 Fw (Fw_Process)")
        uploaded_file = st.file_uploader("파일 Fw를 선택하세요", type=["csv"], key="uploader_fw")
        if uploaded_file:
            df = read_fw_data(uploaded_file)
            st.dataframe(df.head())
            if st.button("파일 Fw 분석 실행", key="analyze_fw"):
                display_analysis_result(df, uploaded_file.name, analyze_Fw_data, 'FwStamp')

    with tab3:
        st.header("파일 RfTx (RfTx_Process)")
        uploaded_file = st.file_uploader("파일 RfTx를 선택하세요", type=["csv"], key="uploader_rftx")
        if uploaded_file:
            df = read_rftx_data(uploaded_file)
            st.dataframe(df.head())
            if st.button("파일 RfTx 분석 실행", key="analyze_rftx"):
                display_analysis_result(df, uploaded_file.name, analyze_RfTx_data, 'RfTxStamp')

    with tab4:
        st.header("파일 Semi (SemiAssy_Process)")
        uploaded_file = st.file_uploader("파일 Semi를 선택하세요", type=["csv"], key="uploader_semi")
        if uploaded_file:
            df = read_semi_data(uploaded_file)
            st.dataframe(df.head())
            if st.button("파일 Semi 분석 실행", key="analyze_semi"):
                display_analysis_result(df, uploaded_file.name, analyze_Semi_data, 'SemiAssyStartTime')

    with tab5:
        st.header("파일 Func (Func_Process)")
        uploaded_file = st.file_uploader("파일 Func를 선택하세요", type=["csv"], key="uploader_func")
        if uploaded_file:
            df = read_batadc_data(uploaded_file)
            st.dataframe(df.head())
            if st.button("파일 Func 분석 실행", key="analyze_func"):
                display_analysis_result(df, uploaded_file.name, analyze_Batadc_data, 'BatadcStamp')

if __name__ == "__main__":
    main()
