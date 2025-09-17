#
# csv_Semi.py
# 이 파일은 Streamlit 앱에서 모듈로 사용됩니다.
# 따라서, 콘솔 출력 관련 코드(print, sys, io 등)는 모두 제거했습니다.

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

def read_csv_with_dynamic_header_for_Semi(uploaded_file):
    """SemiAssy 데이터에 맞는 키워드로 헤더를 찾아 DataFrame을 로드하는 함수"""
    try:
        file_content = io.BytesIO(uploaded_file.getvalue())
        df_temp = pd.read_csv(file_content, header=None, nrows=100)
        
        # 'SemiAssy' 관련 필드명으로 키워드 수정
        # 'SemiStamp' 대신 'SemiAssyStartTime'을 사용하도록 수정
        keywords = ['SNumber', 'SemiAssyStartTime', 'SemiAssyMaxSolarVolt', 'SemiAssyPass']
        
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
        return None

def analyze_Semi_data(df):
    """SemiAssy 데이터의 분석 로직을 담고 있는 함수"""
    # 데이터 전처리
    for col in df.columns:
        df[col] = df[col].apply(clean_string_format)

    # SemiAssyStartTime 열을 datetime 형식으로 변환
    df['SemiAssyStartTime'] = pd.to_datetime(df['SemiAssyStartTime'], errors='coerce')
    df['PassStatusNorm'] = df['SemiAssyPass'].fillna('').astype(str).str.strip().str.upper()

    summary_data = {}

    # 'SemiAssyMaxSolarVolt'를 기준으로 그룹화
    for jig, group in df.groupby('SemiAssyMaxSolarVolt'):
        if group['SemiAssyStartTime'].dt.date.dropna().empty:
            continue
        
        for d, day_group in group.groupby(group['SemiAssyStartTime'].dt.date):
            if pd.isna(d):
                continue
            
            date_iso = pd.to_datetime(d).strftime("%Y-%m-%d")

            pass_sns_series = day_group.groupby('SNumber')['PassStatusNorm'].apply(lambda x: 'O' in x.tolist())
            pass_sns = pass_sns_series[pass_sns_series].index.tolist()

            pass_count = (day_group['PassStatusNorm'] == 'O').sum()
            false_defect_df = day_group[(day_group['PassStatusNorm'] == 'X') & (day_group['SNumber'].isin(pass_sns))]
            false_defect_count = false_defect_df.shape[0]
            false_defect_sns = false_defect_df['SNumber'].unique().tolist()
            true_defect_df = day_group[(day_group['PassStatusNorm'] == 'X') & (~day_group['SNumber'].isin(pass_sns))]
            true_defect_count = true_defect_df.shape[0]

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
    
    all_dates = sorted(list(df['SemiAssyStartTime'].dt.date.dropna().unique()))
    return summary_data, all_dates
