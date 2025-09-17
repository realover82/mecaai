import pandas as pd
import numpy as np
import io
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# '="...' 형식의 문자열을 정리하는 함수
def clean_string_format(value):
    if isinstance(value, str) and value.startswith('="') and value.endswith('"'):
        return value[2:-1]
    return value

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
            file_content.seek(0)
            df = pd.read_csv(file_content, header=header_row)
            return df
        else:
            return None
    except Exception as e:
        # Streamlit 앱에서 오류를 처리하도록 None 반환
        return None

# --- 데이터 분석 및 리포트 생성 로직 함수 ---
def analyze_data(df):
    """
    DataFrame을 분석하고 리포트 데이터를 생성하는 함수.
    """
    # 데이터 전처리
    for col in df.columns:
        df[col] = df[col].apply(clean_string_format)

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
    
    return summary_data, sorted(list(df['PcbStartTime'].dt.date.dropna().unique()))

# --- Tkinter 코드는 이 파일에서 완전히 제거합니다. ---
