import pandas as pd
import numpy as np
import io
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

def clean_string_format(value):
    if isinstance(value, str) and value.startswith('="') and value.endswith('"'):
        return value[2:-1]
    return value

def read_csv_with_dynamic_header_for_Semi(uploaded_file):
    """SemiAssy 데이터에 맞는 키워드로 헤더를 찾아 DataFrame을 로드하는 함수"""
    try:
        # 여러 인코딩 방식으로 시도
        encodings = ['utf-8-sig', 'utf-8', 'cp949', 'euc-kr', 'latin-1']
        
        for encoding in encodings:
            try:
                # 파일을 임시로 읽어 헤더 행을 찾습니다.
                file_content = io.BytesIO(uploaded_file.getvalue())
                df_temp = pd.read_csv(file_content, header=None, nrows=100, encoding=encoding)
                
                # SemiAssy 데이터에 맞는 키워드 (더 유연하게 검색)
                keywords = ['SNumber', 'SemiAssy', 'Semi']  # 더 유연한 키워드
                
                header_row = None
                for i, row in df_temp.iterrows():
                    row_values = [str(x).strip() for x in row.values if pd.notna(x) and str(x) != 'nan']
                    
                    # 키워드를 하나씩 확인하여 매칭되는 개수 세기
                    matched_keywords = 0
                    for keyword in keywords:
                        if any(keyword in str(val) for val in row_values):
                            matched_keywords += 1
                    
                    # 최소 1개 이상의 키워드가 매칭되면 헤더로 간주 (조건 완화)
                    if matched_keywords >= 1:
                        header_row = i
                        break
                
                if header_row is not None:
                    # 헤더 행을 찾으면, 해당 행부터 파일을 다시 읽습니다.
                    file_content.seek(0)
                    df = pd.read_csv(file_content, header=header_row, encoding=encoding)
                    
                    # SemiAssy 관련 컬럼이 있는지 확인
                    semi_columns = [col for col in df.columns if 'SemiAssy' in str(col) or 'Semi' in str(col)]
                    if len(semi_columns) > 0:
                        return df
                else:
                    # 헤더 행을 찾지 못하면 첫 번째 행을 헤더로 시도
                    file_content.seek(0)
                    df = pd.read_csv(file_content, encoding=encoding)
                    
                    # SemiAssy 관련 컬럼이 있는지 확인
                    semi_columns = [col for col in df.columns if 'SemiAssy' in str(col) or 'Semi' in str(col)]
                    if len(semi_columns) > 0:
                        return df
                
            except UnicodeDecodeError:
                continue  # 다음 인코딩으로 시도
            except Exception as e:
                print(f"Error with encoding {encoding}: {e}")
                continue
        
        # 모든 시도가 실패한 경우, 기본 방식으로 읽기 시도
        file_content = io.BytesIO(uploaded_file.getvalue())
        df = pd.read_csv(file_content)
        
        # 데이터가 있고 SemiAssy 관련 컬럼이 없어도 일단 반환 (통합 파일일 수 있음)
        if len(df) > 0:
            return df
        else:
            return None
            
    except Exception as e:
        print(f"Final error reading CSV: {e}")
        return None

def analyze_Semi_data(df):
    """SemiAssy 데이터의 분석 로직을 담고 있는 함수"""
    try:
        # 필요한 컬럼이 있는지 확인
        required_columns = ['SNumber', 'SemiAssyStartTime', 'SemiAssyPass']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"Missing columns: {missing_columns}")
            # 빈 결과 반환
            return {}, []
        
        for col in df.columns:
            df[col] = df[col].apply(clean_string_format)
        
        # SemiAssyStartTime 컬럼 처리
        df['SemiAssyStartTime'] = pd.to_datetime(df['SemiAssyStartTime'], format='%Y%m%d%H%M%S', errors='coerce')
        df['PassStatusNorm'] = df['SemiAssyPass'].fillna('').astype(str).str.strip().str.upper()
        
        # 유효한 날짜가 있는 행만 필터링
        df_valid = df[df['SemiAssyStartTime'].notna()]
        
        if len(df_valid) == 0:
            print("No valid datetime data found")
            return {}, []
        
        # JIG 구분자를 다른 필드로 변경하거나 기본값 사용
        # 예를 들어, BatadcPC나 다른 적절한 필드를 사용하거나, 고정값을 사용
        if 'BatadcPC' in df_valid.columns and not df_valid['BatadcPC'].isna().all():
            jig_column = 'BatadcPC'
        elif 'SemiAssyMaxSolarVolt' in df_valid.columns and not df_valid['SemiAssyMaxSolarVolt'].isna().all():
            jig_column = 'SemiAssyMaxSolarVolt'
        else:
            # JIG 정보가 없는 경우 기본값으로 "DEFAULT_JIG" 사용
            df_valid = df_valid.copy()  # SettingWithCopyWarning 방지
            df_valid['DEFAULT_JIG'] = 'SemiAssy_JIG'
            jig_column = 'DEFAULT_JIG'
        
        summary_data = {}
        
        for jig, group in df_valid.groupby(jig_column):
            # jig 값이 NaN이거나 빈 값인 경우 스킵
            if pd.isna(jig) or str(jig).strip() == '':
                continue
                
            if group['SemiAssyStartTime'].dt.date.dropna().empty:
                continue
            
            for d, day_group in group.groupby(group['SemiAssyStartTime'].dt.date):
                if pd.isna(d):
                    continue
                
                date_iso = pd.to_datetime(d).strftime("%Y-%m-%d")
                
                # 시리얼 번호별로 PASS 여부 확인
                pass_sns_series = day_group.groupby('SNumber')['PassStatusNorm'].apply(lambda x: 'O' in x.tolist())
                pass_sns = pass_sns_series[pass_sns_series].index.tolist()
                
                # 통계 계산
                pass_count = (day_group['PassStatusNorm'] == 'O').sum()
                
                # 가성불량: PASS가 있는 시리얼 번호의 FAIL 케이스
                false_defect_df = day_group[(day_group['PassStatusNorm'] == 'X') & (day_group['SNumber'].isin(pass_sns))]
                false_defect_count = false_defect_df.shape[0]
                false_defect_sns = false_defect_df['SNumber'].unique().tolist()
                
                # 진성불량: PASS가 없는 시리얼 번호의 FAIL 케이스
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
        
        all_dates = sorted(list(df_valid['SemiAssyStartTime'].dt.date.dropna().unique()))
        return summary_data, all_dates
        
    except Exception as e:
        print(f"Error in analyze_Semi_data: {e}")
        return {}, []
