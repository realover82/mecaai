import streamlit as st
import pandas as pd
from datetime import datetime

from csv2 import read_csv_with_dynamic_header, analyze_data

def main():
    st.set_page_config(layout="wide")
    st.title("리모컨 생산 데이터 분석 리포트")
    st.markdown("---")

    uploaded_file = st.file_uploader("CSV 파일을 선택하세요", type=["csv"])

    if uploaded_file is not None:
        st.success(f"파일이 성공적으로 업로드되었습니다: {uploaded_file.name}")
        
        @st.cache_data
        def cached_read_csv():
            return read_csv_with_dynamic_header(uploaded_file)
        
        df = cached_read_csv()
        
        if df is not None:
            st.markdown("### 데이터 미리보기")
            st.dataframe(df.head())
            st.markdown("---")
            
            if st.button("분석 실행"):
                st.markdown("### 분석 리포트")
                
                with st.spinner("데이터 분석 중... 잠시만 기다려주세요."):
                    summary_data, all_dates = analyze_data(df)
                    
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
                        
                        for date_iso, date_str in zip([d.strftime('%Y-%m-%d') for d in all_dates], kor_date_cols):
                            data_point = summary_data[jig].get(date_iso)
                            if data_point and data_point['false_defect_sns']:
                                # st.write(f"**({date_str}) 가성불량 시리얼 번호 목록 ({jig})**")
                                # for sn in data_point['false_defect_sns']:
                                #     st.code(f"      {sn}")
                                st.markdown("---")
                                
                    st.success("분석이 완료되었습니다!")
        else:
            st.error("데이터 로드에 실패했습니다. 파일 형식을 확인해주세요.")

if __name__ == "__main__":
    main()
