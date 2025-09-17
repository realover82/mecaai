# streamlit_app.py 파일 (수정)

import streamlit as st
import pandas as pd
from datetime import datetime
import io

# csv2.py와 csv-b.py에서 함수들을 가져옵니다.
from csv2 import read_csv_with_dynamic_header, analyze_data
from csv_Fw import read_csv_with_dynamic_header_for_Fw, analyze_Fw_data
from csv_RfTx import read_csv_with_dynamic_header_for_RfTx, analyze_RfTx_data
from csv_Semi import read_csv_with_dynamic_header_for_Semi, analyze_Semi_data
from csv_Batadc import read_csv_with_dynamic_header_for_Batadc, analyze_Batadc_data

# to_markdown() 대신 사용할 수동 마크다운 변환 함수
def df_to_markdown_manual(df, index=False):
    """
    tabulate 없이 DataFrame을 마크다운 테이블 문자열로 변환합니다.
    """
    if df.empty:
        return "데이터가 없습니다."

    # 헤더 생성
    if index:
        cols = [''] + list(df.columns)
    else:
        cols = list(df.columns)
    
    header = "| " + " | ".join(cols) + " |"
    
    # 구분선 생성 (왼쪽 정렬)
    separator = "|-" + "|-".join(['---'] * len(cols)) + "|"
    
    # 데이터 행 생성
    rows = []
    for _, row in df.iterrows():
        if index:
            row_data = [str(val) for val in [row.name] + list(row.values)]
        else:
            row_data = [str(val) for val in list(row.values)]
        rows.append("| " + " | ".join(row_data) + " |")

    return "\n".join([header, separator] + rows)


