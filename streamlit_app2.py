import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# --- 1. CSV 파일의 헤더를 동적으로 찾는 함수 ---
@st.cache_data
def read_csv_with_dynamic_header(uploaded_file):
    """
    업로드된 CSV 파일에서 컬럼명이 있는 행을 동적으로 찾아 DataFrame으로 로드하는 함수.
    """
    try:
        # 파일을 BytesIO 객체로 변환
        file_content = io.BytesIO(uploaded_file.getvalue())
        df_temp = pd.read_csv(file_content, header=None, nrows=100)
        
        keywords = ['SNumber', 'PcbStartTime', 'PcbMaxIrPwr', 'PcbPass']
        
        header_row = None
        for i, row in df_temp.iterrows():
            row_values = [str(x).strip() for x in row.values if pd.notna(x)]
            
            if all(keyword in row_values for keyword in keywords):
                header_row = i
                break
        
        if header_row is not None:
            file_content.seek(0) # 파일 포인터를 다시 처음으로
            df = pd.read_csv(file_content, header=header_row)
            return df
        else:
            st.warning("경고: 컬럼명 행을 찾을 수 없습니다.")
            return None
    except Exception as e:
        st.error(f"오류: 파일 로딩 중 예상치 못한 에러가 발생했습니다: {e}")
        return None

# --- 2. 데이터 분석 및 리포트 생성 로직 함수 ---
def analyze_data(df):
    """
    DataFrame을 분석하고 리포트 데이터를 생성하는 함수.
    """
    # 데이터 전처리
    for col in df.columns:
        df[col] = df[col].apply(lambda x: x.strip('="').strip('"') if isinstance(x, str) else x)

    df['PcbStartTime'] = pd.to_datetime(df['PcbStartTime'], errors='coerce')
    df['PassStatusNorm'] = df['PcbPass'].fillna('').astype(str).str.strip().str.upper()

    summary_data = {}
    
    # 'PcbMaxIrPwr'를 기준으로 그룹화
    for jig, group in df.groupby('PcbMaxIrPwr'):
        if group['PcbStartTime'].dt.date.dropna().empty:
            continue
        
        for d, day_group in group.groupby(group['PcbStartTime'].dt.date):
            if pd.isna(d):
                continue
            
            date_iso = pd.to_datetime(d).strftime("%Y-%m-%d")

            # VBA 논리 반영: 'O'가 있는 SN 목록 생성
            pass_sns_series = day_group.groupby('SNumber')['PassStatusNorm'].apply(lambda x: 'O' in x.tolist())
            pass_sns = pass_sns_series[pass_sns_series].index.tolist()

            # 합격(O) 수
            pass_count = (day_group['PassStatusNorm'] == 'O').sum()

            # 가성불량 (X이지만 'O' 기록이 있는 SN) 수 및 해당 SN 목록
            false_defect_df = day_group[(day_group['PassStatusNorm'] == 'X') & (day_group['SNumber'].isin(pass_sns))]
            false_defect_count = false_defect_df.shape[0]
            false_defect_sns = false_defect_df['SNumber'].unique().tolist()

            # 진성불량 (오직 'X' 기록만 있는 SN) 수
            true_defect_df = day_group[(day_group['PassStatusNorm'] == 'X') & (~day_group['SNumber'].isin(pass_sns))]
            true_defect_count = true_defect_df.shape[0]

            # 총 테스트 수 및 총 불합격(FAIL) 수
            total_test = len(day_group)
            fail_count = false_defect_count + true_defect_count

            rate = 100 * pass_count / total_test if total_test > 0 else 0

            if jig not in summary_data:
                summary_data[jig] = {}
            summary_data[jig][date_iso] = {
                'total_test': total_test,
                'pass': pass_count,
                'false_defect': false_defect_count,
                'true_defect': true_defect_count,
                'fail': fail_count,
                'pass_rate': f"{rate:.1f}%",
                'false_defect_sns': false_defect_sns
            }
    
    return summary_data

# --- 3. Streamlit 웹 인터페이스 구성 ---
def main():
    st.set_page_config(layout="wide")
    st.title("리모컨 생산 데이터 분석 리포트")
    st.markdown("---")

    uploaded_file = st.file_uploader("CSV 파일을 선택하세요", type=["csv"])

    if uploaded_file is not None:
        st.success(f"파일이 성공적으로 업로드되었습니다: {uploaded_file.name}")
        df = read_csv_with_dynamic_header(uploaded_file)
        
        if df is not None:
            st.markdown("### 데이터 미리보기")
            st.dataframe(df.head())
            st.markdown("---")
            
            if st.button("분석 실행"):
                st.markdown("### 분석 리포트")
                
                with st.spinner("데이터 분석 중... 잠시만 기다려주세요."):
                    summary_data = analyze_data(df)
                    
                    all_dates = sorted(list(df['PcbStartTime'].dt.date.dropna().unique()))
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
                        
#                         for date_iso, date_str in zip([d.strftime('%Y-%m-%d') for d in all_dates], kor_date_cols):
#                             data_point = summary_data[jig].get(date_iso)
#                             if data_point and data_point['false_defect_sns']:
#                                 st.write(f"**({date_str}) 가성불량 시리얼 번호 목록 ({jig})**")
#                                 for sn in data_point['false_defect_sns']:
#                                     st.code(f"      {sn}")
#                                 st.markdown("---")
                                
                    st.success("분석이 완료되었습니다!")

if __name__ == "__main__":
    main()


