import streamlit as st
import pandas as pd
from datetime import datetime

# csv2.py와 csv-b.py에서 함수들을 가져옵니다.
from csv2 import read_csv_with_dynamic_header, analyze_data
from csv_Fw import read_csv_with_dynamic_header_for_Fw, analyze_Fw_data
from csv_RfTx import read_csv_with_dynamic_header_for_RfTx, analyze_RfTx_data
from csv_Semi import read_csv_with_dynamic_header_for_Semi, analyze_Semi_data
from csv_Batadc import read_csv_with_dynamic_header_for_Batadc, analyze_Batadc_data

# 분석 결과를 표시하는 함수
def display_analysis_result(df, file_name, analysis_function, date_col_name):
    if df is None:
        st.error("데이터 로드에 실패했습니다. 파일 형식을 확인해주세요.")
        return

    st.markdown(f"### '{file_name}' 분석 리포트")
    with st.spinner("데이터 분석 중..."):
        try:
            summary_data, all_dates = analysis_function(df)
            
            kor_date_cols = [f"{d.strftime('%y%m%d')}" for d in all_dates]
            
            st.write(f"**분석 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            st.markdown("---")

            # 각 지그의 리포트를 저장할 리스트
            all_reports = []

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

                # CSV 다운로드를 위해 DataFrame을 리스트에 추가
                all_reports.append(report_df.to_csv(index=False).encode('utf-8'))
            
            st.success("분석이 완료되었습니다!")

            # 모든 분석 결과를 하나의 CSV 파일로 다운로드하는 버튼
            if all_reports:
                st.download_button(
                    label="분석 결과 CSV 다운로드",
                    data='\n'.join([report.decode('utf-8') for report in all_reports]).encode('utf-8'),
                    file_name=f"{file_name}_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                )

        except Exception as e:
            st.error(f"분석 중 오류가 발생했습니다: {str(e)}")
            st.info("파일의 데이터 형식이나 필드명을 확인해주세요.")

# 캐싱 함수들... (이전 코드와 동일)
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

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["파일 PCB 분석", "파일 Fw 분석", "파일 RfTx 분석", "파일 Semi 분석", "파일 Func 분석"])

    with tab1:
        st.header("파일 PCB (Pcb_Process)")
        st.session_state.uploaded_files['pcb'] = st.file_uploader("파일 PCB를 선택하세요", type=["csv"], key="uploader_pcb")
        if st.session_state.uploaded_files['pcb']:
            df = read_pcb_data(st.session_state.uploaded_files['pcb'])
            st.dataframe(df.head())
            if st.button("파일 PCB 분석 실행", key="analyze_pcb"):
                st.session_state.analysis_results['pcb'] = df
                st.success("분석 완료! 다른 탭으로 이동해도 결과가 유지됩니다.")
        
        # 저장된 결과가 있으면 표시
        if st.session_state.analysis_results['pcb'] is not None:
            display_analysis_result(st.session_state.analysis_results['pcb'], st.session_state.uploaded_files['pcb'].name, analyze_data, 'PcbStartTime')
        elif st.session_state.uploaded_files['pcb']:
            st.error("PCB 데이터 파일을 읽을 수 없습니다.")

    with tab2:
        st.header("파일 Fw (Fw_Process)")
        st.session_state.uploaded_files['fw'] = st.file_uploader("파일 Fw를 선택하세요", type=["csv"], key="uploader_fw")
        if st.session_state.uploaded_files['fw']:
            df = read_fw_data(st.session_state.uploaded_files['fw'])
            st.dataframe(df.head())
            if st.button("파일 Fw 분석 실행", key="analyze_fw"):
                st.session_state.analysis_results['fw'] = df
                st.success("분석 완료! 다른 탭으로 이동해도 결과가 유지됩니다.")
        
        if st.session_state.analysis_results['fw'] is not None:
            display_analysis_result(st.session_state.analysis_results['fw'], st.session_state.uploaded_files['fw'].name, analyze_Fw_data, 'FwStamp')
        elif st.session_state.uploaded_files['fw']:
            st.error("Fw 데이터 파일을 읽을 수 없습니다.")

    with tab3:
        st.header("파일 RfTx (RfTx_Process)")
        st.session_state.uploaded_files['rftx'] = st.file_uploader("파일 RfTx를 선택하세요", type=["csv"], key="uploader_rftx")
        if st.session_state.uploaded_files['rftx']:
            df = read_rftx_data(st.session_state.uploaded_files['rftx'])
            st.dataframe(df.head())
            if st.button("파일 RfTx 분석 실행", key="analyze_rftx"):
                st.session_state.analysis_results['rftx'] = df
                st.success("분석 완료! 다른 탭으로 이동해도 결과가 유지됩니다.")

        if st.session_state.analysis_results['rftx'] is not None:
            display_analysis_result(st.session_state.analysis_results['rftx'], st.session_state.uploaded_files['rftx'].name, analyze_RfTx_data, 'RfTxStamp')
        elif st.session_state.uploaded_files['rftx']:
            st.error("RfTx 데이터 파일을 읽을 수 없습니다.")

    with tab4:
        st.header("파일 Semi (SemiAssy_Process)")
        st.session_state.uploaded_files['semi'] = st.file_uploader("파일 Semi를 선택하세요", type=["csv"], key="uploader_semi")
        if st.session_state.uploaded_files['semi']:
            df = read_semi_data(st.session_state.uploaded_files['semi'])
            st.dataframe(df.head())
            if st.button("파일 Semi 분석 실행", key="analyze_semi"):
                st.session_state.analysis_results['semi'] = df
                st.success("분석 완료! 다른 탭으로 이동해도 결과가 유지됩니다.")

        if st.session_state.analysis_results['semi'] is not None:
            display_analysis_result(st.session_state.analysis_results['semi'], st.session_state.uploaded_files['semi'].name, analyze_Semi_data, 'SemiAssyStartTime')
        elif st.session_state.uploaded_files['semi']:
            st.error("Semi 데이터 파일을 읽을 수 없습니다.")

    with tab5:
        st.header("파일 Func (Func_Process)")
        st.session_state.uploaded_files['func'] = st.file_uploader("파일 Func를 선택하세요", type=["csv"], key="uploader_func")
        if st.session_state.uploaded_files['func']:
            df = read_batadc_data(st.session_state.uploaded_files['func'])
            st.dataframe(df.head())
            if st.button("파일 Func 분석 실행", key="analyze_func"):
                st.session_state.analysis_results['func'] = df
                st.success("분석 완료! 다른 탭으로 이동해도 결과가 유지됩니다.")
                
        if st.session_state.analysis_results['func'] is not None:
            display_analysis_result(st.session_state.analysis_results['func'], st.session_state.uploaded_files['func'].name, analyze_Batadc_data, 'BatadcStamp')
        elif st.session_state.uploaded_files['func']:
            st.error("Func 데이터 파일을 읽을 수 없습니다.")
            
if __name__ == "__main__":
    main()