def display_analysis_result(analysis_key, file_name):
    """ session_state에 저장된 분석 결과를 Streamlit에 표시하는 함수"""
    if st.session_state.analysis_results[analysis_key] is None:
        st.error("데이터 로드에 실패했습니다. 파일 형식을 확인해주세요.")
        return

    # df_result = st.session_state.analysis_results[analysis_key]
    summary_data, all_dates = st.session_state.analysis_data[analysis_key]
    
    st.markdown(f"### '{file_name}' 분석 리포트")
    
    kor_date_cols = [f"{d.strftime('%y%m%d')}" for d in all_dates]
    
    st.write(f"**분석 시간**: {st.session_state.analysis_time[analysis_key]}")
    st.markdown("---")

    all_reports_text = ""
    
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
        
        # 수동으로 만든 함수를 사용해 마크다운 테이블 생성 및 출력
        markdown_table = df_to_markdown_manual(report_df)
        st.markdown(markdown_table) # st.table 대신 st.markdown 사용
        all_reports_text += f"--- 구분({jig}) ---\n"
        all_reports_text += markdown_table + "\n\n"

    st.success("분석이 완료되었습니다!")

    # 분석 결과를 CSV 파일로 다운로드하는 버튼 (st.download_button)
    st.download_button(
        label="분석 결과 다운로드",
        data=all_reports_text.encode('utf-8'),
        file_name=f"{file_name}_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
    )

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

    # session_state 초기화
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = {
            'pcb': None, 'fw': None, 'rftx': None, 'semi': None, 'func': None
        }
    if 'uploaded_files' not in st.session_state:
        st.session_state.uploaded_files = {
            'pcb': None, 'fw': None, 'rftx': None, 'semi': None, 'func': None
        }
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = {
            'pcb': None, 'fw': None, 'rftx': None, 'semi': None, 'func': None
        }
    if 'analysis_time' not in st.session_state:
        st.session_state.analysis_time = {
            'pcb': None, 'fw': None, 'rftx': None, 'semi': None, 'func': None
        }

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["파일 PCB 분석", "파일 Fw 분석", "파일 RfTx 분석", "파일 Semi 분석", "파일 Func 분석"])

    with tab1:
        st.header("파일 PCB (Pcb_Process)")
        st.session_state.uploaded_files['pcb'] = st.file_uploader("파일 PCB를 선택하세요", type=["csv"], key="uploader_pcb")
        if st.session_state.uploaded_files['pcb']:
            if st.button("파일 PCB 분석 실행", key="analyze_pcb"):
                df = read_pcb_data(st.session_state.uploaded_files['pcb'])
                if df is not None:
                    with st.spinner("데이터 분석 및 저장 중..."):
                        st.session_state.analysis_results['pcb'] = df
                        st.session_state.analysis_data['pcb'] = analyze_data(df)
                        st.session_state.analysis_time['pcb'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    st.success("분석 완료! 결과가 저장되었습니다.")
                else:
                    st.error("PCB 데이터 파일을 읽을 수 없습니다.")

            if st.session_state.analysis_results['pcb'] is not None:
                display_analysis_result('pcb', st.session_state.uploaded_files['pcb'].name)

    with tab2:
        st.header("파일 Fw (Fw_Process)")
        st.session_state.uploaded_files['fw'] = st.file_uploader("파일 Fw를 선택하세요", type=["csv"], key="uploader_fw")
        if st.session_state.uploaded_files['fw']:
            if st.button("파일 Fw 분석 실행", key="analyze_fw"):
                df = read_fw_data(st.session_state.uploaded_files['fw'])
                if df is not None:
                    with st.spinner("데이터 분석 및 저장 중..."):
                        st.session_state.analysis_results['fw'] = df
                        st.session_state.analysis_data['fw'] = analyze_Fw_data(df)
                        st.session_state.analysis_time['fw'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    st.success("분석 완료! 결과가 저장되었습니다.")
                else:
                    st.error("Fw 데이터 파일을 읽을 수 없습니다.")

            if st.session_state.analysis_results['fw'] is not None:
                display_analysis_result('fw', st.session_state.uploaded_files['fw'].name)

    with tab3:
        st.header("파일 RfTx (RfTx_Process)")
        st.session_state.uploaded_files['rftx'] = st.file_uploader("파일 RfTx를 선택하세요", type=["csv"], key="uploader_rftx")
        if st.session_state.uploaded_files['rftx']:
            if st.button("파일 RfTx 분석 실행", key="analyze_rftx"):
                df = read_rftx_data(st.session_state.uploaded_files['rftx'])
                if df is not None:
                    with st.spinner("데이터 분석 및 저장 중..."):
                        st.session_state.analysis_results['rftx'] = df
                        st.session_state.analysis_data['rftx'] = analyze_RfTx_data(df)
                        st.session_state.analysis_time['rftx'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    st.success("분석 완료! 결과가 저장되었습니다.")
                else:
                    st.error("RfTx 데이터 파일을 읽을 수 없습니다.")

            if st.session_state.analysis_results['rftx'] is not None:
                display_analysis_result('rftx', st.session_state.uploaded_files['rftx'].name)

    with tab4:
        st.header("파일 Semi (SemiAssy_Process)")
        st.session_state.uploaded_files['semi'] = st.file_uploader("파일 Semi를 선택하세요", type=["csv"], key="uploader_semi")
        if st.session_state.uploaded_files['semi']:
            if st.button("파일 Semi 분석 실행", key="analyze_semi"):
                df = read_semi_data(st.session_state.uploaded_files['semi'])
                if df is not None:
                    with st.spinner("데이터 분석 및 저장 중..."):
                        st.session_state.analysis_results['semi'] = df
                        st.session_state.analysis_data['semi'] = analyze_Semi_data(df)
                        st.session_state.analysis_time['semi'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    st.success("분석 완료! 결과가 저장되었습니다.")
                else:
                    st.error("Semi 데이터 파일을 읽을 수 없습니다.")

            if st.session_state.analysis_results['semi'] is not None:
                display_analysis_result('semi', st.session_state.uploaded_files['semi'].name)

    with tab5:
        st.header("파일 Func (Func_Process)")
        st.session_state.uploaded_files['func'] = st.file_uploader("파일 Func를 선택하세요", type=["csv"], key="uploader_func")
        if st.session_state.uploaded_files['func']:
            if st.button("파일 Func 분석 실행", key="analyze_func"):
                df = read_batadc_data(st.session_state.uploaded_files['func'])
                if df is not None:
                    with st.spinner("데이터 분석 및 저장 중..."):
                        st.session_state.analysis_results['func'] = df
                        st.session_state.analysis_data['func'] = analyze_Batadc_data(df)
                        st.session_state.analysis_time['func'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    st.success("분석 완료! 결과가 저장되었습니다.")
                else:
                    st.error("Func 데이터 파일을 읽을 수 없습니다.")
            
            if st.session_state.analysis_results['func'] is not None:
                display_analysis_result('func', st.session_state.uploaded_files['func'].name)
            
if __name__ == "__main__":
    main()
